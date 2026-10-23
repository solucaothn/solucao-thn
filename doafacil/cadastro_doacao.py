import os
from collections.abc import AsyncGenerator, Sequence
from pathlib import PurePath
from typing import Any
from urllib.parse import urlsplit

import httpx
import reflex as rx

from doafacil.login import LoginState


CATALOG_API_ENV = "XANO_API_URL"
AUTH_API_ENV = "XANO_AUTH_API_URL"
MAX_PHOTOS = 5
PHOTO_UPLOAD_ID = "donation-photo-upload"
IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
IMAGE_ACCEPT = {
    mime_type: [
        extension
        for extension, accepted_mime in IMAGE_TYPES.items()
        if accepted_mime == mime_type
    ]
    for mime_type in dict.fromkeys(IMAGE_TYPES.values())
}
CONDITIONS = ("Ótimo", "Bom", "Regular")
DELIVERY_METHODS = ("A combinar",)
CONTACT_PREFERENCES = ("E-mail", "Chat do DoaFácil")
EXCLUDED_CATEGORY_NAMES = frozenset({"alimentos", "móveis"})


class DonationServiceError(Exception):
    pass


class DonationSessionExpiredError(DonationServiceError):
    pass


def _api_endpoint(environment_key: str, path: str) -> str:
    base_url = os.getenv(environment_key, "").strip()
    try:
        parsed_url = urlsplit(base_url)
        valid_port = parsed_url.port is None or 1 <= parsed_url.port <= 65535
    except ValueError:
        parsed_url = urlsplit("")
        valid_port = False

    if (
        parsed_url.scheme not in {"http", "https"}
        or not parsed_url.hostname
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.query
        or parsed_url.fragment
        or not valid_port
    ):
        raise DonationServiceError from None

    return f"{base_url.rstrip('/')}{path}"


