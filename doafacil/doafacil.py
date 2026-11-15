import asyncio
import os
from typing import Any
from urllib.parse import urlsplit

import httpx
import reflex as rx

from doafacil.cadastro import signup_page
from doafacil.cartoes_doacao import (  # noqa: F401 (reexportados para a home e os testes)
    AVAILABLE_CONDITIONS,
    GENERIC_DONATION_IMAGE,
    _is_new_donation,
    _parse_donations,
    donation_card,
)
from doafacil.chat import CHAT_FAB_CLEARANCE, ChatState, chat_fab, chat_page
from doafacil.cadastro_doacao import (
    DonationCreateState,
    donation_creation_page,
)
from doafacil.detalhe_doacao import (
    DonationDetailState,
    donation_detail_page,
)
from doafacil.editar_perfil import EditProfileState, edit_profile_page
from doafacil.explorar import (
    ALL_CATEGORIES_LABEL,
    ALL_LOCATIONS_LABEL,
    ALL_OPTION_VALUE,
    BRAZILIAN_STATES,
    EXPLORE_ROUTE,
    RECENT_DONATIONS_ANCHOR,
    ExploreState,
    build_explore_url,
    explore_page,
    fetch_categories,
)
from doafacil.cadastro_doacao import DonationServiceError
from doafacil.login import LoginState, login_page
from doafacil.minhas_doacoes import (
    EditDonationState,
    MyDonationsState,
    edit_donation_page,
    my_donations_page,
)
from doafacil.perfil_doador import DonorProfileState, donor_profile_page
from doafacil.recuperacao_senha import (
    new_password_page,
    request_recovery_page,
    verify_recovery_page,
)


RECENT_DONATIONS_PATH = "/catalog/donations/recent"
# Fonte do menu do cabeçalho: 14 px entre 992 e 1279 px (o menu só aparece a
# partir de 992 px), para nada quebrar linha com “Olá, <nome>”; 16 px depois.
NAV_FONT_SIZE = rx.breakpoints(initial="0.875rem", lg="1rem")
DONATION_COUNT_PATH = "/catalog/donations/count"
GREEN = "#168447"
# Verde escuro dos números e do texto de apoio: 5,8:1 sobre o creme (AA).
DARK_GREEN = "#166B3B"
CREAM = "#FFF6E8"
FOCUS_RING = {"outline": f"2px solid {GREEN}", "outlineOffset": "2px"}
# Título da primeira dobra e números, como no Figma (frame 655:2691).
HERO_TITLE_COLOR = "#2A2A2A"
HERO_TITLE_WIDTH = "1376px"
HERO_TITLE_FONT_SIZE = "clamp(1.5rem, 2.4vw, 2.25rem)"
# A linha dos números e do carrossel usa as mesmas bordas do conteúdo do
# cabeçalho: até 1200 px, com 16 px de margem no celular e 24 px a partir de md.
HEADER_MAX_WIDTH = "1200px"
HEADER_PADDING_X = rx.breakpoints(initial="16px", md="24px")
# Coluna dos números: 11rem (176 px). Em 1512 px, sobram 1152 - 176 - 32 =
# 944 px para o carrossel, e os 4 cartões ficam com cerca de 221 px.
STATS_COLUMN_WIDTH = "11rem"
# #005723 (token texto/primario do Figma): 8,9:1 sobre o creme.
STAT_COLOR = "#005723"
COUNT_ERROR_MESSAGE = "Não foi possível carregar a contagem de doações."
COMPLETED_ERROR_MESSAGE = "Não foi possível carregar este número."

