import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit

import httpx
import reflex as rx


RECENT_DONATIONS_PATH = "/catalog/donations/recent"
DONATION_COUNT_PATH = "/catalog/donations/count"
GENERIC_DONATION_IMAGE = "/doacao-generica.svg"
AVAILABLE_CONDITIONS = {"Ótimo", "Bom", "Regular"}


def _xano_endpoints() -> tuple[str, str]:
    base_url = os.getenv("XANO_API_URL", "").strip()
    parsed_url = urlsplit(base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("XANO_API_URL precisa conter uma URL HTTP(S) válida.")

    base_url = base_url.rstrip("/")
    return (
        f"{base_url}{RECENT_DONATIONS_PATH}",
        f"{base_url}{DONATION_COUNT_PATH}",
    )


def _is_new_donation(
    created_at: str | int, now: datetime | None = None
) -> bool:
    if isinstance(created_at, bool):
        raise ValueError("A data de criação da doação é inválida.")
    if isinstance(created_at, int):
        try:
            created = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
                milliseconds=created_at
            )
        except OverflowError as error:
            raise ValueError(
                "A data de criação da doação é inválida."
            ) from error
    elif isinstance(created_at, str):
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    else:
        raise ValueError("A data de criação da doação é inválida.")

    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    age = current_time - created
    return timedelta(0) <= age <= timedelta(days=7)


