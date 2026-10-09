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
            rx.fragment(),
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
            rx.fragment(),
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
        rx.vstack(
            rx.heading(
                donation["title"],
                font_size="1.1rem",
                font_weight="700",
                color="white",
                no_of_lines=2,
            ),
            rx.text(
                donation["condition_label"],
                color="white",
                font_size="0.85rem",
                white_space="normal",
                width="100%",
                overflow_wrap="anywhere",
            ),
            rx.button(
                "Acessar",
                color_scheme="green",
                variant="solid",
                size="1",
                cursor="default",
                align_self="end",
            ),
            align="start",
            spacing="2",
            position="absolute",
            bottom="0",
            left="0",
            width="100%",
            padding="16px",
            min_height="48%",
            background=rx.cond(
                donation["photo"] == GENERIC_DONATION_IMAGE,
                "linear-gradient(180deg, transparent 0%, "
                "rgba(15, 123, 62, 0.92) 55%)",
                "linear-gradient(180deg, transparent 0%, "
                "rgba(0, 0, 0, 0.78) 55%)",
            ),
        ),
        position="relative",
        overflow="hidden",
        border_radius="16px",
        min_width="0",
        width="260px",
        max_width="100%",
        aspect_ratio="1 / 1",
        background=rx.cond(
            donation["photo"] == GENERIC_DONATION_IMAGE,
            "#DDF3E5",
            "#FFF6E8",
        ),
        box_shadow="0 4px 16px rgba(39, 39, 39, 0.12)",
    )


def donation_count_view() -> rx.Component:
    return rx.vstack(
        rx.cond(
            HomeState.count_loading,
            rx.text("Carregando...", color="#555555"),
            rx.cond(
                HomeState.count_error != "",
                rx.text(
                    HomeState.count_error,
                    color="#9B2C2C",
                    width="100%",
                    white_space="normal",
                    overflow_wrap="anywhere",
                ),
                rx.text(
                    HomeState.donation_count,
                    font_size="3rem",
                    font_weight="700",
                    color="#1EAB59",
                ),
            ),
        ),
        rx.text(
            "Doações em circulação",
            font_size="1rem",
            font_weight="600",
            color="#333333",
            white_space="nowrap",
        ),
        align="start",
        spacing="1",
        style={"width": rx.breakpoints(initial="100%", lg="150px")},
        min_width="0",
        flex_shrink="0",
    )


def recent_donations_view() -> rx.Component:
    donation_count = HomeState.donations.length()
    group_width = rx.cond(
        donation_count == 0,
        "100%",
        rx.cond(
            donation_count == 1,
            "260px",
            rx.cond(
                donation_count == 2,
                "536px",
                rx.cond(donation_count == 3, "812px", "1104px"),
            ),
        ),
    )

    return rx.vstack(
        rx.heading(
            "Doações mais recentes",
            font_size="1.5rem",
            color="#333333",
        ),
        rx.cond(
            HomeState.donations_loading,
            rx.text("Carregando doações recentes...", color="#555555"),
            rx.cond(
                HomeState.donations_error != "",
                rx.text(
                    HomeState.donations_error,
                    color="#9B2C2C",
                    width="100%",
                    white_space="normal",
                    overflow_wrap="anywhere",
                ),
                rx.cond(
                    HomeState.donations.length() == 0,
                    rx.text(
                        "Ainda não há doações recentes.",
                        color="#555555",
                    ),
                    rx.flex(
                        rx.foreach(HomeState.donations, donation_card),
                        wrap="wrap",
                        justify="center",
                        align="start",
                        gap="16px",
                        width="100%",
                    ),
                ),
            ),
        ),
        align="stretch",
        spacing="5",
        width=group_width,
        max_width="100%",
        min_width="0",
        margin_x="auto",
    )