# Rotas das páginas que ainda não existem (change landing-nova). Quando uma
# delas for criada, basta registrar a rota: os links já apontam para ela.
FUTURE_ROUTES = {
    "como_funciona": "/como-funciona",
    "categorias": "/categorias",
    "quem_somos": "/quem-somos",
    "contato": "/contato",
    "privacidade": "/privacidade",
    "termos": "/termos",
    "duvidas": "/duvidas",
    "seguranca": "/seguranca",
}
NAV_LINKS = (
    ("Explorar Doações", EXPLORE_ROUTE),
    ("Como funciona", FUTURE_ROUTES["como_funciona"]),
    ("Categorias", FUTURE_ROUTES["categorias"]),
)
FOOTER_LINK_GROUPS = (
    (("Quem somos", FUTURE_ROUTES["quem_somos"]), ("Doações", EXPLORE_ROUTE)),
    (("Criar doações", "/cadastro-doacao"), ("Doações mais recentes", RECENT_DONATIONS_ANCHOR)),
    (("Política de privacidade", FUTURE_ROUTES["privacidade"]), ("Termos de uso", FUTURE_ROUTES["termos"])),
    (("Dúvidas frequentes", FUTURE_ROUTES["duvidas"]), ("Segurança e transparência", FUTURE_ROUTES["seguranca"])),
)


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


async def _fetch_recent_donations(
    client: httpx.AsyncClient, url: str
) -> list[dict[str, str | int | bool]]:
    response = await client.get(url)
    response.raise_for_status()
    return _parse_donations(response.json())


def _valid_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


async def _fetch_donation_counts(
    client: httpx.AsyncClient, url: str
) -> tuple[int, int | None]:
    """Doações disponíveis e concluídas. Um `count` inválido invalida a
    resposta; um `completed` ausente ou inválido vira None (só a estatística
    “Pessoas alcançadas” fica com erro)."""
    response = await client.get(url)
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, dict) or not _valid_count(payload.get("count")):
        raise ValueError("A resposta da contagem de doações é inválida.")
    completed = payload.get("completed")
    return payload["count"], completed if _valid_count(completed) else None


async def _load_count_result(
    client: httpx.AsyncClient, url: str
) -> tuple[int, int | None] | Exception:
    try:
        return await _fetch_donation_counts(client, url)
    except (httpx.HTTPError, ValueError) as error:
        return error


async def _load_categories_result(client: httpx.AsyncClient) -> list[dict[str, str]]:
    """Categorias da busca; numa falha, só “Todas as categorias”."""
    try:
        return await fetch_categories(client)
    except (httpx.HTTPError, ValueError, DonationServiceError):
        return []


async def _load_donations_result(
    client: httpx.AsyncClient, url: str
) -> list[dict[str, str | int | bool]] | Exception:
    try:
        return await _fetch_recent_donations(client, url)
    except (httpx.HTTPError, ValueError) as error:
        return error


class HomeState(rx.State):
    donation_count: int = 0
    completed_count: int = 0
    count_loading: bool = True
    count_error: str = ""
    completed_error: str = ""
    donations: list[dict[str, Any]] = []
    donations_loading: bool = True
    donations_error: str = ""
    # Opções do seletor “Categoria” da busca: {id, name} em texto.
    categories: list[dict[str, str]] = []

    @rx.event
    def search(self, form_data: dict[str, Any]):
        """Busca da home: abre /explorar com os filtros escolhidos."""
        return rx.redirect(
            build_explore_url(
                form_data.get("q"),
                form_data.get("categoria"),
                form_data.get("uf"),
            )
        )

    @rx.event
    async def load_home_data(self) -> None:
        self.count_loading = True
        self.count_error = ""
        self.completed_error = ""
        self.donations_loading = True
        self.donations_error = ""

        try:
            recent_url, count_url = _xano_endpoints()
        except ValueError:
            self.count_error = (
                "Não foi possível carregar a contagem. "
                "Configure XANO_API_URL para conectar ao Xano."
            )
            self.completed_error = COMPLETED_ERROR_MESSAGE
            self.donations_error = (
                "Não foi possível carregar as doações recentes. "
                "Configure XANO_API_URL para conectar ao Xano."
            )
            self.categories = []
            self.count_loading = False
            self.donations_loading = False
            return

        async with httpx.AsyncClient(timeout=10.0) as client:
            count_result, donations_result, categories = await asyncio.gather(
                _load_count_result(client, count_url),
                _load_donations_result(client, recent_url),
                _load_categories_result(client),
            )

        if isinstance(count_result, Exception):
            self.count_error = COUNT_ERROR_MESSAGE
            self.completed_error = COMPLETED_ERROR_MESSAGE
        else:
            self.donation_count, completed = count_result
            if completed is None:
                self.completed_error = COMPLETED_ERROR_MESSAGE
            else:
                self.completed_count = completed
        self.count_loading = False
        self.categories = categories

        if isinstance(donations_result, Exception):
            self.donations_error = (
                "Não foi possível carregar as doações recentes."
            )
        else:
            self.donations = donations_result[:4]
        self.donations_loading = False


