"""Demonstrative campaign detail page."""

import reflex as rx

from ..components.header import header
from ..state import Campaign, CampaignState
from ..theme import BORDER, CARD_STYLE, GOLD, MUTED, NAVY, PAGE, TEXT, WHITE


def donation_panel(campaign: Campaign) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.badge(
                "VALORES DEMONSTRATIVOS",
                background=GOLD,
                color=NAVY,
            ),
            rx.heading("Apoie esta causa", size="5", color=NAVY),
            rx.progress(
                value=campaign["progress_percent"],
                max=100,
                style={"--accent-9": GOLD, "--accent-10": "#C59B27"},
                width="100%",
            ),
            rx.text(
                "R$ ",
                campaign["raised_amount"],
                " arrecadados de R$ ",
                campaign["goal_amount"],
                color=NAVY,
                font_weight="700",
            ),
            rx.text(
                campaign["supporters"],
                " apoiadores de exemplo",
                color=MUTED,
            ),
            rx.button(
                "Doar Agora",
                on_click=CampaignState.open_checkout,
                background=GOLD,
                color=NAVY,
                font_weight="800",
                width="100%",
                _hover={"background": "#C59B27"},
            ),
            rx.text(
                "Nenhum pagamento será iniciado nesta demonstração.",
                color=MUTED,
                font_size="13px",
            ),
            align="stretch",
            spacing="4",
        ),
        style=CARD_STYLE,
        padding="5",
        width="100%",
    )


def campaign_content(campaign: Campaign) -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.link("← Voltar às vaquinhas", href="/vaquinhas", color=NAVY),
            rx.callout(
                "Campanha de exemplo. História, arrecadação e apoiadores são "
                "demonstrativos.",
                icon="info",
                style={
                    "background": WHITE,
                    "color": NAVY,
                    "border": "1px solid #0F2C59",
                },
                width="100%",
            ),
            rx.grid(
                rx.vstack(
                    rx.box(
                        rx.vstack(
                            rx.image(
                                src=campaign["image_path"],
                                alt="Ilustração demonstrativa da campanha",
                                width="100%",
                                height="340px",
                                object_fit="cover",
                                border_radius="16px",
                            ),
                            rx.text(
                                "Imagem ilustrativa da campanha",
                                color=WHITE,
                                position="absolute",
                                bottom="12px",
                                left="16px",
                                background="rgba(15, 44, 89, 0.82)",
                                padding="6px 10px",
                                border_radius="8px",
                            ),
                            align="center",
                            justify="center",
                            width="100%",
                        ),
                        position="relative",
                        border_radius="16px",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.avatar(
                            fallback=campaign["creator"][:1],
                            color=NAVY,
                            background=GOLD,
                        ),
                        rx.vstack(
                            rx.text(
                                campaign["creator"],
                                color=NAVY,
                                font_weight="700",
                            ),
                            rx.hstack(
                                rx.badge(
                                    "✓",
                                    background=GOLD,
                                    color=NAVY,
                                ),
                                rx.text("Criador verificado • exemplo", color=MUTED),
                                align="center",
                            ),
                            spacing="1",
                            align="start",
                        ),
                        align="center",
                        spacing="3",
                    ),
                    rx.heading(campaign["title"], size="7", color=NAVY),
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("História", value="historia"),
                            rx.tabs.trigger("Atualizações", value="atualizacoes"),
                            rx.tabs.trigger("Recados", value="recados"),
                        ),
                        rx.tabs.content(
                            rx.text(campaign["story"], color=TEXT, line_height="1.8"),
                            value="historia",
                        ),
                        rx.tabs.content(
                            rx.text(campaign["updates"], color=TEXT),
                            value="atualizacoes",
                        ),
                        rx.tabs.content(
                            rx.text(campaign["messages"], color=TEXT),
                            value="recados",
                        ),
                        default_value="historia",
                        width="100%",
                    ),
                    style={
                        "background": WHITE,
                        "border": f"1px solid {BORDER}",
                        "border_radius": "16px",
                        "padding": "24px",
                    },
                    align="stretch",
                    spacing="5",
                ),
                rx.box(
                    donation_panel(campaign),
                    position="sticky",
                    top="100px",
                    align_self="start",
                ),
                width="100%",
                spacing="6",
                align="start",
                style={
                    "grid_template_columns": (
                        "repeat(auto-fit, minmax(min(100%, 340px), 1fr))"
                    )
                },
            ),
            spacing="5",
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding_y="6",
            padding_x="4",
            align="stretch",
        ),
        width="100%",
    )


def campaign_page() -> rx.Component:
    return rx.vstack(
        header(),
        rx.cond(
            CampaignState.selected_campaign_id != "",
            campaign_content(CampaignState.current_campaign),
            rx.center(
                rx.vstack(
                    rx.heading("Campanha não encontrada", color=NAVY),
                    rx.link("Voltar às vaquinhas", href="/vaquinhas", color=NAVY),
                    align="center",
                    padding="12",
                ),
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        background=PAGE,
        spacing="0",
    )