def start_here_card(
    title: str,
    description: str,
    icon_name: str,
    coming_soon: bool = False,
) -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.box(
                rx.icon(icon_name, size=28, color="white"),
                display="flex",
                align_items="center",
                justify_content="center",
                width="64px",
                height="64px",
                border_radius="50%",
                background="#2DBF72",
            ),
            rx.heading(
                title,
                font_size="1.4rem",
                font_weight="700",
                color="#333333",
                text_align="center",
                min_height="2.8em",
                display="flex",
                align_items="center",
            ),
            rx.text(
                description,
                font_size="1.1rem",
                line_height="1.25",
                color="#666666",
                text_align="center",
            ),
            align="center",
            justify="start",
            spacing="4",
            width="100%",
        ),
        rx.badge(
            "Em breve",
            color="#168447",
            background="#E3F5EA",
            border_radius="999px",
        )
        if coming_soon
        else rx.text(
            "→",
            font_size="2rem",
            line_height="1",
            color="#333333",
            aria_hidden=True,
        ),
        align="center",
        justify="between",
        spacing="6",
        style={
            "width": rx.breakpoints(
                initial="100%", md="calc((100% - 48px) / 3)"
            )
        },
        min_height="280px",
        padding="2rem",
        background="white",
        border="1px solid #E3E0DA",
        border_radius="16px",
        box_shadow="0 3px 12px rgba(39, 39, 39, 0.08)",
    )


def visual_search_select(options: list[str], default_value: str) -> rx.Component:
    return rx.select.root(
        rx.select.trigger(
            width="100%",
            background="white",
            color="#6B6B6B",
            border="1px solid #C8C8C8",
            border_radius="8px",
            opacity="1",
        ),
        rx.select.content(
            rx.select.group(
                *[
                    rx.select.item(option, value=option)
                    for option in options
                ]
            )
        ),
        default_value=default_value,
        width="100%",
    )


def start_here_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                "COMECE POR AQUI",
                font_size="1rem",
                font_weight="700",
                letter_spacing="0.08em",
                color="#168447",
                margin_bottom="1rem",
            ),
            rx.heading(
                "Quer criar uma doação?",
                font_weight="700",
                color="#333333",
                line_height="1.2",
                style={"fontSize": rx.breakpoints(initial="2rem", md="2.5rem")},
                margin_bottom="1.5rem",
            ),
            rx.text(
                "Leva só alguns minutos: conte o que você quer doar e a gente conecta você a quem precisa.",
                font_weight="700",
                color="#333333",
                line_height="1.4",
                max_width="900px",
                style={"fontSize": rx.breakpoints(initial="1.2rem", md="1.5rem")},
                margin_bottom="3rem",
            ),
            rx.flex(
                start_here_card(
                    "Para você mesmo",
                    "Escolha um item disponível e receba de alguém que está desapegando.",
                    "user-round",
                ),
                start_here_card(
                    "Ajude quem precisa",
                    "Cadastre um objeto que você não usa mais e encontre quem precisa.",
                    "hand-heart",
                ),
                start_here_card(
                    "Desapego em grupo",
                    "Para família ou uma empresa que quer doar vários itens de uma vez.",
                    "briefcase",
                    coming_soon=True,
                ),
                wrap="wrap",
                style={
                    "flexDirection": rx.breakpoints(
                        initial="column", md="row"
                    )
                },
                justify="center",
                align="stretch",
                gap="1.5rem",
                width="100%",
                margin_bottom="3rem",
            ),
            rx.flex(
                rx.vstack(
                    rx.text(
                        "Buscar doações",
                        font_size="0.95rem",
                        font_weight="700",
                        color="#333333",
                    ),
                    rx.input(
                        placeholder="O que você está procurando?",
                        id="public-home-search",
                        width="100%",
                        background="white",
                        color="#333333",
                        border="1px solid #C8C8C8",
                        border_radius="8px",
                        opacity="1",
                        _placeholder={
                            "color": "#6b6b6b",
                            "opacity": 1,
                        },
                    ),
                    align="stretch",
                    spacing="2",
                    style={
                        "width": rx.breakpoints(
                            initial="100%", md="calc((100% - 48px) / 4)"
                        )
                    },
                ),
                rx.vstack(
                    rx.text(
                        "Categoria",
                        font_size="0.95rem",
                        font_weight="700",
                        color="#333333",
                    ),
                    visual_search_select(
                        [
                            "Todas as categorias",
                            "Roupas",
                            "Móveis",
                            "Livros",
                            "Eletrônicos",
                            "Brinquedos",
                            "Outros",
                        ],
                        "Todas as categorias",
                    ),
                    align="stretch",
                    spacing="2",
                    style={
                        "width": rx.breakpoints(
                            initial="100%", md="calc((100% - 48px) / 4)"
                        )
                    },
                ),
                rx.vstack(
                    rx.text(
                        "Localização",
                        font_size="0.95rem",
                        font_weight="700",
                        color="#333333",
                    ),
                    visual_search_select(
                        ["Todas as localizações"],
                        "Todas as localizações",
                    ),
                    align="stretch",
                    spacing="2",
                    style={
                        "width": rx.breakpoints(
                            initial="100%", md="calc((100% - 48px) / 4)"
                        )
                    },
                ),
                rx.button(
                    "Buscar",
                    background="#252525",
                    color="white",
                    align_self="end",
                    style={
                        "width": rx.breakpoints(
                            initial="100%", md="calc((100% - 48px) / 4)"
                        )
                    },
                ),
                wrap="wrap",
                style={
                    "flexDirection": rx.breakpoints(
                        initial="column", md="row"
                    )
                },
                align="stretch",
                justify="between",
                gap="16px",
                width="100%",
                padding="1.5rem",
                background="#FFF8EC",
                border_radius="12px",
            ),
            align="stretch",
            spacing="0",
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding="2.5rem 24px 5rem",
        ),
        width="100%",
        background="#FFF6E8",
    )


