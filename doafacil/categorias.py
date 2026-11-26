"""Categorias (change explorar-categorias, spec donation-categories).

- A gaveta “Categorias”, aberta pelo menu da home (Figma 474:1650). É um
  rx.dialog posicionado à esquerda: o Dialog do Radix prende o foco, fecha com
  Esc e com clique fora e devolve o foco ao gatilho. O rx.drawer (Vaul) usa o
  mesmo Dialog, mas acrescenta arrastar e deslizar, que aqui não servem.
- A página /categorias, com a mesma lista, para links diretos e para o
  celular (onde o menu da home não aparece).

Cada categoria leva a /explorar?categoria=<id>.
"""

from __future__ import annotations

from typing import Any

import httpx
import reflex as rx

from doafacil.cabecalho import FOCUS_RING, HEADER_MAX_WIDTH, HEADER_PADDING_X
from doafacil.cadastro_doacao import DonationServiceError
from doafacil.chat import CHAT_FAB_CLEARANCE, chat_fab
from doafacil.explorar import (
    CATEGORY_ICONS,
    CREAM,
    DEFAULT_CATEGORY_ICON,
    EXPLORE_ROUTE,
    GREEN,
    TEXT_DARK,
    TEXT_MUTED,
    back_home_link,
    explore_header,
    fetch_categories,
)

CATEGORIES_TITLE = "Categorias"
CATEGORIES_ERROR_TEXT = "Não foi possível carregar as categorias."
DRAWER_WIDTH = "min(500px, 100vw)"
CATEGORY_ICON_COLOR = "#168447"


def _category_icon(icon: rx.Var) -> rx.Component:
    """Ícone pelo nome guardado em `icon` (o rx.icon precisa de nome fixo)."""
    cases = [
        (name, rx.icon(name, size=20, color=CATEGORY_ICON_COLOR, aria_hidden="true"))
        for name in sorted(set(CATEGORY_ICONS.values()))
    ]
    return rx.match(
        icon,
        *cases,
        rx.icon(DEFAULT_CATEGORY_ICON, size=20, color=CATEGORY_ICON_COLOR, aria_hidden="true"),
    )


def category_link(category: rx.Var[dict[str, Any]], on_click: Any = None) -> rx.Component:
    """Uma categoria: ícone, nome e seta, levando à Explorar filtrada."""
    extra = {"on_click": on_click} if on_click is not None else {}
    return rx.link(
        rx.flex(
            _category_icon(category["icon"]),
            rx.text(category["name"], color=TEXT_DARK, font_weight="700", font_size="1.05rem"),
            align="center",
            gap="12px",
            min_width="0",
        ),
        rx.icon("chevron-right", size=18, color="#555555", aria_hidden="true"),
        href=EXPLORE_ROUTE + "?categoria=" + category["id"].to(str),
        class_name="category-link",
        display="flex",
        align_items="center",
        justify_content="space-between",
        gap="12px",
        width="100%",
        min_height="56px",
        padding="8px 16px",
        border_radius="8px",
        underline="none",
        _hover={"background": "#F2F7F3"},
        _focus_visible=FOCUS_RING,
        **extra,
    )


def category_list(
    categories: rx.Var[list[dict[str, Any]]],
    loading: rx.Var | bool = False,
    on_choose: Any = None,
    on_retry: Any = None,
) -> rx.Component:
    """A lista de categorias, com carregando e falha (sem categorias
    fictícias). Lista vazia vale como falha: o backend sempre tem
    categorias. Na falha, “Tentar de novo” (`on_retry`) busca outra vez
    (change navegacao-celular)."""
    retry = (
        [
            rx.button(
                rx.icon("rotate-cw", size=16, aria_hidden="true"),
                "Tentar de novo",
                on_click=on_retry,
                class_name="category-retry",
                variant="outline",
                color=GREEN,
                border_color=GREEN,
                min_height="44px",
                cursor="pointer",
                _focus_visible=FOCUS_RING,
            )
        ]
        if on_retry is not None
        else []
    )
    return rx.cond(
        loading,
        rx.text("Carregando categorias...", color=TEXT_MUTED, role="status"),
        rx.cond(
            categories.length() > 0,
            rx.el.ul(
                rx.foreach(
                    categories,
                    lambda category: rx.el.li(category_link(category, on_choose), list_style="none"),
                ),
                class_name="category-list",
                display="flex",
                flex_direction="column",
                gap="4px",
                margin="0",
                padding="0",
                width="100%",
            ),
            rx.vstack(
                rx.text(CATEGORIES_ERROR_TEXT, color="#9B2C2C", role="status"),
                *retry,
                rx.link(
                    "Explorar doações",
                    href=EXPLORE_ROUTE,
                    color=GREEN,
                    font_weight="700",
                    min_height="44px",
                    display="inline-flex",
                    align_items="center",
                    _focus_visible=FOCUS_RING,
                ),
                align="start",
                spacing="1",
            ),
        ),
    )