def _parse_categories(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise DonationServiceError

    categories: list[dict[str, Any]] = []
    has_valid_category = False
    for item in payload:
        if not isinstance(item, dict):
            continue
        category_id = item.get("id")
        name = item.get("name")
        if (
            isinstance(category_id, bool)
            or not isinstance(category_id, int)
            or not isinstance(name, str)
            or not name.strip()
        ):
            continue
        has_valid_category = True
        normalized_name = name.strip()
        if normalized_name.casefold() in EXCLUDED_CATEGORY_NAMES:
            continue
        categories.append({"id": category_id, "name": normalized_name})

    if payload and not has_valid_category:
        raise DonationServiceError
    return categories


async def _fetch_categories(
    client: httpx.AsyncClient, endpoint: str
) -> list[dict[str, Any]]:
    try:
        response = await client.get(endpoint)
        response.raise_for_status()
        return _parse_categories(response.json())
    except (httpx.HTTPError, ValueError):
        raise DonationServiceError from None


async def _fetch_profile(
    client: httpx.AsyncClient, endpoint: str, auth_token: str
) -> tuple[str, str]:
    try:
        response = await client.get(
            endpoint,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
    except httpx.RequestError:
        raise DonationServiceError from None

    if response.status_code in {401, 403}:
        raise DonationSessionExpiredError from None
    if response.is_error:
        raise DonationServiceError

    try:
        payload = response.json()
    except ValueError:
        raise DonationServiceError from None

    if not isinstance(payload, dict):
        raise DonationServiceError

    city = payload.get("city")
    state = payload.get("state")
    if (
        not isinstance(city, str)
        or not city.strip()
        or not isinstance(state, str)
        or not state.strip()
    ):
        raise DonationServiceError
    return city.strip(), state.strip()


def _validated_photos(
    files: Sequence[rx.UploadFile],
) -> list[tuple[str, bytes, str]]:
    if len(files) > MAX_PHOTOS:
        raise DonationServiceError

    validated: list[tuple[str, bytes, str]] = []
    for file in files:
        filename = file.name
        expected_mime = IMAGE_TYPES.get(PurePath(filename).suffix.lower())
        actual_mime = file.content_type or ""
        if (
            expected_mime is None
            or (actual_mime and actual_mime != expected_mime)
        ):
            raise DonationServiceError
        validated.append((filename, b"", expected_mime))
    return validated


def _validate_step(
    step: int,
    title: str,
    description: str,
    category_id: str,
    condition: str,
    delivery_method: str,
    contact_preference: str,
    category_ids: set[int],
    city: str,
    state: str,
) -> str:
    if step == 1 and not title.strip():
        return "Informe o nome do item para continuar."
    if step == 2:
        if not description.strip():
            return "Descreva o item para continuar."
        try:
            selected_category = int(category_id)
        except ValueError:
            return "Selecione uma categoria para continuar."
        if selected_category not in category_ids:
            return "Selecione uma categoria válida para continuar."
        if condition not in CONDITIONS:
            return "Selecione a condição do item para continuar."
    if step == 4:
        if delivery_method not in DELIVERY_METHODS:
            return "Selecione uma forma de entrega para continuar."
        if not city.strip() or not state.strip():
            return (
                "Complete cidade e estado no seu perfil antes de continuar."
            )
    if step == 5 and contact_preference not in CONTACT_PREFERENCES:
        return "Selecione uma forma de contato para publicar."
    return ""


async def _publish_donation(
    client: httpx.AsyncClient,
    endpoint: str,
    auth_token: str,
    payload: dict[str, object],
    photos: Sequence[tuple[str, bytes, str]],
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {auth_token}"}
    multipart_fields = [
        (key, (None, str(value))) for key, value in payload.items()
    ]
    multipart_files = [
        ("photos[]", (filename, contents, mime_type))
        for filename, contents, mime_type in photos
    ]
    try:
        response = await client.post(
            endpoint,
            files=[*multipart_fields, *multipart_files],
            headers=headers,
        )
    except httpx.RequestError:
        raise DonationServiceError from None

    if response.status_code in {401, 403}:
        raise DonationSessionExpiredError
    if response.is_error:
        raise DonationServiceError

    try:
        result = response.json()
    except ValueError:
        raise DonationServiceError from None

    donation = result.get("donation") if isinstance(result, dict) else None
    if (
        not isinstance(donation, dict)
        or isinstance(donation.get("id"), bool)
        or not isinstance(donation.get("id"), int)
        or donation.get("status") != "disponível"
    ):
        raise DonationServiceError
    return donation


class DonationCreateState(LoginState):
    current_step: int = 1
    title: str = ""
    description: str = ""
    category_id: str = ""
    category_name: str = ""
    condition: str = ""
    delivery_method: str = ""
    contact_preference: str = ""
    categories: list[dict[str, Any]] = []
    city: str = ""
    state: str = ""
    is_loading_data: bool = False
    data_load_failed: bool = False
    is_publishing: bool = False
    published: bool = False
    donation_error_message: str = ""
    upload_progress: str = ""
    success_message: str = ""

    @rx.var
    def progress_percentage(self) -> int:
        return self.current_step * 20

    @rx.var
    def category_options(self) -> list[str]:
        return [category["name"] for category in self.categories]

    @rx.event
    async def load_initial_data(
        self,
    ) -> AsyncGenerator[rx.event.EventSpec, None]:
        self.current_step = 1
        self.title = ""
        self.description = ""
        self.category_id = ""
        self.category_name = ""
        self.condition = ""
        self.delivery_method = ""
        self.contact_preference = ""
        self.categories = []
        self.city = ""
        self.state = ""
        self.is_loading_data = False
        self.data_load_failed = False
        self.is_publishing = False
        self.published = False
        self.donation_error_message = ""
        self.upload_progress = ""
        self.success_message = ""

        if not self.auth_token:
            yield rx.redirect("/login")
            return

        yield rx.clear_selected_files(PHOTO_UPLOAD_ID)
        self.is_loading_data = True
        self.data_load_failed = False
        self.donation_error_message = ""
        try:
            categories_endpoint = _api_endpoint(
                CATALOG_API_ENV, "/catalog/categories"
            )
            profile_endpoint = _api_endpoint(
                AUTH_API_ENV, "/auth/profile"
            )
        except DonationServiceError:
            self.data_load_failed = True
            self.donation_error_message = (
                "Não foi possível conectar aos serviços do DoaFácil. "
                "Tente novamente."
            )
            self.is_loading_data = False
            return

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                self.categories = await _fetch_categories(
                    client, categories_endpoint
                )
            except DonationServiceError:
                self.data_load_failed = True
                self.donation_error_message = (
                    "Não foi possível carregar as categorias. "
                    "Tente novamente."
                )
            try:
                self.city, self.state = await _fetch_profile(
                    client, profile_endpoint, self.auth_token
                )
            except DonationSessionExpiredError:
                self.is_loading_data = False
                yield LoginState.logout
                yield rx.redirect("/login")
                return
            except DonationServiceError:
                self.data_load_failed = True
                self.donation_error_message = (
                    "Não foi possível carregar a localização do seu perfil. "
                    "Confira seus dados e tente novamente."
                )

        self.is_loading_data = False

    @rx.event
    def set_category(self, value: str) -> None:
        selected = next(
            (
                category
                for category in self.categories
                if category["name"] == value
            ),
            None,
        )
        self.category_id = str(selected["id"]) if selected else ""
        self.category_name = selected["name"] if selected else ""

    @rx.event
    def set_title(self, value: str) -> None:
        self.title = value

    @rx.event
    def set_description(self, value: str) -> None:
        self.description = value

    @rx.event
    def set_condition(self, value: str) -> None:
        self.condition = value

    @rx.event
    def set_delivery_method(self, value: str) -> None:
        self.delivery_method = value

    @rx.event
    def set_contact_preference(self, value: str) -> None:
        self.contact_preference = value

    @rx.event
    def advance(self, files: list[rx.UploadFile]) -> None:
        if self.is_loading_data or self.is_publishing or self.published:
            return
        if self.current_step == 3:
            if not files:
                self.donation_error_message = (
                    "Adicione pelo menos uma foto para continuar."
                )
                return
            self.current_step = 4
            self.donation_error_message = ""
            return
        category_ids = {
            category["id"] for category in self.categories
        }
        error = _validate_step(
            self.current_step,
            self.title,
            self.description,
            self.category_id,
            self.condition,
            self.delivery_method,
            self.contact_preference,
            category_ids,
            self.city,
            self.state,
        )
        if error:
            self.donation_error_message = error
            return
        if self.current_step < 5:
            self.current_step += 1
        self.donation_error_message = ""

    @rx.event
    def go_back(self) -> None:
        if self.current_step > 1 and not self.is_publishing:
            self.current_step -= 1
        self.donation_error_message = ""

    @rx.event
    async def publish(
        self, files: list[rx.UploadFile]
    ) -> AsyncGenerator[rx.event.EventSpec, None]:
        if not self.auth_token:
            yield rx.redirect("/login")
            return
        if self.is_publishing or self.published:
            return

        category_ids = {
            category["id"] for category in self.categories
        }
        validation_error = _validate_step(
            5,
            self.title,
            self.description,
            self.category_id,
            self.condition,
            self.delivery_method,
            self.contact_preference,
            category_ids,
            self.city,
            self.state,
        )
        if validation_error:
            self.donation_error_message = validation_error
            return

        try:
            photo_metadata = _validated_photos(files)
        except DonationServiceError:
            self.donation_error_message = (
                "Selecione até cinco imagens JPEG, PNG, GIF ou WEBP."
            )
            return

        self.is_publishing = True
        self.donation_error_message = ""
        self.success_message = ""
        photos: list[tuple[str, bytes, str]] = []
        for index, (filename, _, mime_type) in enumerate(photo_metadata, 1):
            self.upload_progress = (
                f"Preparando imagem {index} de {len(photo_metadata)}..."
            )
            try:
                contents = await files[index - 1].read()
            except OSError:
                self.is_publishing = False
                self.upload_progress = ""
                self.donation_error_message = (
                    "Não foi possível ler uma das imagens. "
                    "Remova-a e tente novamente."
                )
                return
            if not contents:
                self.is_publishing = False
                self.upload_progress = ""
                self.donation_error_message = (
                    "Uma das imagens está vazia. Remova-a e tente novamente."
                )
                return
            photos.append((filename, contents, mime_type))

        self.upload_progress = "Enviando sua doação..."
        payload: dict[str, object] = {
            "category_id": int(self.category_id),
            "title": self.title.strip(),
            "description": self.description.strip(),
            "condition": self.condition,
            "delivery_method": self.delivery_method,
            "contact_preference": self.contact_preference,
        }
        try:
            endpoint = _api_endpoint(
                CATALOG_API_ENV, "/catalog/donations/publish"
            )
            async with httpx.AsyncClient(timeout=60.0) as client:
                await _publish_donation(
                    client,
                    endpoint,
                    self.auth_token,
                    payload,
                    photos,
                )
        except DonationSessionExpiredError:
            self.is_publishing = False
            self.upload_progress = ""
            yield LoginState.logout
            yield rx.redirect("/login")
            return
        except DonationServiceError:
            self.donation_error_message = (
                "Não foi possível publicar sua doação. "
                "Seus dados foram mantidos; tente novamente."
            )
        else:
            self.published = True
            self.success_message = (
                "Doação publicada! Obrigado por compartilhar."
            )
        self.is_publishing = False
        self.upload_progress = ""


def _field_label(text: str) -> rx.Component:
    return rx.text(
        text,
        color="#333333",
        font_weight="700",
        font_size="0.8rem",
        width="100%",
    )


def _select_field(
    label: str,
    options: Sequence[str] | rx.Var[list[str]],
    value: rx.Var[str],
    on_change: Any,
    placeholder: str,
    field_id: str,
) -> rx.Component:
    return rx.vstack(
        _field_label(label),
        rx.select(
            options,
            id=field_id,
            value=value,
            on_change=on_change,
            placeholder=placeholder,
            width="100%",
            height="40px",
            background="white",
            color="#333333",
            high_contrast=True,
            border="1px solid #C8C8C8",
            border_radius="8px",
        ),
        align="start",
        spacing="2",
        width="100%",
    )


def _step_one() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "O que você quer doar?",
            color="#333333",
            font_size="1.2rem",
            font_weight="700",
            width="100%",
        ),
        rx.text(
            "Comece contando qual objeto está pronto para ganhar um novo lar.",
            color="#666666",
            width="100%",
        ),
        _field_label("Nome do item"),
        rx.input(
            value=DonationCreateState.title,
            on_change=DonationCreateState.set_title,
            placeholder="Ex.: Carrinho de brinquedo",
            id="donation-title",
            max_length=100,
            width="100%",
            height="40px",
            background="white",
            color="#333333",
            border="1px solid #C8C8C8",
            border_radius="8px",
        ),
        align="start",
        spacing="3",
        width="100%",
    )


def _step_two() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Conte mais sobre o item",
            color="#333333",
            font_size="1.2rem",
            font_weight="700",
            width="100%",
        ),
        rx.text(
            "Uma boa descrição ajuda as pessoas a entenderem sua doação.",
            color="#666666",
            width="100%",
        ),
        _field_label("Descrição"),
        rx.text_area(
            value=DonationCreateState.description,
            on_change=DonationCreateState.set_description,
            placeholder="Conte detalhes importantes sobre o objeto.",
            id="donation-description",
            max_length=2000,
            min_height="100px",
            width="100%",
            background="white",
            color="#333333",
            border="1px solid #C8C8C8",
            border_radius="8px",
        ),
        _select_field(
            "Categoria",
            DonationCreateState.category_options,
            DonationCreateState.category_name,
            DonationCreateState.set_category,
            "Selecione uma categoria",
            "donation-category",
        ),
        _select_field(
            "Condição do item",
            CONDITIONS,
            DonationCreateState.condition,
            DonationCreateState.set_condition,
            "Selecione a condição",
            "donation-condition",
        ),
        align="start",
        spacing="3",
        width="100%",
    )


