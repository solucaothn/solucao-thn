import os
import uuid
from collections.abc import AsyncGenerator, Sequence
from typing import Any
from urllib.parse import urlsplit

import httpx
import reflex as rx

from doafacil.campos import select_field
from doafacil.fotos_doacao import (
    EMPTY_MESSAGE,
    FORMAT_MESSAGE,
    IMAGE_TYPES,
    MAX_PHOTO_BYTES,
    MAX_PHOTOS,
    READ_ERROR_MESSAGE,
    PhotoImageError,
    check_file,
    make_cover as order_make_cover,
    move as order_move,
    process_photo,
    rejection_message,
    remove as order_remove,
)
from doafacil.login import LoginState


CATALOG_API_ENV = "XANO_API_URL"
AUTH_API_ENV = "XANO_AUTH_API_URL"
PHOTO_UPLOAD_ID = "donation-photo-upload"
PHOTOS_PREPARING_MESSAGE = "Preparando fotos..."
PHOTO_STEP_TEXT = "Adicione de 1 a 5 fotos. A primeira foto é a capa da doação."
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
MISSING_PHOTOS_MESSAGE = "Adicione pelo menos uma foto para continuar."


class DonationServiceError(Exception):
    pass


class DonationMissingPhotosError(DonationServiceError):
    pass


class DonationSessionExpiredError(DonationServiceError):
    pass


def _contains_error_message(payload: object, message: str) -> bool:
    if isinstance(payload, str):
        return message in payload
    if isinstance(payload, dict):
        return any(
            _contains_error_message(value, message)
            for value in payload.values()
        )
    if isinstance(payload, list):
        return any(
            _contains_error_message(value, message) for value in payload
        )
    return False


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


def _photos_payload(
    photos: Sequence[dict[str, Any]],
    files: dict[str, tuple[bytes, str, str]],
) -> list[tuple[str, bytes, str]]:
    """As fotos preparadas na ordem da tela, com os nomes foto-1.<ext>,
    foto-2.<ext>... (o Xano grava nessa ordem e usa a primeira como capa)."""
    payload: list[tuple[str, bytes, str]] = []
    for position, photo in enumerate(photos, 1):
        contents, mime_type, extension = files[photo["id"]]
        payload.append((f"foto-{position}.{extension}", contents, mime_type))
    return payload


def _clear_photos(state: Any) -> None:
    """Apaga as fotos guardadas no servidor (variável de backend) e as
    miniaturas. Usada ao reiniciar o cadastro e ao publicar com sucesso."""
    state.photos = []
    state._photo_files = {}
    state.photos_busy = False
    state.photo_notice = ""