def _statistic(value: rx.Var, error: rx.Var, label: str) -> rx.Component:
    """Número e rótulo de uma estatística; erro ou carregando no lugar do
    número, nunca um valor fictício."""
    return rx.vstack(
        rx.cond(
            HomeState.count_loading,
            rx.text("Carregando...", color="#555555"),
            rx.cond(
                error != "",
                rx.text(
                    error,
                    color="#9B2C2C",
                    width="100%",
                    max_width="100%",
                    white_space="normal",
                    overflow_wrap="anywhere",
                    font_size="0.85rem",
                ),
                # Figma: LINE Seed JP Bold 24 px.
                rx.text(
                    value,
                    font_size="1.5rem",
                    font_weight="700",
                    line_height="normal",
                    color=STAT_COLOR,
                ),
            ),
        ),
        # Figma: LINE Seed JP Regular 16 px.
        rx.text(
            label,
            font_size="1rem",
            line_height="normal",
            color=STAT_COLOR,
            white_space="normal",
        ),
        align="start",
        spacing="0",
        width="100%",
    )


def donation_count_view() -> rx.Component:
    return rx.vstack(
        _statistic(HomeState.donation_count, HomeState.count_error, "Doações em circulação!"),
        _statistic(HomeState.completed_count, HomeState.completed_error, "Pessoas alcançadas"),
        align="start",
        spacing="5",
        style={"width": rx.breakpoints(initial="100%", md=STATS_COLUMN_WIDTH)},
        min_width=rx.breakpoints(initial="100%", md=STATS_COLUMN_WIDTH),
        flex_shrink="0",
    )


def recent_donations_view() -> rx.Component:
    return rx.vstack(
        rx.flex(
            rx.heading(
                "Doações mais recentes:",
                font_size="1.5rem",
                color="#333333",
            ),
            # Visível também com a lista vazia ou com erro.
            rx.link(
                "Ver mais...",
                href=EXPLORE_ROUTE,
                class_name="home-see-more",
                color=DARK_GREEN,
                font_size="0.9rem",
                font_weight="700",
                display="inline-flex",
                align_items="center",
                min_height="44px",
                _focus_visible=FOCUS_RING,
            ),
            justify="between",
            align="center",
            wrap="wrap",
            column_gap="16px",
            width="100%",
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
                        wrap="nowrap",
                        justify="start",
                        align="start",
                        gap="20px",
                        width="100%",
                        overflow_x="auto",
                        padding_bottom="8px",
                        class_name="recent-donations-carousel",
                        style={
                            "scrollSnapType": "x mandatory",
                            "scrollbarWidth": "thin",
                            "scrollbarColor": "#B8C8BC transparent",
                        },
                    ),
                ),
            ),
        ),
        align="stretch",
        spacing="5",
        width="100%",
        flex="1",
        max_width="100%",
        min_width="0",
        id="doacoes-recentes",
    )


START_CARD_WIDTH = rx.breakpoints(initial="100%", md="calc((100% - 48px) / 3)")


def start_here_card(
    title: str,
    description: str,
    icon_name: str,
    href: str | None = None,
    coming_soon: bool = False,
) -> rx.Component:
    """Cartão de “Comece por aqui”. Com `href`, o cartão inteiro é um link
    (seta decorativa); sem ele, mostra “Em breve” e não navega."""
    card = _start_here_card_body(title, description, icon_name, coming_soon, href is not None)
    if href is None:
        return card
    return rx.link(
        card,
        href=href,
        aria_label=f"{title}: {description}",
        class_name="home-start-card-link",
        display="flex",
        underline="none",
        color="inherit",
        border_radius="16px",
        style={"width": START_CARD_WIDTH},
        _focus_visible=FOCUS_RING,
        _hover={"textDecoration": "none"},
    )


