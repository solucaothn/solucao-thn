"""Shared header for the demonstrative fundraising pages."""

import reflex as rx

from ..state import CampaignState
from ..theme import BORDER, GOLD, NAVY, PAGE, TEXT, WHITE


def header() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.link(
                rx.hstack(
                    rx.box(
                        "♥",
                        color="#D4AF37",
                        font_size="24px",
                        font_weight="900",
                    ),
                    rx.text(
                        "DoaFácil",
                        color=WHITE,
                        font_size="22px",
                        font_weight="800",
                    ),
                    spacing="2",
                    align="center",
                ),
                href="/",
                text_decoration="none",
            ),
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Buscar vaquinhas",
                        value=CampaignState.search_text,
                        on_change=CampaignState.set_search_text,
                        aria_label="Buscar campanhas pelo título",
                        background=PAGE,
                        color=TEXT,
                        border=f"1px solid {BORDER}",
                        border_radius="10px",
                    ),
                    rx.select(
                        CampaignState.categories,
                        value=CampaignState.selected_category,
                        on_change=CampaignState.set_category,
                        aria_label="Filtrar por categoria",
                        style={
                            "background": WHITE,
                            "color": TEXT,
                            "border": f"1px solid {BORDER}",
                        },
                    ),
                    rx.button(
                        "Buscar",
                        type_="submit",
                        background="#D4AF37",
                        color=NAVY,
                        _hover={"background": "#C59B27"},
                    ),
                    spacing="2",
                    width="100%",
                ),
                on_submit=CampaignState.open_feed,
                width="min(100%, 620px)",
            ),
            rx.hstack(
                rx.link(
                    rx.button(
                        "Criar Doação",
                        background=GOLD,
                        color=NAVY,
                        font_weight="700",
                        _hover={"background": "#C59B27"},
                    ),
                    href="/app#catalogo-criar-doacao",
                ),
                rx.link(
                    rx.button(
                        "Entrar",
                        variant="outline",
                        color=WHITE,
                        border_color=WHITE,
                    ),
                    href="/app#login",
                ),
                spacing="2",
                align="center",
            ),
            justify="between",
            align="center",
            spacing="4",
            width="100%",
            max_width="1280px",
            margin="0 auto",
            padding="14px 24px",
            flex_wrap="wrap",
        ),
        position="sticky",
        top="0",
        z_index="100",
        width="100%",
        background=NAVY,
        border_bottom=f"1px solid {NAVY}",
        box_shadow="0 4px 14px rgba(15, 44, 89, 0.15)",
    )
