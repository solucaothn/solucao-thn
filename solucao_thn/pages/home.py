"""Demonstrative fundraising campaign feed."""

import reflex as rx

from ..components.header import header
from ..state import Campaign, CampaignState
from ..theme import (
    CARD_STYLE,
    GOLD,
    GOLD_HOVER,
    MUTED,
    NAVY,
    PAGE,
    WHITE,
)


def category_chip(category: str) -> rx.Component:
    return rx.button(
        category,
        on_click=CampaignState.set_category(category),
        variant="outline",
        color=rx.cond(CampaignState.selected_category == category, WHITE, NAVY),
        background=rx.cond(
            CampaignState.selected_category == category, NAVY, WHITE
        ),
        border=f"1px solid {NAVY}",
        border_radius="999px",
        _hover={"background": NAVY, "color": WHITE},
    )


def campaign_card(campaign: Campaign) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.box(
                rx.image(
                    src=campaign["image_path"],
                    alt="Ilustração demonstrativa da campanha",
                    width="100%",
                    height="180px",
                    object_fit="cover",
                    border_radius="12px",
                ),
                rx.badge(
                    "EXEMPLO",
                    position="absolute",
                    top="12px",
                    left="12px",
                    color=NAVY,
                    background=GOLD,
                ),
                position="relative",
                width="100%",
                border_radius="12px",
            ),
            rx.vstack(
                rx.badge(
                    campaign["category"],
                    style={
                        "background": PAGE,
                        "color": NAVY,
                        "border": "1px solid #E2E8F0",
                    },
                ),
                rx.heading(
                    campaign["title"],
                    size="4",
                    color=NAVY,
                    min_height="56px",
                ),
                rx.text(campaign["summary"], color=MUTED, min_height="48px"),
                rx.progress(
                    value=campaign["progress_percent"],
                    max=100,
                    style={"--accent-9": GOLD, "--accent-10": GOLD_HOVER},
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Arrecadado", color=MUTED),
                    rx.spacer(),
                    rx.text(
                        "R$ ",
                        campaign["raised_amount"],
                        " de R$ ",
                        campaign["goal_amount"],
                        color=NAVY,
                        font_weight="700",
                    ),
                    width="100%",
                ),
                rx.hstack(
                    rx.text(campaign["supporters"], " apoiadores", color=MUTED),
                    rx.spacer(),
                    rx.text(campaign["progress_percent"], "%", color=NAVY),
                    width="100%",
                ),
                rx.button(
                    "Conhecer vaquinha",
                    on_click=CampaignState.open_campaign(campaign["id"]),
                    width="100%",
                    background=NAVY,
                    color=WHITE,
                    _hover={"background": "#173B70"},
                ),
                spacing="3",
                width="100%",
            ),
            padding="4",
            align="stretch",
            spacing="4",
        ),
        style=CARD_STYLE,
        width="100%",
    )


def home_page() -> rx.Component:
    return rx.vstack(
        header(),
        rx.container(
            rx.vstack(
                rx.box(
                    rx.vstack(
                        rx.badge(
                            "CAMPANHAS DEMONSTRATIVAS",
                            background=GOLD,
                            color=NAVY,
                        ),
                        rx.heading(
                            "Juntos, podemos fazer a diferença",
                            size="8",
                            color=WHITE,
                            max_width="760px",
                        ),
                        rx.text(
                            "Explore histórias de exemplo e conheça como será "
                            "a experiência de apoiar uma causa.",
                            color=WHITE,
                            font_size="18px",
                            max_width="680px",
                        ),
                        rx.link(
                            rx.button(
                                "Explorar campanhas",
                                background=GOLD,
                                color=NAVY,
                                font_weight="700",
                                _hover={"background": GOLD_HOVER},
                            ),
                            href="#campanhas",
                        ),
                        align="start",
                        spacing="5",
                        padding="48px",
                    ),
                    background=NAVY,
                    border_radius="20px",
                    width="100%",
                ),
                rx.callout(
                    "Conteúdo e valores fictícios para demonstração. "
                    "Esta interface não recebe nem processa pagamentos.",
                    icon="info",
                    style={
                        "background": WHITE,
                        "color": NAVY,
                        "border": "1px solid #0F2C59",
                    },
                    width="100%",
                ),
                rx.vstack(
                    rx.heading("Encontre uma causa", size="6", color=NAVY),
                    rx.hstack(
                        rx.foreach(CampaignState.categories, category_chip),
                        spacing="2",
                        wrap="wrap",
                    ),
                    width="100%",
                    align="start",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.heading(
                            "Vaquinhas em destaque",
                            size="6",
                            color=NAVY,
                            id="campanhas",
                        ),
                        rx.spacer(),
                        rx.text(
                            CampaignState.filtered_campaigns.length(),
                            " exemplos",
                            color=MUTED,
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.grid(
                        rx.foreach(
                            CampaignState.filtered_campaigns, campaign_card
                        ),
                        width="100%",
                        spacing="5",
                        style={
                            "grid_template_columns": (
                                "repeat(auto-fit, minmax(min(100%, 290px), 1fr))"
                            )
                        },
                    ),
                    rx.cond(
                        CampaignState.filtered_campaigns.length() == 0,
                        rx.text(
                            "Nenhuma campanha demonstrativa corresponde à busca.",
                            color=MUTED,
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    align="start",
                ),
                spacing="7",
                width="100%",
                max_width="1280px",
                margin="0 auto",
                padding_y="8",
                padding_x="4",
            ),
            width="100%",
        ),
        width="100%",
        min_height="100vh",
        background=PAGE,
        spacing="0",
    )