def _step_three() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Adicione fotos",
            color="#333333",
            font_size="1.2rem",
            font_weight="700",
            width="100%",
        ),
        rx.text(
            "Fotos ajudam as pessoas a conhecerem melhor o objeto. "
            "Você pode publicar sem fotos.",
            color="#666666",
            width="100%",
        ),
        rx.upload(
            rx.vstack(
                rx.icon("image", size=32, color="#00A859"),
                rx.text(
                    "Arraste as imagens para cá ou escolha os arquivos",
                    color="#333333",
                    font_weight="600",
                    text_align="center",
                ),
                rx.text(
                    "JPEG, PNG, GIF ou WEBP · até 5 fotos",
                    color="#666666",
                    font_size="0.9rem",
                ),
                align="center",
                spacing="3",
                width="100%",
                padding="2rem 1rem",
            ),
            id=PHOTO_UPLOAD_ID,
            multiple=True,
            accept=IMAGE_ACCEPT,
            max_files=MAX_PHOTOS,
            no_keyboard=True,
            width="100%",
            border="2px dashed #9DBFA9",
            border_radius="12px",
            background="#F9FCF9",
            cursor="pointer",
        ),
        rx.hstack(
            rx.text(
                "Fotos selecionadas: ",
                rx.selected_files(PHOTO_UPLOAD_ID).length(),
                " / ",
                MAX_PHOTOS,
                color="#333333",
            ),
            rx.spacer(),
            rx.button(
                "Remover todas",
                type="button",
                on_click=rx.clear_selected_files(PHOTO_UPLOAD_ID),
                disabled=DonationCreateState.is_publishing,
                variant="soft",
                color="#166B3B",
                background="#E8F5EC",
            ),
            width="100%",
            align="center",
            wrap="wrap",
        ),
        rx.foreach(
            rx.selected_files(PHOTO_UPLOAD_ID),
            lambda filename: rx.hstack(
                rx.icon("image", size=16, color="#168447"),
                rx.text(
                    filename,
                    color="#333333",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
                rx.spacer(),
                rx.text(
                    "Pronta para enviar",
                    color="#168447",
                    font_size="0.85rem",
                    flex_shrink="0",
                ),
                width="100%",
                padding="0.6rem 0.8rem",
                border="1px solid #E1E9E3",
                border_radius="8px",
            ),
        ),
        align="start",
        spacing="3",
        width="100%",
    )


