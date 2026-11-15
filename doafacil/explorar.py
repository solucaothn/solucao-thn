"""Explorar doações (`/explorar`).

Change landing-nova: a rota e os parâmetros `q`, `categoria` e `uf`, com as
funções `build_explore_url` e `parse_explore_filters`.
Change explorar-categorias: a listagem real, pelo endpoint público
`catalog/donations/search` (12 por página, só disponíveis), com “Carregar
mais”, estado vazio, cabeçalho com busca e o botão flutuante do chat.
"""

from __future__ import annotations

import asyncio
import unicodedata
from typing import Any
from urllib.parse import urlencode

import httpx
import reflex as rx

from doafacil.cabecalho import (
    FOCUS_RING,
    HEADER_MAX_WIDTH,
    HEADER_PADDING,
    HEADER_PADDING_X,
    header_auth_controls,
)
from doafacil.cadastro_doacao import (
    CATALOG_API_ENV,
    DonationServiceError,
    _api_endpoint,
    _parse_categories,
)
from doafacil.cartoes_doacao import _parse_donations, donation_grid_card
from doafacil.chat import CHAT_FAB_CLEARANCE, chat_fab

EXPLORE_ROUTE = "/explorar"
CATEGORIES_ROUTE = "/categorias"
RECENT_DONATIONS_ANCHOR = "/#doacoes-recentes"
CATEGORIES_PATH = "/catalog/categories"
SEARCH_PATH = "/catalog/donations/search"
PER_PAGE = 12
# Valor das opções “Todas as …” nos seletores (o Radix não aceita valor vazio).
ALL_OPTION_VALUE = "todas"
ALL_CATEGORIES_LABEL = "Todas as categorias"
ALL_LOCATIONS_LABEL = "Todas as localizações"
BRAZILIAN_STATES = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
)
RECENT_TITLE = "Adicionadas recentemente"
EMPTY_TEXT = "Nenhuma doação encontrada"
LOAD_ERROR_TEXT = "Não foi possível carregar as doações."
LOAD_MORE_ERROR_TEXT = "Não foi possível carregar mais doações."
# Ícone de cada categoria, pelo nome em minúsculas e sem acento (os nomes
# vêm do Xano). Outros nomes usam o ícone genérico.
CATEGORY_ICONS = {
    "moveis": "house",
    "eletronicos": "smartphone",
    "brinquedos": "bike",
    "livros": "book-open",
    "roupas": "shirt",
}
DEFAULT_CATEGORY_ICON = "tag"
# Verde dos links sobre o creme: 6,1:1 (AA). O #168447 dá só 4,4:1 ali.
GREEN = "#166B3B"
CREAM = "#FFF6E8"
TEXT_DARK = "#1F1F1F"
TEXT_MUTED = "#555555"
ERROR_RED = "#9B2C2C"
GRID_COLUMNS = "repeat(auto-fill, minmax(min(100%, 220px), 1fr))"
# Logotipo do cabeçalho: o mesmo tamanho da home (100 px no celular e 190 px
# a partir de md), com 72 px de altura.
LOGO_WIDTH = rx.breakpoints(initial="100px", md="190px")
SEARCH_TEXT_COLOR = "#333333"
SEARCH_BACKGROUND = "#EFEFEF"


def _clean_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _valid_category(value: object) -> str:
    """Id de categoria como texto, só se for inteiro positivo."""
    text = _clean_text(value)
    if text.isdigit() and int(text) > 0:
        return str(int(text))
    return ""


def _valid_state(value: object) -> str:
    text = _clean_text(value).upper()
    return text if text in BRAZILIAN_STATES else ""


def build_explore_url(query: object, category: object, state: object) -> str:
    """`/explorar` com `q`, `categoria` e `uf`, só para os filtros escolhidos."""
    params: dict[str, str] = {}
    text = _clean_text(query)
    if text:
        params["q"] = text
    category_id = _valid_category(category)
    if category_id:
        params["categoria"] = category_id
    uf = _valid_state(state)
    if uf:
        params["uf"] = uf
    return f"{EXPLORE_ROUTE}?{urlencode(params)}" if params else EXPLORE_ROUTE


def parse_explore_filters(params: dict[str, Any]) -> dict[str, str]:
    """Filtros válidos da URL; um parâmetro inválido vira “não escolhido”."""
    return {
        "q": _clean_text(params.get("q")),
        "categoria": _valid_category(params.get("categoria")),
        "uf": _valid_state(params.get("uf")),
    }


