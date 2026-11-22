"""Página “não encontrada” própria, em português (change acabamento, spec
site-shell), no lugar do 404 padrão do Reflex, em inglês."""

from __future__ import annotations

import reflex as rx

from doafacil.cabecalho import FOCUS_RING, GREEN
from doafacil.navegacao import site_header

NOT_FOUND_TITLE = "Página não encontrada"
NOT_FOUND_TEXT = "O endereço pode ter mudado ou não existe mais."
CREAM = "#FFF6E8"
TEXT_DARK = "#1F1F1F"
TEXT_MUTED = "#555555"
EXPLORE_ROUTE = "/explorar"

_LINK = {
    "display": "inline-flex",
    "align_items": "center",
    "justify_content": "center",
    "min_height": "44px",
    "padding": "0 20px",
    "border_radius": "8px",
    "font_weight": "700",
    "underline": "none",
    "_focus_visible": FOCUS_RING,
}


def not_found_page() -> rx.Component:
    return rx.box(
        site_header(),
        rx.box(
            rx.vstack(
                rx.heading(NOT_FOUND_TITLE, as_="h1", color=TEXT_DARK, font_size="1.75rem", font_weight="700"),
                rx.text(NOT_FOUND_TEXT, color=TEXT_MUTED, font_size="1.05rem"),
                rx.flex(
                    rx.link(
                        "Voltar ao início",
                        href="/",
                        class_name="not-found-home",
                        background=GREEN,
                        color="white",
                        _hover={"background": "#126f3b", "color": "white"},
                        **_LINK,
                    ),
                    rx.link(
                        "Explorar doações",
                        href=EXPLORE_ROUTE,
                        class_name="not-found-explore",
                        color=GREEN,
                        border=f"1px solid {GREEN}",
                        background="white",
                        _hover={"background": "#F2F7F3", "color": GREEN},
                        **_LINK,
                    ),
                    gap="12px",
                    wrap="wrap",
                    justify="center",
                ),
                align="center",
                spacing="4",
                text_align="center",
                class_name="page-fade-enter",
                width="100%",
                max_width="560px",
                margin="0 auto",
            ),
            padding=rx.breakpoints(initial="48px 16px", md="96px 24px"),
            box_sizing="border-box",
            width="100%",
            flex="1",
        ),
        display="flex",
        flex_direction="column",
        min_height="100vh",
        background=CREAM,
    )