def _step_four() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Como será a entrega?",
            color="#333333",
            font_size="1.2rem",
            font_weight="700",
            width="100%",
        ),
        rx.text(
            "A localização é a cidade e o estado informados no seu perfil.",
            color="#666666",
            width="100%",
        ),
        rx.vstack(
            _field_label("Localização da doação"),
            rx.hstack(
                rx.icon("map-pin", size=18, color="#168447"),
                rx.text(
                    DonationCreateState.city,
                    ", ",
                    DonationCreateState.state,
                    color="#333333",
                    font_weight="600",
                ),
                width="100%",
                padding="0.85rem 1rem",
                border="1px solid #C8C8C8",
                border_radius="8px",
                background="#F7F8F7",
            ),
            align="start",
            spacing="2",
            width="100%",
        ),
        _select_field(
            "Forma de entrega",
            DELIVERY_METHODS,
            DonationCreateState.delivery_method,
            DonationCreateState.set_delivery_method,
            "Selecione uma forma de entrega",
            "donation-delivery-method",
        ),
        align="start",
        spacing="3",
        width="100%",
    )


def _step_five() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Como prefere ser contatado?",
            color="#333333",
            font_size="1.2rem",
            font_weight="700",
            width="100%",
        ),
        rx.text(
            "Escolha como as pessoas interessadas poderão falar com você.",
            color="#666666",
            width="100%",
        ),
        _select_field(
            "Preferência de contato",
            CONTACT_PREFERENCES,
            DonationCreateState.contact_preference,
            DonationCreateState.set_contact_preference,
            "Selecione uma forma de contato",
            "donation-contact-preference",
        ),
        rx.cond(
            DonationCreateState.success_message != "",
            rx.text(
                DonationCreateState.success_message,
                role="status",
                color="#166B3B",
                font_weight="700",
                background="#E8F5EC",
                padding="0.9rem 1rem",
                border_radius="8px",
                width="100%",
            ),
            rx.fragment(),
        ),
        align="start",
        spacing="3",
        width="100%",
    )