def category_icon(name: object) -> str:
    """Ícone Lucide de uma categoria, pelo nome sem acento e em minúsculas."""
    if not isinstance(name, str):
        return DEFAULT_CATEGORY_ICON
    plain = unicodedata.normalize("NFKD", name.strip().casefold())
    plain = "".join(char for char in plain if not unicodedata.combining(char))
    return CATEGORY_ICONS.get(plain, DEFAULT_CATEGORY_ICON)


async def fetch_categories(client: httpx.AsyncClient) -> list[dict[str, str]]:
    """Categorias do backend como `{id, name, icon}` em texto (os seletores
    usam id e nome; a lista de categorias usa também o ícone)."""
    response = await client.get(_api_endpoint(CATALOG_API_ENV, CATEGORIES_PATH))
    response.raise_for_status()
    return [
        {
            "id": str(category["id"]),
            "name": category["name"],
            "icon": category_icon(category["name"]),
        }
        for category in _parse_categories(response.json())
    ]


def _valid_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


async def fetch_search_page(
    client: httpx.AsyncClient, filters: dict[str, str], page: int
) -> dict[str, Any]:
    """Uma página da busca pública: `{items, total, page_total}`. Só os
    filtros escolhidos vão na consulta."""
    params: dict[str, Any] = {"page": page}
    if filters.get("q"):
        params["q"] = filters["q"]
    if filters.get("categoria"):
        params["category_id"] = filters["categoria"]
    if filters.get("uf"):
        params["state"] = filters["uf"]
    response = await client.get(_api_endpoint(CATALOG_API_ENV, SEARCH_PATH), params=params)
    response.raise_for_status()
    payload = response.json()
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("items"), list)
        or not _valid_count(payload.get("total"))
        or not _valid_count(payload.get("page_total"))
    ):
        raise ValueError("A resposta da busca é inválida.")
    return {
        "items": _parse_donations(payload["items"]),
        "total": payload["total"],
        "page_total": payload["page_total"],
    }


def explore_title(query: str, category_id: str, category_label: str, state: str) -> str:
    """Título da página conforme os filtros (spec donation-explore)."""
    parts = []
    if category_id:
        parts.append(f"Categoria “{category_label}”" if category_label else "Categoria")
    if query:
        parts.append(f"Resultados para “{query}”")
    title = " · ".join(parts) if parts else RECENT_TITLE
    return f"{title} em {state}" if state else title


class ExploreState(rx.State):
    search_text: str = ""
    category_id: str = ""
    category_label: str = ""
    state_label: str = ""
    items: list[dict[str, Any]] = []
    page: int = 0
    page_total: int = 0
    total: int = 0
    loading: bool = True
    loading_more: bool = False
    error: str = ""
    load_more_error: str = ""

    @rx.var
    def has_filters(self) -> bool:
        return bool(self.search_text or self.category_id or self.state_label)

    @rx.var
    def title(self) -> str:
        return explore_title(self.search_text, self.category_id, self.category_label, self.state_label)

    @rx.var
    def has_more(self) -> bool:
        return self.page < self.page_total

    @rx.var
    def result_text(self) -> str:
        if self.total == 1:
            return "1 doação encontrada"
        return f"{self.total} doações encontradas"

    @rx.var
    def state_select_value(self) -> str:
        return self.state_label or ALL_OPTION_VALUE

    @rx.var
    def remove_category_url(self) -> str:
        return build_explore_url(self.search_text, None, self.state_label)

    def _filters(self) -> dict[str, str]:
        return {"q": self.search_text, "categoria": self.category_id, "uf": self.state_label}

    @rx.event
    async def load_filters(self) -> None:
        # RouterData.url (a API nova; o router.page está obsoleto desde a 0.8.1).
        filters = parse_explore_filters(dict(self.router.url.query_parameters))
        self.search_text = filters["q"]
        self.category_id = filters["categoria"]
        self.state_label = filters["uf"]
        self.category_label = ""
        self.items = []
        self.page = 0
        self.page_total = 0
        self.total = 0
        self.error = ""
        self.load_more_error = ""
        self.loading = True
        yield

        async def categories_or_empty(client: httpx.AsyncClient) -> list[dict[str, str]]:
            if not filters["categoria"]:
                return []
            try:
                return await fetch_categories(client)
            except (httpx.HTTPError, ValueError, DonationServiceError):
                return []

        async def first_page(client: httpx.AsyncClient) -> dict[str, Any] | Exception:
            try:
                return await fetch_search_page(client, filters, 1)
            except (httpx.HTTPError, ValueError, DonationServiceError) as error:
                return error

        async with httpx.AsyncClient(timeout=15.0) as client:
            categories, result = await asyncio.gather(categories_or_empty(client), first_page(client))

        names = {category["id"]: category["name"] for category in categories}
        self.category_label = names.get(filters["categoria"], "")
        if isinstance(result, Exception):
            self.error = LOAD_ERROR_TEXT
        else:
            self.items = result["items"]
            self.total = result["total"]
            self.page_total = result["page_total"]
            self.page = 1
        self.loading = False

    @rx.event
    async def load_more(self) -> None:
        if self.loading or self.loading_more or self.page >= self.page_total:
            return
        self.loading_more = True
        self.load_more_error = ""
        yield
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                result = await fetch_search_page(client, self._filters(), self.page + 1)
        except (httpx.HTTPError, ValueError, DonationServiceError):
            self.load_more_error = LOAD_MORE_ERROR_TEXT
        else:
            known = {item["id"] for item in self.items}
            self.items = self.items + [item for item in result["items"] if item["id"] not in known]
            self.total = result["total"]
            self.page_total = result["page_total"]
            self.page += 1
        self.loading_more = False

    @rx.event
    def search(self, form_data: dict[str, Any]):
        """Busca do cabeçalho: novo `q` e `uf`, mantendo a categoria atual
        só na própria /explorar (na /categorias o estado pode ser antigo)."""
        on_explore = str(self.router.url.path).rstrip("/") == EXPLORE_ROUTE
        category = self.category_id if on_explore else None
        return rx.redirect(build_explore_url(form_data.get("q"), category, form_data.get("uf")))