def _parse_donations(
    payload: object, now: datetime | None = None
) -> list[dict[str, str | int | bool]]:
    if not isinstance(payload, list):
        raise ValueError("A resposta de doações recentes precisa ser uma lista.")

    donations: list[dict[str, str | int | bool]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("A resposta contém uma doação inválida.")

        donation_id = item.get("id")
        created_at = item.get("created_at")
        title = item.get("title")
        photo = item.get("photo")
        condition = item.get("condition")

        if (
            isinstance(donation_id, bool)
            or not isinstance(donation_id, int)
            or isinstance(created_at, bool)
            or not isinstance(created_at, (str, int))
            or not isinstance(title, str)
            or not title.strip()
        ):
            raise ValueError("A resposta contém campos obrigatórios inválidos.")
        if photo is not None and not isinstance(photo, str):
            raise ValueError("A foto da doação precisa ser uma URL ou nula.")
        if condition is not None and (
            not isinstance(condition, str)
            or condition not in AVAILABLE_CONDITIONS
        ):
            raise ValueError("A condição da doação não é reconhecida.")

        try:
            is_new = _is_new_donation(created_at, now)
        except ValueError as error:
            raise ValueError("A data de criação da doação é inválida.") from error

        donations.append(
            {
                "id": donation_id,
                "title": title,
                "photo": photo or GENERIC_DONATION_IMAGE,
                "condition_label": (
                    f"Condição: {condition}"
                    if condition
                    else "Condição não informada"
                ),
                "is_new": is_new,
            }
        )

    return donations


async def _fetch_recent_donations(
    client: httpx.AsyncClient, url: str
) -> list[dict[str, str | int | bool]]:
    response = await client.get(url)
    response.raise_for_status()
    return _parse_donations(response.json())


async def _fetch_donation_count(client: httpx.AsyncClient, url: str) -> int:
    response = await client.get(url)
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("A resposta da contagem de doações é inválida.")
    count = payload.get("count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("A resposta da contagem de doações é inválida.")
    return count


async def _load_count_result(
    client: httpx.AsyncClient, url: str
) -> int | Exception:
    try:
        return await _fetch_donation_count(client, url)
    except (httpx.HTTPError, ValueError) as error:
        return error


async def _load_donations_result(
    client: httpx.AsyncClient, url: str
) -> list[dict[str, str | int | bool]] | Exception:
    try:
        return await _fetch_recent_donations(client, url)
    except (httpx.HTTPError, ValueError) as error:
        return error


class HomeState(rx.State):
    donation_count: int = 0
    count_loading: bool = True
    count_error: str = ""
    donations: list[dict[str, Any]] = []
    donations_loading: bool = True
    donations_error: str = ""

    @rx.event
    async def load_home_data(self) -> None:
        self.count_loading = True
        self.count_error = ""
        self.donations_loading = True
        self.donations_error = ""

        try:
            recent_url, count_url = _xano_endpoints()
        except ValueError:
            self.count_error = (
                "Não foi possível carregar a contagem. "
                "Configure XANO_API_URL para conectar ao Xano."
            )
            self.donations_error = (
                "Não foi possível carregar as doações recentes. "
                "Configure XANO_API_URL para conectar ao Xano."
            )
            self.count_loading = False
            self.donations_loading = False
            return

        async with httpx.AsyncClient(timeout=10.0) as client:
            count_result, donations_result = await asyncio.gather(
                _load_count_result(client, count_url),
                _load_donations_result(client, recent_url),
            )

        if isinstance(count_result, Exception):
            self.count_error = "Não foi possível carregar a contagem de doações."
        else:
            self.donation_count = count_result
        self.count_loading = False

        if isinstance(donations_result, Exception):
            self.donations_error = (
                "Não foi possível carregar as doações recentes."
            )
        else:
            self.donations = donations_result
        self.donations_loading = False


def donation_card(donation: rx.Var[dict[str, Any]]) -> rx.Component:
    return rx.box(
        rx.cond(
            donation["photo"] == GENERIC_DONATION_IMAGE,
            rx.image(
                src=donation["photo"],
                alt=donation["title"],
                position="absolute",
                top="4%",
                left="16%",
                width="68%",
                height="68%",
                object_fit="contain",
            ),
            rx.image(
                src=donation["photo"],
                alt=donation["title"],
                position="absolute",
                inset="0",
                width="100%",
                height="100%",
                object_fit="cover",
            ),
        ),
        rx.cond(
            donation["is_new"],
            rx.badge(
                "NOVO",
                position="absolute",
                top="12px",
                left="12px",
                background="#C62828",
                color="white",
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.vstack(
                rx.heading(
                    donation["title"],
                    size="4",
                    color="white",
                    no_of_lines=2,
                ),
                rx.text(
                    donation["condition_label"],
                    color="white",
                    font_size="0.9rem",
                ),
                align="start",
                spacing="1",
            ),
            rx.button(
                "Acessar",
                color_scheme="green",
                variant="solid",
                size="2",
                cursor="default",
                flex_shrink="0",
            ),
            align="end",
            justify="between",
            position="absolute",
            bottom="0",
            left="0",
            width="100%",
            padding="16px",
            min_height="48%",
            background=(
                "linear-gradient(180deg, transparent 0%, "
                "rgba(0, 0, 0, 0.78) 55%)"
            ),
        ),
        position="relative",
        overflow="hidden",
        border_radius="16px",
        min_width="0",
        width="100%",
        aspect_ratio="1 / 1",
        background="#FFF6E8",
        box_shadow="0 4px 16px rgba(39, 39, 39, 0.12)",
    )


def donation_count_view() -> rx.Component:
    return rx.vstack(
        rx.cond(
            HomeState.count_loading,
            rx.text("Carregando...", color="#555555"),
            rx.cond(
                HomeState.count_error != "",
                rx.text(HomeState.count_error, color="#9B2C2C"),
                rx.text(
                    HomeState.donation_count,
                    font_size="2rem",
                    font_weight="700",
                    color="#1EAB59",
                ),
            ),
        ),
        rx.text(
            "Doações em circulação",
            font_size="1.1rem",
            font_weight="600",
            color="#333333",
        ),
        align="start",
        spacing="1",
        width={"initial": "100%", "lg": "150px"},
        flex_shrink="0",
    )


def recent_donations_view() -> rx.Component:
    return rx.vstack(
        rx.heading("Doações mais recentes", size="6", color="#333333"),
        rx.cond(
            HomeState.donations_loading,
            rx.text("Carregando doações recentes...", color="#555555"),
            rx.cond(
                HomeState.donations_error != "",
                rx.text(HomeState.donations_error, color="#9B2C2C"),
                rx.cond(
                    HomeState.donations.length() == 0,
                    rx.text(
                        "Ainda não há doações recentes.",
                        color="#555555",
                    ),
                    rx.grid(
                        rx.foreach(HomeState.donations, donation_card),
                        columns={
                            "initial": "1fr",
                            "sm": "repeat(2, minmax(0, 1fr))",
                            "lg": "repeat(4, minmax(0, 1fr))",
                        },
                        spacing="4",
                        width="100%",
                    ),
                ),
            ),
        ),
        align="stretch",
        spacing="5",
        width="100%",
        flex="1",
        min_width="0",
    )


def index() -> rx.Component:
    return rx.box(
        rx.box(
            rx.hstack(
                rx.image(
                    src="/logo.svg",
                    alt="DoaFácil",
                    width="190px",
                    height="72px",
                    object_fit="contain",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.link(
                        "Explorar Doações",
                        href="#",
                        color="#168447",
                        font_weight="700",
                        white_space="nowrap",
                    ),
                    rx.link(
                        "Como funciona",
                        href="#",
                        color="#168447",
                        font_weight="700",
                        white_space="nowrap",
                    ),
                    rx.link(
                        "Categorias",
                        href="#",
                        color="#168447",
                        font_weight="700",
                        white_space="nowrap",
                    ),
                    spacing="6",
                    display={"initial": "none", "lg": "flex"},
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        "Entrar",
                        variant="outline",
                        color="#168447",
                        border_color="#168447",
                        size="3",
                    ),
                    rx.button(
                        "Quero Doar",
                        background="#168447",
                        color="white",
                        size="3",
                    ),
                    spacing="3",
                ),
                align="center",
                width="100%",
                max_width="1200px",
                margin="0 auto",
                padding="12px 24px",
            ),
            width="100%",
            background="white",
        ),
        rx.vstack(
            rx.vstack(
                rx.heading(
                    "Doar é fácil.",
                    " No DoaFácil, o que sobra em você vira recomeço para alguém.",
                    size={"initial": "7", "md": "9"},
                    color="#333333",
                    text_align="center",
                    font_weight="700",
                    max_width="1120px",
                    line_height="1.2",
                ),
                align="center",
                justify="center",
                width="100%",
                padding_top={"initial": "48px", "md": "72px"},
                padding_bottom={"initial": "44px", "md": "64px"},
            ),
            rx.hstack(
                donation_count_view(),
                recent_donations_view(),
                align="center",
                spacing={"initial": "6", "lg": "8"},
                width="100%",
                max_width="1280px",
                padding_x="24px",
                flex_direction={"initial": "column", "lg": "row"},
            ),
            align="center",
            spacing="7",
            width="100%",
            flex="1",
            padding_bottom="56px",
            background="#FFF6E8",
        ),
        rx.image(
            src="/ilustracao-rodape.png",
            alt="Pessoas reunidas na comunidade DoaFácil",
            width="100%",
            height="auto",
            display="block",
            object_fit="contain",
            flex_shrink="0",
        ),
        display="flex",
        flex_direction="column",
        width="100%",
        min_height="100vh",
        background="#FFF6E8",
        font_family="'LINE Seed JP', Arial, sans-serif",
    )


app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=LINE+Seed+JP:wght@400;700&display=swap"
    ]
)
app.add_page(index, on_load=HomeState.load_home_data)