class CategoriesState(rx.State):
    categories: list[dict[str, str]] = []
    loading: bool = True
    drawer_open: bool = False

    @rx.event
    async def load_categories(self) -> None:
        self.loading = True
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                self.categories = await fetch_categories(client)
        except (httpx.HTTPError, ValueError, DonationServiceError):
            self.categories = []
        self.loading = False

    @rx.event
    def retry_categories(self):
        """“Tentar de novo” da /categorias (change correcoes-revisao): mostra
        “Carregando categorias...” na hora e busca outra vez, com o mesmo
        pedido do load_categories."""
        self.loading = True
        return CategoriesState.load_categories

    @rx.event
    def set_drawer_open(self, is_open: bool) -> None:
        self.drawer_open = bool(is_open)

    @rx.event
    def close_drawer(self) -> None:
        self.drawer_open = False


def categories_drawer(
    categories: rx.Var[list[dict[str, Any]]],
    trigger: rx.Component,
    on_retry: Any = None,
    loading: rx.Var | bool = False,
) -> rx.Component:
    """Gaveta à esquerda (Figma 474:1650): título, “Fechar” (X) e a lista.
    Escolher uma categoria fecha a gaveta e abre a Explorar filtrada. Com
    `loading`, mostra “Carregando categorias...” (o “Tentar de novo” da
    gaveta, change correcoes-revisao)."""
    return rx.dialog.root(
        rx.dialog.trigger(trigger),
        rx.dialog.content(
            rx.flex(
                rx.dialog.title(
                    CATEGORIES_TITLE,
                    color=TEXT_DARK,
                    font_size="1.25rem",
                    font_weight="700",
                    margin="0",
                ),
                rx.dialog.close(
                    rx.button(
                        rx.icon("x", size=22, aria_hidden="true"),
                        aria_label="Fechar",
                        variant="ghost",
                        color="#333333",
                        min_width="44px",
                        min_height="44px",
                        _focus_visible=FOCUS_RING,
                    ),
                ),
                justify="between",
                align="center",
                padding="20px 16px 16px 20px",
                border_bottom="1px solid #D9D9D9",
            ),
            rx.dialog.description(
                "Escolha uma categoria para ver as doações dela.",
                class_name="sr-only",
                style={
                    "position": "absolute",
                    "width": "1px",
                    "height": "1px",
                    "overflow": "hidden",
                    "clip": "rect(0 0 0 0)",
                    "whiteSpace": "nowrap",
                },
            ),
            rx.box(
                category_list(categories, loading, on_choose=CategoriesState.close_drawer, on_retry=on_retry),
                padding="12px 8px",
                overflow_y="auto",
                flex="1",
            ),
            class_name="categories-drawer",
            # Painel lateral: preso à esquerda, na altura toda da tela.
            position="fixed",
            top="0",
            left="0",
            bottom="0",
            width=DRAWER_WIDTH,
            max_width=DRAWER_WIDTH,
            height="100dvh",
            max_height="100dvh",
            margin="0",
            padding="0",
            border_radius="0",
            display="flex",
            flex_direction="column",
            background="white",
            transform="none",
            box_shadow="4px 0 24px rgba(0, 0, 0, 0.12)",
        ),
        open=CategoriesState.drawer_open,
        on_open_change=CategoriesState.set_drawer_open,
    )


def categories_page() -> rx.Component:
    """A página /categorias, com a mesma lista da gaveta."""
    return rx.box(
        explore_header(),
        rx.box(
            rx.box(
                back_home_link(),
                rx.heading(CATEGORIES_TITLE, as_="h1", color=TEXT_DARK, font_weight="700", font_size="1.75rem"),
                display="flex",
                flex_direction="column",
                align_items="start",
                gap="8px",
                class_name="page-fade-enter",
            ),
            rx.box(
                category_list(
                    CategoriesState.categories,
                    CategoriesState.loading,
                    # Mostra o carregando na hora (change correcoes-revisao).
                    on_retry=CategoriesState.retry_categories,
                ),
                width="100%",
                max_width="560px",
                background="white",
                border="1px solid #E3E0DA",
                border_radius="12px",
                padding="8px",
            ),
            display="flex",
            flex_direction="column",
            gap="20px",
            width="100%",
            max_width=HEADER_MAX_WIDTH,
            margin="0 auto",
            padding_x=HEADER_PADDING_X,
            padding_top="16px",
            padding_bottom=CHAT_FAB_CLEARANCE,
            box_sizing="border-box",
        ),
        chat_fab(),
        width="100%",
        min_height="100vh",
        background=CREAM,
        font_family="'LINE Seed JP', Arial, sans-serif",
    )