def institutional_card(
    category: str,
    title: str,
    icon_name: str,
    background: str,
) -> rx.Component:
    return rx.vstack(
        rx.icon(icon_name, size=30, color="white"),
        rx.vstack(
            rx.text(
                category,
                font_size="0.85rem",
                color="#F4F4F4",
            ),
            rx.heading(
                title,
                font_size="1.15rem",
                font_weight="700",
                color="white",
                line_height="1.2",
            ),
            rx.text(
                "Saiba mais",
                font_size="0.95rem",
                font_weight="700",
                color="white",
                text_decoration="underline",
            ),
            align="start",
            spacing="2",
            width="100%",
        ),
        align="start",
        justify="between",
        spacing="6",
        style={
            "width": rx.breakpoints(
                initial="100%",
                sm="calc((100% - 16px) / 2)",
                lg="calc((100% - 48px) / 4)",
            )
        },
        min_height="270px",
        padding="24px",
        background=background,
        border_radius="16px",
        box_shadow="0 4px 14px rgba(20, 35, 28, 0.12)",
    )


def institutional_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                "Doar no DoaFácil é simples e seguro.",
                font_weight="700",
                color="#333333",
                text_align="center",
                style={"fontSize": rx.breakpoints(initial="2rem", md="2.5rem")},
            ),
            rx.text(
                "Doações já circularam por aqui, conectando quem tem com quem precisa. "
                "Transparência em cada etapa, do anúncio à entrega.",
                font_size="1.1rem",
                line_height="1.5",
                color="#4A4A4A",
                text_align="center",
                max_width="820px",
            ),
            rx.flex(
                institutional_card(
                    "Solidariedade",
                    "Conheça histórias de quem doou e quem recebeu",
                    "hand-heart",
                    "linear-gradient(145deg, #168447 0%, #333333 100%)",
                ),
                institutional_card(
                    "Segurança",
                    "Como funciona a autenticação e proteção dos seus dados",
                    "shield-check",
                    "linear-gradient(145deg, #333333 0%, #168447 100%)",
                ),
                institutional_card(
                    "Nossa missão",
                    "Descubra por que criamos o DoaFácil",
                    "heart",
                    "linear-gradient(145deg, #656B70 0%, #333333 100%)",
                ),
                institutional_card(
                    "Passo a passo",
                    "Veja como criar sua doação em poucos minutos",
                    "circle-check",
                    "linear-gradient(145deg, #168447 0%, #5B6262 100%)",
                ),
                wrap="wrap",
                style={
                    "flexDirection": rx.breakpoints(
                        initial="column", sm="row"
                    )
                },
                justify="center",
                align="stretch",
                gap="16px",
                width="100%",
            ),
            align="center",
            spacing="5",
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding="72px 24px 80px",
        ),
        width="100%",
        background="#EEEDEA",
    )