def _start_here_card_body(
    title: str,
    description: str,
    icon_name: str,
    coming_soon: bool,
    in_link: bool,
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
        # Dentro do link, o cartão ocupa o link; sozinho, a coluna.
        style={"width": "100%" if in_link else START_CARD_WIDTH},
        min_height="280px",
        padding="2rem",
        background="white",
        border="1px solid #E3E0DA",
        border_radius="16px",
        box_shadow="0 3px 12px rgba(39, 39, 39, 0.08)",
    )


SEARCH_FIELD_WIDTH = rx.breakpoints(initial="100%", md="calc((100% - 48px) / 4)")


def search_select(
    name: str,
    label: str,
    all_label: str,
    items: rx.Component | list[rx.Component],
) -> rx.Component:
    """Seletor da busca: “Todas as …” (valor `todas`) e as opções dadas. O
    `name` vai no envio do formulário."""
    extra = items if isinstance(items, list) else [items]
    return rx.select.root(
        rx.select.trigger(
            aria_label=label,
            width="100%",
            background="white",
            color="#6B6B6B",
            border="1px solid #C8C8C8",
            border_radius="8px",
            opacity="1",
        ),
        rx.select.content(
            rx.select.group(
                rx.select.item(all_label, value=ALL_OPTION_VALUE),
                *extra,
            )
        ),
        name=name,
        default_value=ALL_OPTION_VALUE,
        width="100%",
    )


def _search_field(label: str, control: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(
            label,
            font_size="0.95rem",
            font_weight="700",
            color="#333333",
        ),
        control,
        align="stretch",
        spacing="2",
        style={"width": SEARCH_FIELD_WIDTH},
    )