def _text_link(label: str, href: str | rx.Var, **props: Any) -> rx.Component:
    return rx.link(
        label,
        href=href,
        color=GREEN,
        font_weight="700",
        display="inline-flex",
        align_items="center",
        gap="4px",
        min_height="44px",
        underline="hover",
        _focus_visible=FOCUS_RING,
        **props,
    )


def explore_header() -> rx.Component:
    """Cabeçalho da Explorar e da /categorias (Figma 438:1426): logotipo,
    busca com texto, UF e lupa, e os controles de conta. Em telas estreitas,
    a busca desce para uma linha própria."""
    return rx.box(
        rx.flex(
            rx.link(
                # O mesmo logotipo e tamanho da home.
                rx.image(
                    src="/logo.svg",
                    alt="DoaFácil — início",
                    style={"width": LOGO_WIDTH},
                    height="72px",
                    object_fit="contain",
                ),
                href="/",
                aria_label="DoaFácil — início",
                display="inline-flex",
                min_height="44px",
                align_items="center",
                _focus_visible=FOCUS_RING,
            ),
            rx.form(
                rx.flex(
                    rx.input(
                        name="q",
                        key=ExploreState.search_text,
                        default_value=ExploreState.search_text,
                        placeholder="Buscar",
                        aria_label="Buscar doações",
                        id="explore-search",
                        flex="1",
                        min_width="0",
                        size="3",
                        variant="soft",
                        color_scheme="gray",
                        radius="full",
                    ),
                    rx.select.root(
                        # Cinza escuro como o texto do campo: #333333 sobre o
                        # #EFEFEF da busca dá 11,3:1 (o azul do tema sumia).
                        rx.select.trigger(
                            aria_label="Localização",
                            variant="ghost",
                            color_scheme="gray",
                            color=SEARCH_TEXT_COLOR,
                            font_weight="700",
                            min_height="44px",
                        ),
                        rx.select.content(
                            rx.select.item("Todas", value=ALL_OPTION_VALUE),
                            *[rx.select.item(uf, value=uf) for uf in BRAZILIAN_STATES],
                        ),
                        name="uf",
                        key=ExploreState.state_select_value,
                        default_value=ExploreState.state_select_value,
                    ),
                    rx.button(
                        rx.icon("search", size=20, aria_hidden="true"),
                        type="submit",
                        aria_label="Buscar",
                        variant="ghost",
                        color="#333333",
                        min_width="44px",
                        min_height="44px",
                        _focus_visible=FOCUS_RING,
                    ),
                    align="center",
                    gap="8px",
                    width="100%",
                    padding="0 8px 0 4px",
                    background=SEARCH_BACKGROUND,
                    border_radius="999px",
                ),
                on_submit=ExploreState.search,
                reset_on_submit=False,
                class_name="explore-header-search",
                flex="1",
                min_width="0",
                max_width="620px",
                order=rx.breakpoints(initial="3", md="2"),
                style={"width": rx.breakpoints(initial="100%", md="auto")},
            ),
            rx.box(header_auth_controls(), order="2", margin_left="auto"),
            align="center",
            wrap="wrap",
            column_gap="24px",
            row_gap="8px",
            width="100%",
            max_width=HEADER_MAX_WIDTH,
            margin="0 auto",
            padding=HEADER_PADDING,
            box_sizing="border-box",
        ),
        width="100%",
        background="white",
    )


