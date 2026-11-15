"""Explorar doações (`/explorar`), change landing-nova.

Por enquanto a página é provisória: recebe os filtros da busca da home
(`q`, `categoria` e `uf`), confirma o que chegou e avisa que a busca está em
construção. A listagem de resultados vem numa change seguinte, que reaproveita
a rota, os parâmetros e as funções `build_explore_url` e `parse_explore_filters`.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx
import reflex as rx

from doafacil.cadastro_doacao import (
    CATALOG_API_ENV,
    DonationServiceError,
    _api_endpoint,
    _parse_categories,
)

EXPLORE_ROUTE = "/explorar"
RECENT_DONATIONS_ANCHOR = "/#doacoes-recentes"
CATEGORIES_PATH = "/catalog/categories"
# Valor das opções “Todas as …” nos seletores (o Radix não aceita valor vazio).
ALL_OPTION_VALUE = "todas"
ALL_CATEGORIES_LABEL = "Todas as categorias"
ALL_LOCATIONS_LABEL = "Todas as localizações"
BRAZILIAN_STATES = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
)
UNDER_CONSTRUCTION_TEXT = (
    "A busca de doações ainda está em construção. "
    "Os filtros que você escolheu chegaram aqui e vão ser usados quando a lista ficar pronta."
)
NO_FILTERS_TEXT = "Nenhum filtro foi escolhido."
# Verde dos links sobre o creme: 6,1:1 (AA). O #168447 dá só 4,4:1 ali.
GREEN = "#166B3B"
TEXT_DARK = "#1F1F1F"
TEXT_MUTED = "#555555"


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


async def fetch_categories(client: httpx.AsyncClient) -> list[dict[str, str]]:
    """Categorias do backend como `{id, name}` em texto, para os seletores."""
    response = await client.get(_api_endpoint(CATALOG_API_ENV, CATEGORIES_PATH))
    response.raise_for_status()
    return [
        {"id": str(category["id"]), "name": category["name"]}
        for category in _parse_categories(response.json())
    ]


class ExploreState(rx.State):
    search_text: str = ""
    category_label: str = ""
    state_label: str = ""

    @rx.var
    def has_filters(self) -> bool:
        return bool(self.search_text or self.category_label or self.state_label)

    @rx.event
    async def load_filters(self) -> None:
        filters = parse_explore_filters(dict(self.router.page.params))
        self.search_text = filters["q"]
        self.state_label = filters["uf"]
        self.category_label = ""
        if not filters["categoria"]:
            return
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                categories = await fetch_categories(client)
        except (httpx.HTTPError, ValueError, DonationServiceError):
            categories = []
        names = {category["id"]: category["name"] for category in categories}
        self.category_label = names.get(filters["categoria"], ALL_CATEGORIES_LABEL)


def _filter_line(label: str, value: rx.Var) -> rx.Component:
    return rx.cond(
        value != "",
        rx.text(
            rx.text.strong(f"{label}: "),
            value,
            color=TEXT_DARK,
            overflow_wrap="anywhere",
        ),
        rx.fragment(),
    )


def explore_page() -> rx.Component:
    """Página provisória: título, aviso, resumo dos filtros e caminhos de volta."""
    return rx.box(
        rx.box(
            rx.link(
                rx.image(src="/logo.svg", alt="DoaFácil — início", width="140px", height="50px", object_fit="contain"),
                href="/",
                display="inline-flex",
                min_height="44px",
                align_items="center",
            ),
            width="100%",
            max_width="900px",
            margin="0 auto",
            padding="12px 16px",
        ),
        rx.box(
            rx.heading(
                "Explorar doações",
                as_="h1",
                color=TEXT_DARK,
                font_weight="700",
                style={"fontSize": rx.breakpoints(initial="1.75rem", md="2.25rem")},
            ),
            rx.text(UNDER_CONSTRUCTION_TEXT, color=TEXT_MUTED, line_height="1.5"),
            rx.box(
                rx.heading("Filtros recebidos", as_="h2", font_size="1.1rem", color=TEXT_DARK),
                rx.cond(
                    ExploreState.has_filters,
                    rx.vstack(
                        _filter_line("Busca", ExploreState.search_text),
                        _filter_line("Categoria", ExploreState.category_label),
                        _filter_line("Localização", ExploreState.state_label),
                        spacing="1",
                        align="start",
                    ),
                    rx.text(NO_FILTERS_TEXT, color=TEXT_MUTED),
                ),
                role="status",
                display="flex",
                flex_direction="column",
                gap="8px",
                padding="16px",
                background="white",
                border="1px solid #E3E0DA",
                border_radius="12px",
                width="100%",
            ),
            rx.flex(
                rx.link("Voltar ao início", href="/", class_name="explore-back-link", color=GREEN, font_weight="700", min_height="44px", display="inline-flex", align_items="center", text_decoration="underline"),
                rx.link("Ver doações recentes", href=RECENT_DONATIONS_ANCHOR, color=GREEN, font_weight="700", min_height="44px", display="inline-flex", align_items="center", text_decoration="underline"),
                wrap="wrap",
                column_gap="24px",
            ),
            display="flex",
            flex_direction="column",
            gap="20px",
            width="100%",
            max_width="900px",
            margin="0 auto",
            padding="24px 16px 64px",
            box_sizing="border-box",
            class_name="page-fade-enter",
        ),
        width="100%",
        min_height="100vh",
        background="#FFF6E8",
        font_family="'LINE Seed JP', Arial, sans-serif",
    )