def search_bar() -> rx.Component:
    """Busca da home: abre /explorar com `q`, `categoria` e `uf`, só para os
    filtros escolhidos (Enter no campo também envia)."""
    return rx.form(
        rx.flex(
            _search_field(
                "Buscar doações",
                rx.input(
                    name="q",
                    placeholder="O que você está procurando?",
                    id="public-home-search",
                    aria_label="Buscar doações",
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
            ),
            _search_field(
                "Categoria",
                search_select(
                    "categoria",
                    "Categoria",
                    ALL_CATEGORIES_LABEL,
                    rx.foreach(
                        HomeState.categories,
                        lambda category: rx.select.item(category["name"], value=category["id"]),
                    ),
                ),
            ),
            _search_field(
                "Localização",
                search_select(
                    "uf",
                    "Localização",
                    ALL_LOCATIONS_LABEL,
                    [rx.select.item(uf, value=uf) for uf in BRAZILIAN_STATES],
                ),
            ),
            rx.button(
                "Buscar",
                rx.icon("search", size=18, aria_hidden="true"),
                type="submit",
                background="#252525",
                color="white",
                align_self="end",
                min_height="44px",
                _focus_visible=FOCUS_RING,
                style={"width": SEARCH_FIELD_WIDTH},
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
        on_submit=HomeState.search,
        reset_on_submit=False,
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
                # #166B3B: 6,1:1 sobre o creme (o #168447 dá 4,4:1, abaixo do AA).
                color=DARK_GREEN,
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
                    href=EXPLORE_ROUTE,
                ),
                start_here_card(
                    "Ajude quem precisa",
                    "Cadastre um objeto que você não usa mais e encontre quem precisa.",
                    "hand-heart",
                    href="/cadastro-doacao",
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
            search_bar(),
            align="stretch",
            spacing="0",
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding="2.5rem 24px 5rem",
        ),
        width="100%",
        background="#FFF6E8",
        class_name="page-fade-enter",
    )


# Cartões institucionais (change landing-nova). As fotos do Figma têm marca
# d'água de banco de imagens e não são usadas: com `image` None, o cartão usa
# o degradê (placeholder). Para usar uma foto própria, coloque o arquivo em
# assets/landing/ e preencha `image` com o caminho (por exemplo,
# "/landing/historias.jpg"); um véu escuro embaixo mantém o texto legível.
INSTITUTIONAL_CARDS = (
    {
        "category": "Solidariedade",
        "title": "Histórias que continuam",
        "icon": "hand-heart",
        "image": None,
        "placeholder": "linear-gradient(145deg, #168447 0%, #333333 100%)",
    },
    {
        "category": "Segurança",
        "title": "Você no controle",
        "icon": "shield-check",
        "image": None,
        "placeholder": "linear-gradient(145deg, #333333 0%, #168447 100%)",
    },
    {
        "category": "Nossa missão",
        "title": "Nada se perde",
        "icon": "heart",
        "image": None,
        "placeholder": "linear-gradient(145deg, #656B70 0%, #333333 100%)",
    },
    {
        "category": "Passo a passo",
        "title": "Doar leva minutos",
        "icon": "check",
        "image": None,
        "placeholder": "linear-gradient(145deg, #168447 0%, #5B6262 100%)",
    },
)
INSTITUTIONAL_VEIL = "linear-gradient(180deg, rgba(0, 0, 0, 0) 35%, rgba(0, 0, 0, 0.72) 100%)"


def _institutional_background(card: dict[str, Any]) -> str:
    image = card["image"]
    if image:
        return f"{INSTITUTIONAL_VEIL}, url('{image}') center / cover no-repeat"
    return card["placeholder"]


def institutional_card(card: dict[str, Any]) -> rx.Component:
    """Cartão quadrado: ícone em círculo verde, categoria e título embaixo."""
    return rx.box(
        rx.vstack(
            rx.box(
                rx.icon(card["icon"], size=16, color="white", aria_hidden="true"),
                display="flex",
                align_items="center",
                justify_content="center",
                width="30px",
                height="30px",
                border_radius="50%",
                background=GREEN,
            ),
            rx.text(
                card["category"],
                font_size="0.85rem",
                color="white",
            ),
            rx.heading(
                card["title"],
                as_="h3",
                font_size="1.1rem",
                font_weight="700",
                color="white",
                line_height="1.2",
            ),
            align="start",
            spacing="1",
            width="100%",
        ),
        class_name="home-institutional-card",
        display="flex",
        align_items="flex-end",
        aspect_ratio="1",
        style={
            "width": rx.breakpoints(
                initial="100%",
                sm="calc((100% - 16px) / 2)",
                lg="calc((100% - 48px) / 4)",
            )
        },
        max_width=rx.breakpoints(initial="320px", lg="none"),
        padding="16px",
        background=_institutional_background(card),
        border_radius="16px",
        box_shadow="0 4px 14px rgba(20, 35, 28, 0.12)",
    )


def institutional_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                "Doar no DoaFácil é simples e seguro.",
                font_weight="700",
                color="#1F1F1F",
                line_height="1.15",
                style={"fontSize": rx.breakpoints(initial="2rem", md="3rem")},
            ),
            rx.text(
                "Doações já circularam por aqui, conectando quem tem com quem precisa. "
                "Transparência em cada etapa, do anúncio à entrega.",
                font_size="1.1rem",
                line_height="1.5",
                color=DARK_GREEN,
                max_width="820px",
            ),
            rx.flex(
                *[institutional_card(card) for card in INSTITUTIONAL_CARDS],
                wrap="wrap",
                style={
                    "flexDirection": rx.breakpoints(
                        initial="column", sm="row"
                    )
                },
                justify="center",
                align="center",
                gap="16px",
                width="100%",
                margin_top="1.5rem",
            ),
            align="start",
            spacing="3",
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding="72px 24px 80px",
        ),
        width="100%",
        background=CREAM,
        class_name="page-fade-enter",
    )


FOOTER_FOCUS_RING = {"outline": "2px solid #2DBF72", "outlineOffset": "2px"}


def _footer_link(label: str, href: str) -> rx.Component:
    """Link do rodapé: #F5F5F5 sobre #252525 (14,6:1), sem sublinhado."""
    return rx.link(
        label,
        href=href,
        color="#F5F5F5",
        font_size="13px",
        underline="hover",
        _focus_visible=FOOTER_FOCUS_RING,
    )


def public_home_footer() -> rx.Component:
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
                    _footer_link("Clique aqui para falar conosco", FUTURE_ROUTES["contato"]),
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
                                *[_footer_link(label, href) for label, href in group],
                                align="start",
                                spacing="0",
                                style={
                                    "rowGap": "6px",
                                    "width": rx.breakpoints(
                                        initial="50%", md="25%"
                                    )
                                },
                            )
                            for group in FOOTER_LINK_GROUPS
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
            padding_top="48px",
            padding_x="24px",
            # Espaço do botão flutuante: nada do rodapé fica sob ele.
            padding_bottom=CHAT_FAB_CLEARANCE,
        ),
        width="100%",
        background="#252525",
        color="white",
    )