def _focus_script(element_id: str) -> str:
    # Depois de redesenhar a lista, devolve o foco ao botão certo.
    return (
        "setTimeout(() => { const el = document.getElementById("
        f"{element_id!r}); if (el) {{ el.focus(); }} }}, 0)"
    )


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
        try:
            error_payload = response.json()
        except ValueError:
            raise DonationServiceError from None
        if _contains_error_message(error_payload, MISSING_PHOTOS_MESSAGE):
            raise DonationMissingPhotosError
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
    # Fotos (change fotos-formulario-doacao). As versões preparadas ficam só
    # no servidor, em _photo_files (variável de backend, que não vai ao
    # navegador): {id: (bytes, tipo, extensão)}. O navegador recebe só as
    # miniaturas, em photos, na ordem da tela (a primeira é a capa).
    photos: list[dict[str, str]] = []
    photos_busy: bool = False
    photo_notice: str = ""
    _photo_files: dict[str, tuple[bytes, str, str]] = {}

    @rx.var
    def progress_percentage(self) -> int:
        return self.current_step * 20

    @rx.var
    def photo_count(self) -> int:
        return len(self.photos)

    @rx.var
    def photos_full(self) -> bool:
        return len(self.photos) >= MAX_PHOTOS

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
        # Reinício: apaga as fotos guardadas da visita anterior.
        _clear_photos(self)

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

    # Fotos ----------------------------------------------------------------

    @rx.event
    async def add_photos(
        self, files: list[rx.UploadFile]
    ) -> AsyncGenerator[rx.event.EventSpec | None, None]:
        """Soma as fotos escolhidas às já aceitas (até 5). Cada foto é
        conferida (tipo e 5 MB), preparada (orientação, sem metadados, até
        1600 px, JPEG ou, com transparência, PNG) e guardada só nessa versão
        preparada."""
        if self.photos_busy or self.is_publishing or self.published:
            return
        self.donation_error_message = ""
        self.photo_notice = ""
        self.photos_busy = True
        yield
        error = ""
        accepted = 0
        for file in files or []:
            if len(self.photos) >= MAX_PHOTOS:
                error = error or FORMAT_MESSAGE
                break
            try:
                contents = await file.read()
            except OSError:
                error = error or READ_ERROR_MESSAGE
                continue
            problem = check_file(file.name or "", file.content_type or "", len(contents))
            if problem:
                error = error or problem
                continue
            try:
                processed = process_photo(contents)
            except PhotoImageError:
                error = error or FORMAT_MESSAGE
                continue
            # Só a versão preparada fica guardada; o arquivo recebido é descartado.
            del contents
            photo_id = uuid.uuid4().hex
            self._photo_files = {
                **self._photo_files,
                photo_id: (processed.contents, processed.mime, processed.extension),
            }
            self.photos = [
                *self.photos,
                {"id": photo_id, "thumb": processed.thumb},
            ]
            accepted += 1
        self.photos_busy = False
        if error:
            self.donation_error_message = error
        if accepted:
            self.photo_notice = (
                "Foto adicionada." if accepted == 1 else f"{accepted} fotos adicionadas."
            )
        yield rx.clear_selected_files(PHOTO_UPLOAD_ID)

    @rx.event
    def photos_rejected(self, rejections: list[dict[str, Any]]) -> None:
        """Arquivos recusados pelo próprio componente (tipo, mais de 5 MB ou
        mais de 5 numa escolha): nenhuma requisição; as fotos aceitas ficam."""
        self.photo_notice = ""
        self.donation_error_message = rejection_message(rejections)

    @rx.event
    def remove_photo(self, photo_id: str):
        if self.photos_busy or self.is_publishing or self.published:
            return
        position = next(
            (index for index, photo in enumerate(self.photos) if photo["id"] == photo_id),
            -1,
        )
        if position < 0:
            return
        self.photos = order_remove(self.photos, photo_id)
        # Apaga do servidor a versão guardada da foto removida.
        self._photo_files = {
            key: value for key, value in self._photo_files.items() if key != photo_id
        }
        self.donation_error_message = ""
        self.photo_notice = "Foto removida."
        if self.photos:
            next_photo = self.photos[min(position, len(self.photos) - 1)]
            return rx.call_script(_focus_script(f"photo-{next_photo['id']}-remove"))
        return rx.call_script(_focus_script(PHOTO_UPLOAD_ID))

    @rx.event
    def move_photo(self, photo_id: str, delta: int):
        if self.photos_busy or self.is_publishing or self.published:
            return
        moved = order_move(self.photos, photo_id, int(delta))
        if [photo["id"] for photo in moved] == [photo["id"] for photo in self.photos]:
            return
        self.photos = moved
        position = next(index for index, photo in enumerate(moved) if photo["id"] == photo_id)
        self.photo_notice = f"Foto movida para a posição {position + 1}."
        direction = "left" if int(delta) < 0 else "right"
        # Na ponta, o botão daquele lado fica desativado: o foco vai ao outro.
        if (direction == "left" and position == 0) or (
            direction == "right" and position == len(moved) - 1
        ):
            direction = "right" if direction == "left" else "left"
        return rx.call_script(_focus_script(f"photo-{photo_id}-{direction}"))

    @rx.event
    def make_cover(self, photo_id: str):
        if self.photos_busy or self.is_publishing or self.published:
            return
        reordered = order_make_cover(self.photos, photo_id)
        if [photo["id"] for photo in reordered] == [photo["id"] for photo in self.photos]:
            return
        self.photos = reordered
        self.photo_notice = "Foto definida como capa."
        # “Tornar capa” fica desativado na capa: o foco vai a “Mover para a direita”
        # (ou a “Remover”, se ela for a única foto).
        target = "right" if len(reordered) > 1 else "remove"
        return rx.call_script(_focus_script(f"photo-{photo_id}-{target}"))

    # Navegação -------------------------------------------------------------

    @rx.event
    def advance(self) -> None:
        if self.is_loading_data or self.is_publishing or self.published:
            return
        if self.current_step == 3:
            if self.photos_busy:
                return
            if not self.photos:
                self.donation_error_message = MISSING_PHOTOS_MESSAGE
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
    async def publish(self) -> AsyncGenerator[rx.event.EventSpec, None]:
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

        if not self.photos:
            self.donation_error_message = MISSING_PHOTOS_MESSAGE
            return
        if len(self.photos) > MAX_PHOTOS:
            self.donation_error_message = FORMAT_MESSAGE
            return
        try:
            # As fotos preparadas, na ordem da tela, com os nomes foto-N.<ext>.
            photos = _photos_payload(self.photos, self._photo_files)
        except KeyError:
            self.donation_error_message = (
                "Não foi possível ler uma das imagens. "
                "Remova-a e tente novamente."
            )
            return

        self.is_publishing = True
        self.donation_error_message = ""
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
                donation = await _publish_donation(
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
        except DonationMissingPhotosError:
            self.donation_error_message = MISSING_PHOTOS_MESSAGE
        except DonationServiceError:
            self.donation_error_message = (
                "Não foi possível publicar sua doação. "
                "Seus dados foram mantidos; tente novamente."
            )
        else:
            # Importação local: chat.py importa deste módulo e
            # detalhe_doacao.py importa de chat.py (evita o ciclo).
            from doafacil.detalhe_doacao import DonationDetailState

            self.published = True
            self.is_publishing = False
            self.upload_progress = ""
            # Publicada: as fotos guardadas no servidor são apagadas.
            _clear_photos(self)
            donation_id = donation["id"]
            yield DonationDetailState.set_published_notice(donation_id)
            yield rx.redirect(f"/doacao/{donation_id}")
            return
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
    """O select com o estilo no Trigger (doafacil/campos.py): fundo branco,
    borda #C8C8C8, texto #1F1F1F e foco verde, nos quatro selects do cadastro.
    O atalho rx.select(...) punha o estilo no Root e deixava o botão cinza."""
    if not isinstance(options, rx.Var):
        options = tuple(options)
    return select_field(label, options, value, on_change, placeholder, field_id)


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


PHOTO_GREEN = "#007A42"
# Foco dos botões do wizard (Voltar, Continuar e Publicar): verde, como os
# outros controles do site, no lugar do anel azul do tema Radix.
WIZARD_FOCUS = {"outline": "2px solid #007A42", "outlineOffset": "2px", "boxShadow": "none"}
PHOTO_ICON_GREEN = "#168447"
PHOTO_TEXT = "#333333"
PHOTO_MUTED = "#555555"
PHOTO_DANGER = "#B42318"
COVER_BADGE_BACKGROUND = "#E8F5EC"
COVER_BADGE_TEXT = "#166B3B"


def _photo_button(
    icon: str,
    label: rx.Var,
    element_id: rx.Var,
    on_click: Any,
    disabled: rx.Var,
    color: str = PHOTO_TEXT,
) -> rx.Component:
    """Botão de ícone de 44 px, com rótulo acessível que inclui a posição."""
    return rx.el.button(
        rx.icon(icon, size=20, aria_hidden="true"),
        type="button",
        id=element_id,
        aria_label=label,
        title=label,
        on_click=on_click,
        disabled=disabled,
        class_name="donation-photo-action",
        display="inline-flex",
        align_items="center",
        justify_content="center",
        width="44px",
        height="44px",
        min_width="44px",
        padding="0",
        border="1px solid #C8C8C8",
        border_radius="8px",
        background="#FFFFFF",
        color=color,
        cursor="pointer",
        # Desativado por cor (sem opacidade parcial, como os campos do cadastro).
        _disabled={"color": "#A3A3A3", "borderColor": "#E4E4E4", "cursor": "default"},
        _focus_visible={"outline": f"2px solid {PHOTO_GREEN}", "outlineOffset": "2px"},
    )


def _photo_row(photo: rx.Var, index: rx.Var) -> rx.Component:
    """Uma foto: miniatura, “Foto N”, o selo “Capa” na primeira e os botões
    mover, tornar capa e remover."""
    number = (index + 1).to_string()
    total = DonationCreateState.photo_count.to_string()
    photo_id = photo["id"].to(str)
    busy = DonationCreateState.photos_busy | DonationCreateState.is_publishing
    is_first = index == 0
    is_last = index == DonationCreateState.photo_count - 1
    return rx.flex(
        rx.image(
            src=photo["thumb"],
            alt=rx.Var.create("Foto ") + number + " de " + total,
            width="72px",
            height="72px",
            min_width="72px",
            object_fit="cover",
            border_radius="8px",
            background="#F2F2F2",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.hstack(
                rx.text(
                    rx.Var.create("Foto ") + number,
                    color=PHOTO_TEXT,
                    font_weight="700",
                ),
                rx.cond(
                    is_first,
                    rx.text(
                        "Capa",
                        class_name="donation-photo-cover",
                        color=COVER_BADGE_TEXT,
                        background=COVER_BADGE_BACKGROUND,
                        font_size="0.75rem",
                        font_weight="700",
                        padding="2px 8px",
                        border_radius="999px",
                    ),
                    rx.fragment(),
                ),
                align="center",
                spacing="2",
            ),
            rx.flex(
                _photo_button(
                    "chevron-left",
                    rx.Var.create("Mover foto ") + number + " para a esquerda",
                    rx.Var.create("photo-") + photo_id + "-left",
                    DonationCreateState.move_photo(photo["id"], -1),
                    is_first | busy,
                ),
                _photo_button(
                    "chevron-right",
                    rx.Var.create("Mover foto ") + number + " para a direita",
                    rx.Var.create("photo-") + photo_id + "-right",
                    DonationCreateState.move_photo(photo["id"], 1),
                    is_last | busy,
                ),
                _photo_button(
                    "star",
                    rx.Var.create("Tornar foto ") + number + " a capa",
                    rx.Var.create("photo-") + photo_id + "-cover",
                    DonationCreateState.make_cover(photo["id"]),
                    is_first | busy,
                ),
                _photo_button(
                    "trash-2",
                    rx.Var.create("Remover foto ") + number,
                    rx.Var.create("photo-") + photo_id + "-remove",
                    DonationCreateState.remove_photo(photo["id"]),
                    busy,
                    color=PHOTO_DANGER,
                ),
                wrap="wrap",
                gap="8px",
            ),
            align="start",
            spacing="2",
            min_width="0",
            flex="1",
        ),
        class_name="donation-photo-row",
        gap="12px",
        align="start",
        width="100%",
        padding="8px",
        border="1px solid #E1E9E3",
        border_radius="8px",
        background="#FFFFFF",
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
            PHOTO_STEP_TEXT,
            color="#666666",
            width="100%",
        ),
        rx.upload(
            rx.vstack(
                rx.icon("image", size=32, color=PHOTO_ICON_GREEN, aria_hidden="true"),
                rx.cond(
                    DonationCreateState.photos_full,
                    rx.text(
                        "Limite de 5 fotos atingido",
                        color=PHOTO_TEXT,
                        font_weight="600",
                        text_align="center",
                    ),
                    rx.text(
                        "Arraste as imagens para cá ou escolha os arquivos",
                        color=PHOTO_TEXT,
                        font_weight="600",
                        text_align="center",
                    ),
                ),
                rx.text(
                    "JPEG, PNG, GIF ou WEBP · até 5 MB · até 5 fotos · a primeira é a capa",
                    color=PHOTO_MUTED,
                    font_size="0.9rem",
                    text_align="center",
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
            max_size=MAX_PHOTO_BYTES,
            disabled=(
                DonationCreateState.photos_full
                | DonationCreateState.photos_busy
                | DonationCreateState.is_publishing
            ),
            on_drop=DonationCreateState.add_photos(
                rx.upload_files(upload_id=PHOTO_UPLOAD_ID)
            ),
            on_drop_rejected=DonationCreateState.photos_rejected,
            width="100%",
            border="2px dashed #9DBFA9",
            border_radius="12px",
            background="#F9FCF9",
            cursor="pointer",
        ),
        rx.text(
            DonationCreateState.photo_count,
            " de 5 fotos",
            aria_live="polite",
            class_name="donation-photo-count",
            color=PHOTO_TEXT,
        ),
        rx.cond(
            DonationCreateState.photos_busy,
            rx.text(
                PHOTOS_PREPARING_MESSAGE,
                role="status",
                color=COVER_BADGE_TEXT,
                font_weight="600",
            ),
            rx.fragment(),
        ),
        rx.cond(
            DonationCreateState.photo_notice != "",
            rx.text(
                DonationCreateState.photo_notice,
                role="status",
                color=COVER_BADGE_TEXT,
                font_size="0.9rem",
            ),
            rx.fragment(),
        ),
        rx.vstack(
            rx.foreach(DonationCreateState.photos, _photo_row),
            class_name="donation-photo-list",
            spacing="2",
            width="100%",
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
            DonationCreateState.contact_preference == "E-mail",
            rx.text(
                "Seu e-mail ficará disponível para pessoas logadas que "
                "quiserem falar com você.",
                role="note",
                color="#166B3B",
                background="#E8F5EC",
                padding="0.85rem 1rem",
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
                    # Anel de foco verde, no lugar do azul do tema.
                    _focus_visible=WIZARD_FOCUS,
                ),
                rx.fragment(),
            ),
            rx.cond(
                DonationCreateState.current_step < 5,
                rx.button(
                    "Continuar",
                    type="button",
                    on_click=DonationCreateState.advance,
                    disabled=(
                        DonationCreateState.is_loading_data
                        | DonationCreateState.photos_busy
                    ),
                    background="#007A42",
                    color="white",
                    _hover={"background": "#006B39"},
                    _focus_visible=WIZARD_FOCUS,
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
                    on_click=DonationCreateState.publish,
                    disabled=(
                        DonationCreateState.is_publishing
                        | DonationCreateState.published
                    ),
                    background="#007A42",
                    color="white",
                    _hover={"background": "#006B39"},
                    _focus_visible=WIZARD_FOCUS,
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


def _back_link() -> rx.Component:
    # Faixa de largura total: a seta fica no canto esquerdo, logo abaixo do
    # cabeçalho, e não acompanha a coluna centralizada do wizard.
    return rx.box(
        rx.link(
            rx.icon("chevron-left", size=24),
            href="/",
            color="#166B3B",
            font_weight="600",
            aria_label="Voltar ao início",
        ),
        width="100%",
        padding="0.75rem 1.25rem 0",
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
        _back_link(),
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