def public_home_footer() -> rx.Component:
    link_groups = (
        ("Quem somos", "Doações"),
        ("Criar doações", "Doações mais recentes"),
        ("Política de privacidade", "Termos de uso"),
        ("Dúvidas frequentes", "Segurança e transparência"),
    )
    return rx.box(
        rx.vstack(
            rx.image(
                src="/logo.svg",
                alt="DoaFácil",
                width="160px",
                height="58px",
                object_fit="contain",
            ),
            rx.flex(
                rx.vstack(
                    rx.text(
                        "Fale conosco",
                        font_size="15px",
                        font_weight="700",
                        color="#2DBF72",
                    ),
                    rx.text(
                        "Clique aqui para falar conosco",
                        color="#F5F5F5",
                        font_size="13px",
                    ),
                    align="start",
                    spacing="1",
                    style={"width": rx.breakpoints(initial="100%", md="28%")},
                ),
                rx.vstack(
                    rx.text(
                        "Links rápidos",
                        font_size="15px",
                        font_weight="700",
                        color="#2DBF72",
                    ),
                    rx.flex(
                        *[
                            rx.vstack(
                                *[
                                    rx.text(
                                        label,
                                        color="#F5F5F5",
                                        font_size="13px",
                                    )
                                    for label in group
                                ],
                                align="start",
                                spacing="0",
                                style={
                                    "rowGap": "6px",
                                    "width": rx.breakpoints(
                                        initial="50%", md="25%"
                                    )
                                },
                            )
                            for group in link_groups
                        ],
                        wrap="wrap",
                        align="start",
                        gap="0",
                        width="100%",
                    ),
                    align="start",
                    spacing="2",
                    style={
                        "width": rx.breakpoints(
                            initial="100%", md="calc(72% - 16px)"
                        )
                    },
                ),
                style={
                    "flexDirection": rx.breakpoints(
                        initial="column", md="row"
                    )
                },
                align="start",
                gap="4",
                width="100%",
            ),
            rx.text(
                "Projeto acadêmico DoaFácil",
                color="#D7D7D7",
                font_size="12px",
                border_top="1px solid #515151",
                padding_top="20px",
                width="100%",
            ),
            align="start",
            spacing="5",
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding="48px 24px 32px",
        ),
        width="100%",
        background="#252525",
        color="white",
    )


def index() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.box(
                rx.hstack(
                    rx.image(
                        src="/logo.svg",
                        alt="DoaFácil",
                        style={
                            "width": rx.breakpoints(initial="100px", md="190px")
                        },
                        height="72px",
                        object_fit="contain",
                    ),
                    rx.spacer(),
                    rx.desktop_only(
                        rx.hstack(
                            rx.text(
                                "Explorar Doações",
                                color="#168447",
                                font_weight="700",
                                white_space="nowrap",
                            ),
                            rx.text(
                                "Como funciona",
                                color="#168447",
                                font_weight="700",
                                white_space="nowrap",
                            ),
                            rx.text(
                                "Categorias",
                                color="#168447",
                                font_weight="700",
                                white_space="nowrap",
                            ),
                            spacing="6",
                        )
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.button(
                            "Entrar",
                            variant="outline",
                            color="#168447",
                            border_color="#168447",
                            size="2",
                        ),
                        rx.button(
                            "Quero Doar",
                            background="#168447",
                            color="white",
                            size="2",
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
                        color="#333333",
                        text_align="center",
                        font_weight="700",
                        max_width="900px",
                        width="100%",
                        line_height="1.2",
                        white_space="normal",
                        overflow_wrap="anywhere",
                        style={
                            "fontSize": rx.breakpoints(
                                initial="2rem", md="2.75rem"
                            )
                        },
                    ),
                    align="center",
                    justify="center",
                    width="100%",
                    padding_top="3rem",
                    padding_bottom="2.5rem",
                ),
                rx.hstack(
                    donation_count_view(),
                    recent_donations_view(),
                    align="center",
                    spacing="6",
                    width="100%",
                    max_width="1200px",
                    padding_x="24px",
                    style={
                        "flexDirection": rx.breakpoints(
                            initial="column", lg="row"
                        )
                    },
                ),
                align="center",
                spacing="7",
                width="100%",
                flex="1",
                padding_bottom="0",
                background="#FFF6E8",
            ),
            rx.image(
                src="/ilustracao-rodape.png",
                alt="Pessoas reunidas na comunidade DoaFácil",
                width="100%",
                height="auto",
                display="block",
                margin_top="0",
                margin_bottom="0",
                object_fit="contain",
                flex_shrink="0",
            ),
            align="stretch",
            spacing="0",
            width="100%",
            min_height="100vh",
            flex="1",
        ),
        start_here_section(),
        institutional_section(),
        public_home_footer(),
        display="flex",
        flex_direction="column",
        width="100%",
        min_height="100vh",
        background="#FFF6E8",
        font_family="'LINE Seed JP', Arial, sans-serif",
    )


app = rx.App(
    style={
        "#public-home-search::placeholder": {
            "color": "#6b6b6b",
            "opacity": "1",
        }
    },
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=LINE+Seed+JP:wght@400;700&display=swap"
    ]
)
app.add_page(index, on_load=HomeState.load_home_data)