def _nav_link(label: str, href: str) -> rx.Component:
    return rx.link(
        label,
        href=href,
        color=GREEN,
        font_weight="700",
        white_space="nowrap",
        font_size=NAV_FONT_SIZE,
        underline="hover",
        display="inline-flex",
        align_items="center",
        min_height="44px",
        _focus_visible=FOCUS_RING,
    )


def account_menu() -> rx.Component:
    """Menu da conta (change landing-nova): inicial e primeiro nome, com
    “Minhas doações”, “Editar perfil” e “Sair”. O Radix cuida do teclado
    (setas, Enter, Esc) e do foco."""
    name = LoginState.account_name
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.box(
                    name.to(str)[0].upper(),
                    aria_hidden="true",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    width="32px",
                    height="32px",
                    flex_shrink="0",
                    border_radius="50%",
                    background="#EDEDED",
                    border="1px solid #D6D6D6",
                    color="#555555",
                    font_weight="700",
                ),
                rx.text(
                    name,
                    class_name="home-account-name",
                    color="#333333",
                    font_weight="700",
                    white_space="nowrap",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    min_width="0",
                    max_width=rx.breakpoints(initial="80px", lg="120px"),
                    # Abaixo de 768 px (sm) fica só a inicial (o nome continua
                    # no rótulo acessível), para o cabeçalho caber em 360 px.
                    display=rx.breakpoints(initial="none", sm="block"),
                ),
                rx.icon("chevron-down", size=16, color="#333333", aria_hidden="true"),
                aria_label=rx.Var.create("Menu da conta de ") + name,
                class_name="home-account-menu",
                variant="ghost",
                display="inline-flex",
                align_items="center",
                gap="8px",
                min_height="44px",
                padding="0 8px",
                cursor="pointer",
                _focus_visible=FOCUS_RING,
            ),
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("package", size=16, aria_hidden="true"),
                "Minhas doações",
                on_select=rx.redirect("/minhas-doacoes"),
            ),
            rx.menu.item(
                rx.icon("user-pen", size=16, aria_hidden="true"),
                "Editar perfil",
                on_select=rx.redirect("/perfil/editar"),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("log-out", size=16, aria_hidden="true"),
                "Sair",
                on_select=LoginState.logout,
            ),
            align="end",
        ),
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
                            *[_nav_link(label, href) for label, href in NAV_LINKS],
                            # 12 px entre 992 e 1279 px (menos espaço) e
                            # 32 px a partir de 1280 px.
                            spacing=rx.breakpoints(initial="3", lg="6"),
                        )
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.cond(
                            LoginState.auth_token,
                            # A entrada no chat é o botão flutuante
                            # (chat_fab), não um item do cabeçalho.
                            account_menu(),
                            rx.button(
                                "Entrar",
                                variant="outline",
                                color="#168447",
                                border_color="#168447",
                                size="2",
                                on_click=rx.redirect("/login"),
                            ),
                        ),
                        rx.link(
                            "Quero Doar",
                            href="/cadastro-doacao",
                            background="#168447",
                            color="white",
                            padding="8px 16px",
                            border_radius="6px",
                            font_size="14px",
                            font_weight="500",
                            white_space="nowrap",
                            display="inline-flex",
                            align_items="center",
                            min_height="44px",
                            _hover={"background": "#126f3b"},
                            _focus_visible=FOCUS_RING,
                        ),
                        spacing=rx.breakpoints(initial="2", sm="3"),
                        align="center",
                    ),
                    align="center",
                    width="100%",
                    max_width=HEADER_MAX_WIDTH,
                    margin="0 auto",
                    padding=rx.breakpoints(initial="12px 16px", md="12px 24px"),
                ),
                width="100%",
                background="white",
            ),
            rx.vstack(
                rx.vstack(
                    # Figma (nó 615:2345): LINE Seed JP Bold 36 px, altura de
                    # linha normal (~40 px), #2A2A2A, centralizado, 1376 px de
                    # largura no quadro de 1512 px, quebrando em
                    # “…recomeço para” / “alguém.”. Abaixo disso, a fonte
                    # diminui com a largura (2,4vw) até 24 px.
                    rx.heading(
                        "Doar é fácil.",
                        " No DoaFácil, o que sobra em você vira recomeço para alguém.",
                        class_name="home-hero-title",
                        font_family="'LINE Seed JP', Arial, sans-serif",
                        color=HERO_TITLE_COLOR,
                        text_align="center",
                        font_weight="700",
                        line_height="normal",
                        width=f"min({HERO_TITLE_WIDTH}, 100%)",
                        white_space="normal",
                        overflow_wrap="break-word",
                        font_size=HERO_TITLE_FONT_SIZE,
                    ),
                    align="center",
                    justify="center",
                    width="100%",
                    padding_x="16px",
                    box_sizing="border-box",
                    padding_top="3rem",
                    padding_bottom="2.5rem",
                    class_name="page-fade-enter",
                ),
                rx.hstack(
                    donation_count_view(),
                    recent_donations_view(),
                    # Números centralizados na altura dos cartões das
                    # recentes (pedido do grupo; no Figma ficam no topo).
                    align="center",
                    spacing="6",
                    width="100%",
                    # Mesmas bordas do conteúdo do cabeçalho.
                    max_width=HEADER_MAX_WIDTH,
                    padding_x=HEADER_PADDING_X,
                    box_sizing="border-box",
                    style={
                        "flexDirection": rx.breakpoints(
                            initial="column", md="row"
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
                class_name="page-fade-enter",
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
        chat_fab(),
        display="flex",
        flex_direction="column",
        width="100%",
        min_height="100vh",
        background="#FFF6E8",
        font_family="'LINE Seed JP', Arial, sans-serif",
    )


# Campos de texto legíveis em todo o site, em qualquer tema do sistema: o
# texto digitado ou colado fica #1F1F1F opaco, e o texto de exemplo #6B6B6B.
# O Radix pinta o <input> e o <textarea> pela classe (.rt-TextFieldInput,
# .rt-TextAreaInput), que vence um seletor só de elemento; por isso o
# !important. O placeholder herda o -webkit-text-fill-color do campo, que
# vence o color, então a cor dele também vai no -webkit-text-fill-color.
# Exceções: campos desativados (como o do chat somente leitura) mantêm o
# visual de desativado do Radix, e o <input type="file"> escondido do upload,
# hidden, checkbox e radio ficam de fora.
FIELD_TEXT_SELECTOR = (
    "input:not([type='file']):not([type='hidden']):not([type='checkbox'])"
    ":not([type='radio']):not(:disabled), "
    "textarea:not(:disabled)"
)
FIELD_PLACEHOLDER_SELECTOR = "input::placeholder, textarea::placeholder"
FIELD_TEXT_COLOR = "#1F1F1F"
FIELD_PLACEHOLDER_COLOR = "#6B6B6B"

app = rx.App(
    style={
        FIELD_TEXT_SELECTOR: {
            "color": f"{FIELD_TEXT_COLOR} !important",
            "WebkitTextFillColor": f"{FIELD_TEXT_COLOR} !important",
            "opacity": "1 !important",
        },
        FIELD_PLACEHOLDER_SELECTOR: {
            "color": f"{FIELD_PLACEHOLDER_COLOR} !important",
            "WebkitTextFillColor": f"{FIELD_PLACEHOLDER_COLOR} !important",
            "opacity": "1 !important",
        },
        (
            "#donation-category, "
            "#donation-condition, "
            "#donation-delivery-method, "
            "#donation-contact-preference"
        ): {
            "color": "#333333",
        },
        (
            "#donation-category[data-placeholder] .rt-SelectTriggerInner, "
            "#donation-condition[data-placeholder] .rt-SelectTriggerInner, "
            "#donation-delivery-method[data-placeholder] "
            ".rt-SelectTriggerInner, "
            "#donation-contact-preference[data-placeholder] "
            ".rt-SelectTriggerInner"
        ): {
            "color": "#333333",
        },
        (
            "#login-email:-webkit-autofill, "
            "#login-email:-webkit-autofill:hover, "
            "#login-email:-webkit-autofill:focus, "
            "#login-password:-webkit-autofill, "
            "#login-password:-webkit-autofill:hover, "
            "#login-password:-webkit-autofill:focus, "
            "#signup-name:-webkit-autofill, "
            "#signup-name:-webkit-autofill:hover, "
            "#signup-name:-webkit-autofill:focus, "
            "#signup-email:-webkit-autofill, "
            "#signup-email:-webkit-autofill:hover, "
            "#signup-email:-webkit-autofill:focus, "
            "#signup-city:-webkit-autofill, "
            "#signup-city:-webkit-autofill:hover, "
            "#signup-city:-webkit-autofill:focus, "
            "#signup-password:-webkit-autofill, "
            "#signup-password:-webkit-autofill:hover, "
            "#signup-password:-webkit-autofill:focus, "
            "#signup-confirm-password:-webkit-autofill, "
            "#signup-confirm-password:-webkit-autofill:hover, "
            "#signup-confirm-password:-webkit-autofill:focus, "
            "#recovery-email:-webkit-autofill, "
            "#recovery-email:-webkit-autofill:hover, "
            "#recovery-email:-webkit-autofill:focus, "
            "#recovery-code:-webkit-autofill, "
            "#recovery-code:-webkit-autofill:hover, "
            "#recovery-code:-webkit-autofill:focus, "
            "#recovery-password:-webkit-autofill, "
            "#recovery-password:-webkit-autofill:hover, "
            "#recovery-password:-webkit-autofill:focus, "
            "#recovery-password-confirmation:-webkit-autofill, "
            "#recovery-password-confirmation:-webkit-autofill:hover, "
            "#recovery-password-confirmation:-webkit-autofill:focus"
        ): {
            # A cor do texto vem da regra global dos campos.
            "background_color": "white",
            "box_shadow": "0 0 0 1000px white inset",
        },
        ".recent-donations-carousel::-webkit-scrollbar": {
            "height": "6px",
        },
        ".recent-donations-carousel::-webkit-scrollbar-thumb": {
            "background_color": "#B8C8BC",
            "border_radius": "999px",
        },
        ".recent-donations-carousel::-webkit-scrollbar-track": {
            "background_color": "transparent",
        },
    },
    stylesheets=[
        "/auth-card.css",
        "/chat.css",
        "https://fonts.googleapis.com/css2?family=LINE+Seed+JP:wght@400;700&display=swap"
    ]
)
app.add_page(
    index,
    on_load=[
        HomeState.load_home_data,
        LoginState.load_account,
        ChatState.load_unread_total,
    ],
)
app.add_page(
    login_page,
    route="/login",
    on_load=LoginState.consume_password_reset_notice,
)
app.add_page(signup_page, route="/cadastro")
app.add_page(request_recovery_page, route="/recuperar-senha")
app.add_page(
    verify_recovery_page,
    route="/verificar-email",
    on_load=LoginState.require_verification_email,
)
app.add_page(
    new_password_page,
    route="/nova-senha",
    on_load=LoginState.require_reset_token,
)
app.add_page(
    donation_creation_page,
    route="/cadastro-doacao",
    on_load=DonationCreateState.load_initial_data,
)
app.add_page(
    donation_detail_page,
    route="/doacao/[id]",
    on_load=DonationDetailState.load_donation,
)
app.add_page(
    donor_profile_page,
    route="/doacao/[id]/quem-doa",
    on_load=DonorProfileState.load_profile,
)
app.add_page(
    my_donations_page,
    route="/minhas-doacoes",
    on_load=MyDonationsState.load_page,
)
app.add_page(
    edit_donation_page,
    route="/minhas-doacoes/[id]/editar",
    on_load=EditDonationState.load_edit,
)
app.add_page(
    edit_profile_page,
    route="/perfil/editar",
    on_load=EditProfileState.load_profile,
)
app.add_page(
    chat_page,
    route="/chat",
    on_load=ChatState.load_chat,
)
# Explorar doações: por enquanto, a página provisória da change landing-nova.
app.add_page(
    explore_page,
    route=EXPLORE_ROUTE,
    title="Explorar doações | DoaFácil",
    on_load=ExploreState.load_filters,
)