def back_home_link() -> rx.Component:
    return _text_link(
        "Voltar ao início",
        "/",
        class_name="explore-back-link",
    )


def _category_chip() -> rx.Component:
    """A categoria aplicada, removível (mantém `q` e `uf`)."""
    return rx.cond(
        ExploreState.category_id != "",
        rx.link(
            rx.text("Categoria: ", ExploreState.category_label, as_="span"),
            rx.icon("x", size=14, aria_hidden="true"),
            href=ExploreState.remove_category_url,
            aria_label="Remover o filtro de categoria",
            class_name="explore-category-chip",
            display="inline-flex",
            align_items="center",
            gap="6px",
            min_height="44px",
            padding="0 14px",
            border_radius="999px",
            background="#E8F5EC",
            color=GREEN,
            font_weight="700",
            underline="none",
            _focus_visible=FOCUS_RING,
        ),
        rx.fragment(),
    )


def _results() -> rx.Component:
    """Grade, “Carregar mais”, estado vazio e erros. Os cartões vêm do Xano
    e não animam."""
    return rx.cond(
        ExploreState.loading,
        rx.text("Carregando doações...", color=TEXT_MUTED, role="status"),
        rx.cond(
            ExploreState.error != "",
            rx.vstack(
                rx.text(ExploreState.error, color=ERROR_RED, role="status"),
                rx.button(
                    "Tentar de novo",
                    on_click=ExploreState.load_filters,
                    variant="outline",
                    color=GREEN,
                    min_height="44px",
                    _focus_visible=FOCUS_RING,
                ),
                align="start",
                spacing="3",
            ),
            rx.cond(
                ExploreState.items.length() == 0,
                rx.vstack(
                    rx.text(EMPTY_TEXT, color=TEXT_DARK, font_weight="700", role="status"),
                    rx.cond(
                        ExploreState.has_filters,
                        _text_link("Limpar filtros", EXPLORE_ROUTE, class_name="explore-clear-filters"),
                        rx.fragment(),
                    ),
                    align="start",
                    spacing="2",
                ),
                rx.vstack(
                    rx.text(ExploreState.result_text, color=TEXT_MUTED, role="status"),
                    rx.grid(
                        rx.foreach(ExploreState.items, donation_grid_card),
                        class_name="explore-grid",
                        width="100%",
                        gap="20px",
                        style={"gridTemplateColumns": GRID_COLUMNS},
                    ),
                    rx.cond(
                        ExploreState.load_more_error != "",
                        rx.text(ExploreState.load_more_error, color=ERROR_RED, role="status"),
                        rx.fragment(),
                    ),
                    rx.cond(
                        ExploreState.has_more,
                        rx.button(
                            rx.cond(ExploreState.loading_more, "Carregando...", "Carregar mais"),
                            on_click=ExploreState.load_more,
                            disabled=ExploreState.loading_more,
                            class_name="explore-load-more",
                            align_self="center",
                            background="#168447",
                            color="white",
                            min_height="44px",
                            padding="0 24px",
                            _focus_visible=FOCUS_RING,
                        ),
                        rx.fragment(),
                    ),
                    align="stretch",
                    spacing="4",
                    width="100%",
                ),
            ),
        ),
    )


def explore_page() -> rx.Component:
    """Explorar doações (Figma 438:1426 e 476:2478)."""
    return rx.box(
        explore_header(),
        rx.box(
            rx.box(
                back_home_link(),
                rx.flex(
                    rx.heading(
                        ExploreState.title,
                        as_="h1",
                        color=TEXT_DARK,
                        font_weight="400",
                        overflow_wrap="anywhere",
                        style={"fontSize": rx.breakpoints(initial="1.5rem", md="1.75rem")},
                    ),
                    _text_link("Ver categorias", CATEGORIES_ROUTE, class_name="explore-categories-link"),
                    justify="between",
                    align="center",
                    wrap="wrap",
                    column_gap="16px",
                    width="100%",
                ),
                _category_chip(),
                display="flex",
                flex_direction="column",
                align_items="start",
                gap="8px",
                class_name="page-fade-enter",
            ),
            _results(),
            display="flex",
            flex_direction="column",
            gap="20px",
            width="100%",
            max_width=HEADER_MAX_WIDTH,
            margin="0 auto",
            padding_x=HEADER_PADDING_X,
            padding_top="16px",
            # Espaço do botão flutuante: nenhum cartão fica sob ele.
            padding_bottom=CHAT_FAB_CLEARANCE,
            box_sizing="border-box",
        ),
        chat_fab(),
        width="100%",
        min_height="100vh",
        background=CREAM,
        font_family="'LINE Seed JP', Arial, sans-serif",
    )
