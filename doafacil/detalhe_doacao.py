import os
import re
from typing import Any
from urllib.parse import urlsplit

import httpx
import reflex as rx


DONATION_DETAIL_PATH = "/catalog/donations/detail"
GENERIC_DETAIL_IMAGE = "/doacao-generica.svg"
DONATION_NOT_FOUND_MESSAGE = "Doação não encontrada"
DONATION_DETAIL_ERROR_MESSAGE = (
    "Não foi possível carregar os detalhes da doação. Tente novamente mais tarde."
)


class DonationNotFoundError(Exception):
    pass


def _positive_donation_id(value: object) -> int:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]+", value) is None:
        raise DonationNotFoundError

    try:
        donation_id = int(value)
    except ValueError as error:
        raise DonationNotFoundError from error
    if donation_id <= 0:
        raise DonationNotFoundError
    return donation_id


def _donation_detail_endpoint(base_url: str, donation_id: int) -> str:
    parsed_url = urlsplit(base_url.strip())
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("XANO_API_URL precisa conter uma URL HTTP(S) válida.")
    return f"{base_url.strip().rstrip('/')}{DONATION_DETAIL_PATH}?donation_id={donation_id}"


def _parse_donation_detail(
    payload: object, expected_id: int
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("A resposta do detalhe precisa ser um objeto.")

    donation_id = payload.get("id")
    title = payload.get("title")
    condition = payload.get("condition")
    description = payload.get("description")
    category = payload.get("category")
    city = payload.get("city")
    state = payload.get("state")
    delivery_method = payload.get("delivery_method")
    contact_preference = payload.get("contact_preference")
    donor_first_name = payload.get("donor_first_name")
    photos = payload.get("photos")

    if (
        isinstance(donation_id, bool)
        or not isinstance(donation_id, int)
        or donation_id != expected_id
        or not isinstance(title, str)
        or not title.strip()
        or not isinstance(condition, str)
        or condition not in {"Ótimo", "Bom", "Regular"}
        or not isinstance(description, str)
        or not isinstance(category, str)
        or not category.strip()
        or not isinstance(city, str)
        or not isinstance(state, str)
        or not isinstance(delivery_method, str)
        or not delivery_method.strip()
        or not isinstance(contact_preference, str)
        or not contact_preference.strip()
        or not isinstance(donor_first_name, str)
        or not isinstance(photos, list)
        or any(not isinstance(photo, str) or not photo.strip() for photo in photos)
    ):
        raise ValueError("A resposta do detalhe contém dados inválidos.")

    unique_photos = list(dict.fromkeys(photos))
    if not unique_photos:
        unique_photos = [GENERIC_DETAIL_IMAGE]

    return {
        "id": donation_id,
        "title": title,
        "condition": condition,
        "description": description,
        "category": category,
        "city": city,
        "state": state,
        "delivery_method": delivery_method,
        "contact_preference": contact_preference,
        "donor_first_name": donor_first_name,
        "photos": unique_photos,
    }


async def _fetch_donation_detail(
    client: httpx.AsyncClient,
    base_url: str,
    donation_id_value: object,
) -> dict[str, Any]:
    donation_id = _positive_donation_id(donation_id_value)
    endpoint = _donation_detail_endpoint(base_url, donation_id)
    response = await client.get(endpoint)
    if response.status_code == 404:
        raise DonationNotFoundError
    response.raise_for_status()
    return _parse_donation_detail(response.json(), donation_id)


class DonationDetailState(rx.State):
    donation_id: int = 0
    title: str = ""
    condition: str = ""
    description: str = ""
    category: str = ""
    city: str = ""
    state: str = ""
    delivery_method: str = ""
    contact_preference: str = ""
    donor_first_name: str = ""
    photos: list[str] = []
    view_state: str = "loading"

    @rx.event
    async def load_donation(self) -> None:
        self.donation_id = 0
        self.title = ""
        self.condition = ""
        self.description = ""
        self.category = ""
        self.city = ""
        self.state = ""
        self.delivery_method = ""
        self.contact_preference = ""
        self.donor_first_name = ""
        self.photos = []
        self.view_state = "loading"
        donation_id = self.router.page.params.get("id", "")

        try:
            _positive_donation_id(donation_id)
            base_url = os.getenv("XANO_API_URL", "").strip()
            async with httpx.AsyncClient(timeout=15.0) as client:
                donation = await _fetch_donation_detail(
                    client,
                    base_url,
                    donation_id,
                )
        except DonationNotFoundError:
            self.view_state = "not_found"
        except (httpx.HTTPError, ValueError):
            self.view_state = "error"
        else:
            self.donation_id = donation["id"]
            self.title = donation["title"]
            self.condition = donation["condition"]
            self.description = donation["description"]
            self.category = donation["category"]
            self.city = donation["city"]
            self.state = donation["state"]
            self.delivery_method = donation["delivery_method"]
            self.contact_preference = donation["contact_preference"]
            self.donor_first_name = donation["donor_first_name"]
            self.photos = donation["photos"]
            self.view_state = "loaded"


def _gallery_thumbnail(photo: rx.Var[str]) -> rx.Component:
    return rx.image(
        src=photo,
        alt="Foto da doação",
        width="100%",
        height="150px",
        object_fit="cover",
        border_radius="10px",
        background="#EEEEEE",
    )


def _header() -> rx.Component:
    return rx.box(
        rx.image(
            src="/logo.svg",
            alt="DoaFácil",
            width="190px",
            height="72px",
            object_fit="contain",
        ),
        display="flex",
        justify_content="center",
        align_items="center",
        width="100%",
        background="white",
        padding="8px 24px",
    )


def _donation_content() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.box(
                rx.vstack(
                    rx.image(
                        src=DonationDetailState.photos[0],
                        alt=DonationDetailState.title,
                        width="100%",
                        height=rx.breakpoints(
                            initial="280px", md="440px"
                        ),
                        object_fit="cover",
                        border_radius="12px",
                        background="#EEEEEE",
                    ),
                    rx.flex(
                        rx.foreach(
                            DonationDetailState.photos[1:],
                            _gallery_thumbnail,
                        ),
                        wrap="wrap",
                        gap="12px",
                        width="100%",
                    ),
                    align="stretch",
                    spacing="3",
                    width="100%",
                ),
                rx.vstack(
                    rx.heading(
                        DonationDetailState.title,
                        font_size=rx.breakpoints(
                            initial="1.6rem", md="2.1rem"
                        ),
                        color="#222222",
                        line_height="1.2",
                    ),
                    rx.text(
                        "Condição: ",
                        DonationDetailState.condition,
                        color="#333333",
                        font_size="1rem",
                    ),
                    rx.divider(),
                    rx.text("Forma de entrega", font_weight="700", color="#333333"),
                    rx.text(
                        DonationDetailState.delivery_method,
                        color="#555555",
                    ),
                    rx.text(
                        "Preferência de contato",
                        font_weight="700",
                        color="#333333",
                    ),
                    rx.text(
                        DonationDetailState.contact_preference,
                        color="#555555",
                    ),
                    align="stretch",
                    spacing="3",
                    width="100%",
                    padding="24px",
                    background="white",
                    border_radius="12px",
                    box_shadow="0 2px 12px rgba(39, 39, 39, 0.10)",
                ),
                style={
                    "display": "grid",
                    "gridTemplateColumns": rx.breakpoints(
                        initial="1fr", md="minmax(0, 1.7fr) minmax(280px, 1fr)"
                    ),
                },
                gap="24px",
                width="100%",
                align_items="start",
            ),
            rx.box(
                rx.vstack(
                    rx.vstack(
                        rx.heading(
                            "Detalhes",
                            font_size="1.35rem",
                            color="#333333",
                            class_name="page-fade-enter",
                        ),
                        rx.text(
                            "Descrição",
                            font_weight="700",
                            color="#333333",
                        ),
                        rx.text(
                            DonationDetailState.description,
                            color="#555555",
                            white_space="pre-wrap",
                        ),
                        rx.text(
                            "Categoria",
                            font_weight="700",
                            color="#333333",
                        ),
                        rx.text(
                            DonationDetailState.category,
                            color="#555555",
                        ),
                        align="stretch",
                        spacing="3",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.heading(
                            "Localização",
                            font_size="1.35rem",
                            color="#333333",
                            class_name="page-fade-enter",
                        ),
                        rx.text(
                            DonationDetailState.city,
                            ", ",
                            DonationDetailState.state,
                            color="#555555",
                        ),
                        align="stretch",
                        spacing="3",
                        width="100%",
                        padding_top="24px",
                        border_top="1px solid #D8D0C5",
                    ),
                    align="stretch",
                    spacing="6",
                    width="100%",
                ),
                rx.vstack(
                    rx.heading(
                        "Quem doa",
                        font_size="1.2rem",
                        color="#333333",
                        class_name="page-fade-enter",
                    ),
                    rx.text(
                        DonationDetailState.donor_first_name,
                        font_weight="700",
                        color="#333333",
                    ),
                    rx.text(
                        DonationDetailState.city,
                        ", ",
                        DonationDetailState.state,
                        color="#555555",
                    ),
                    align="stretch",
                    spacing="2",
                    width="100%",
                    padding="24px",
                    background="white",
                    border_radius="12px",
                    box_shadow="0 2px 12px rgba(39, 39, 39, 0.10)",
                ),
                style={
                    "display": "grid",
                    "gridTemplateColumns": rx.breakpoints(
                        initial="1fr", md="minmax(0, 1.7fr) minmax(280px, 1fr)"
                    ),
                },
                gap="24px",
                width="100%",
                align_items="start",
            ),
            align="stretch",
            spacing="6",
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding="32px 24px 56px",
        ),
        width="100%",
        min_height="calc(100vh - 88px)",
        background="#FFF6E8",
    )


def _detail_state_message(message: str, color: str) -> rx.Component:
    return rx.box(
        rx.text(message, color=color, text_align="center"),
        display="flex",
        align_items="center",
        justify_content="center",
        width="100%",
        min_height="calc(100vh - 88px)",
        padding="24px",
        background="#FFF6E8",
        class_name="page-fade-enter",
    )


def donation_detail_page() -> rx.Component:
    return rx.box(
        _header(),
        rx.cond(
            DonationDetailState.view_state == "loading",
            _detail_state_message("Carregando doação...", "#555555"),
            rx.cond(
                DonationDetailState.view_state == "not_found",
                _detail_state_message(
                    DONATION_NOT_FOUND_MESSAGE,
                    "#555555",
                ),
                rx.cond(
                    DonationDetailState.view_state == "error",
                    _detail_state_message(
                        DONATION_DETAIL_ERROR_MESSAGE,
                        "#9B2C2C",
                    ),
                    _donation_content(),
                ),
            ),
        ),
        display="flex",
        flex_direction="column",
        width="100%",
        min_height="100vh",
        background="#FFF6E8",
        font_family="'LINE Seed JP', Arial, sans-serif",
    )