def _legal_notice() -> rx.Component:
    return rx.text(
        "Ao clicar no botão abaixo você declara que é maior de 18 anos, "
        "leu e está de acordo com os Termos, Taxas, Prazos e Regulamentos.",
        color="#333333",
        font_size="0.75rem",
        line_height="1.5",
        width="100%",
    )


def _wizard_content() -> rx.Component:
    step_content = rx.vstack(
        rx.cond(
            DonationCreateState.current_step == 1,
            _step_one(),
            rx.fragment(),
        ),
        rx.cond(
            DonationCreateState.current_step == 2,
            _step_two(),
            rx.fragment(),
        ),
        rx.box(
            _step_three(),
            display=rx.cond(
                DonationCreateState.current_step == 3, "block", "none"
            ),
            width="100%",
        ),
        rx.cond(
            DonationCreateState.current_step == 4,
            _step_four(),
            rx.fragment(),
        ),
        rx.cond(
            DonationCreateState.current_step == 5,
            _step_five(),
            rx.fragment(),
        ),
        align="stretch",
        spacing="5",
        width="100%",
    )

    return rx.vstack(
        rx.vstack(
            rx.box(
                rx.box(
                    width=(
                        DonationCreateState.progress_percentage.to_string()
                        + "%"
                    ),
                    height="100%",
                    background="#00A859",
                    border_radius="999px",
                    transition="width 0.2s ease",
                ),
                width="100%",
                height="4px",
                background="#E4E7E4",
                border_radius="999px",
                role="progressbar",
                aria_label="Progresso do cadastro",
                aria_valuemin=1,
                aria_valuemax=5,
                aria_valuenow=DonationCreateState.current_step,
            ),
            rx.text(
                "Passo ",
                DonationCreateState.current_step,
                " de 5",
                color="#333333",
                font_size="0.65rem",
            ),
            align="end",
            spacing="1",
            width="100%",
        ),
        rx.cond(
            DonationCreateState.donation_error_message != "",
            rx.text(
                DonationCreateState.donation_error_message,
                role="alert",
                color="#9B2C2C",
                background="#FFF0EE",
                padding="0.85rem 1rem",
                border_radius="8px",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            DonationCreateState.data_load_failed,
            rx.button(
                "Tentar carregar novamente",
                type="button",
                on_click=DonationCreateState.load_initial_data,
                disabled=DonationCreateState.is_loading_data,
                variant="soft",
                color="#166B3B",
                background="#E8F5EC",
            ),
            rx.fragment(),
        ),
        rx.cond(
            DonationCreateState.upload_progress != "",
            rx.text(
                DonationCreateState.upload_progress,
                color="#166B3B",
                font_weight="600",
                role="status",
                width="100%",
            ),
            rx.fragment(),
        ),
        step_content,
        _legal_notice(),
        rx.hstack(
            rx.cond(
                DonationCreateState.current_step > 1,
                rx.button(
                    "Voltar",
                    type="button",
                    on_click=DonationCreateState.go_back,
                    disabled=DonationCreateState.is_publishing,
                    variant="outline",
                    border="1px solid #168447",
                    color="#166B3B",
                    background="white",
                    min_width="120px",
                    height="40px",
                ),
                rx.fragment(),
            ),
            rx.cond(
                DonationCreateState.current_step < 5,
                rx.button(
                    "Continuar",
                    type="button",
                    on_click=DonationCreateState.advance(
                        rx.upload_files(PHOTO_UPLOAD_ID)
                    ),
                    disabled=DonationCreateState.is_loading_data,
                    background="#007A42",
                    color="white",
                    _hover={"background": "#006B39"},
                    flex="1",
                    height="40px",
                ),
                rx.button(
                    rx.cond(
                        DonationCreateState.is_publishing,
                        "Publicando...",
                        rx.cond(
                            DonationCreateState.published,
                            "Publicado",
                            "Publicar doação",
                        ),
                    ),
                    type="button",
                    on_click=DonationCreateState.publish(
                        rx.upload_files(PHOTO_UPLOAD_ID)
                    ),
                    disabled=(
                        DonationCreateState.is_publishing
                        | DonationCreateState.published
                    ),
                    background="#007A42",
                    color="white",
                    _hover={"background": "#006B39"},
                    flex="1",
                    height="40px",
                ),
            ),
            width="100%",
            align="center",
            spacing="3",
            margin_top="0.5rem",
        ),
        align="stretch",
        spacing="4",
        width="100%",
        max_width="360px",
        margin="0 auto",
        background="transparent",
        padding="0",
        class_name="auth-card-enter",
    )


def donation_creation_page() -> rx.Component:
    return rx.box(
        rx.box(
            rx.link(
                rx.image(
                    src="/logo.svg",
                    alt="DoaFácil",
                    width="140px",
                    height="52px",
                    object_fit="contain",
                ),
                href="/",
            ),
            width="100%",
            background="white",
            padding="0.25rem 1rem",
            box_shadow="0 2px 8px rgba(39, 39, 39, 0.06)",
            display="flex",
            justify_content="center",
        ),
        rx.box(
            rx.link(
                rx.icon("chevron-left", size=24),
                href="/",
                color="#166B3B",
                font_weight="600",
                aria_label="Voltar ao início",
            ),
            width="100%",
            max_width="1000px",
            margin="0 auto",
            padding="0 1.25rem",
        ),
        rx.vstack(
            rx.cond(
                DonationCreateState.is_loading_data,
                rx.vstack(
                    rx.spinner(color="#00A859", size="3"),
                    rx.text(
                        "Preparando seu cadastro...",
                        color="#555555",
                    ),
                    align="center",
                    spacing="4",
                    width="100%",
                    padding="3rem",
                ),
                _wizard_content(),
            ),
            align="stretch",
            spacing="0",
            width="100%",
            max_width="1000px",
            margin="0 auto",
            padding="1rem 1.25rem 3rem",
        ),
        min_height="100vh",
        background="#FFF6E8",
    )
