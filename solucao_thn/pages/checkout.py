"""Non-transactional demonstration checkout page."""

import reflex as rx

from ..components.header import header
from ..state import Campaign, CampaignState
from ..theme import BORDER, CARD_STYLE, GOLD, GOLD_HOVER, MUTED, NAVY, PAGE, TEXT, WHITE


def amount_button(amount: int) -> rx.Component:
    return rx.button(
        f"R$ {amount}",
        on_click=CampaignState.select_amount(amount),
        width="100%",
        color=rx.cond(
            (CampaignState.selected_amount == amount)
            & ~CampaignState.use_custom_amount,
            NAVY,
            TEXT,
        ),
        background=rx.cond(
            (CampaignState.selected_amount == amount)
            & ~CampaignState.use_custom_amount,
            GOLD,
            WHITE,
        ),
        border=f"1px solid {BORDER}",
        _hover={"border_color": GOLD},
    )


def checkout_content(campaign: Campaign) -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.link(
                "← Voltar à campanha",
                on_click=CampaignState.return_to_campaign,
                color=NAVY,
            ),
            rx.callout(
                "Checkout demonstrativo: não informe dados de cartão ou "
                "credenciais de pagamento. Nenhuma cobrança será feita.",
                icon="info",
                style={
                    "background": WHITE,
                    "color": NAVY,
                    "border": "1px solid #0F2C59",
                },
                width="100%",
            ),
            rx.grid(
                rx.card(
                    rx.vstack(
                        rx.heading("Escolha como apoiar", size="6", color=NAVY),
                        rx.text(campaign["title"], color=TEXT, font_weight="600"),
                        rx.text("Valor da contribuição", color=MUTED),
                        rx.grid(
                            amount_button(20),
                            amount_button(50),
                            amount_button(100),
                            columns="3",
                            spacing="3",
                            width="100%",
                        ),
                        rx.input(
                            placeholder="Outro valor (R$)",
                            type_="number",
                            min="1",
                            value=CampaignState.custom_amount,
                            on_change=CampaignState.set_custom_amount,
                            width="100%",
                            background=WHITE,
                            color=TEXT,
                            border=f"1px solid {BORDER}",
                        ),
                        rx.hstack(
                            rx.checkbox(
                                checked=CampaignState.is_anonymous,
                                on_change=CampaignState.toggle_anonymous,
                            ),
                            rx.text(
                                "Quero contribuir anonimamente (demonstração)",
                                color=TEXT,
                            ),
                            align="center",
                        ),
                        rx.text_area(
                            placeholder="Deixe uma mensagem de apoio (opcional)",
                            value=CampaignState.support_message,
                            on_change=CampaignState.set_support_message,
                            width="100%",
                            background=WHITE,
                            color=TEXT,
                            border=f"1px solid {BORDER}",
                        ),
                        rx.heading("Método de pagamento (visual)", size="4", color=NAVY),
                        rx.hstack(
                            rx.button(
                                "PIX",
                                on_click=CampaignState.select_payment_method("pix"),
                                variant=rx.cond(
                                    CampaignState.payment_method == "pix",
                                    "solid",
                                    "outline",
                                ),
                                background=rx.cond(
                                    CampaignState.payment_method == "pix",
                                    NAVY,
                                    WHITE,
                                ),
                                color=rx.cond(
                                    CampaignState.payment_method == "pix",
                                    WHITE,
                                    NAVY,
                                ),
                            ),
                            rx.button(
                                "Cartão",
                                on_click=CampaignState.select_payment_method("cartao"),
                                variant=rx.cond(
                                    CampaignState.payment_method == "cartao",
                                    "solid",
                                    "outline",
                                ),
                                background=rx.cond(
                                    CampaignState.payment_method == "cartao",
                                    NAVY,
                                    WHITE,
                                ),
                                color=rx.cond(
                                    CampaignState.payment_method == "cartao",
                                    WHITE,
                                    NAVY,
                                ),
                            ),
                            spacing="3",
                        ),
                        rx.cond(
                            CampaignState.payment_method == "pix",
                            rx.box(
                                rx.vstack(
                                    rx.text(
                                        "PIX com QR Code",
                                        color=NAVY,
                                        font_weight="700",
                                    ),
                                    rx.text(
                                        "Prévia indisponível até a integração "
                                        "de um provedor. Nenhum código real "
                                        "será gerado.",
                                        color=MUTED,
                                        text_align="center",
                                    ),
                                    align="center",
                                    spacing="2",
                                ),
                                background=PAGE,
                                border=f"1px dashed {BORDER}",
                                border_radius="12px",
                                padding="5",
                                width="100%",
                            ),
                            rx.text(
                                "A integração de cartão ainda não está disponível. "
                                "Não informe dados de cartão.",
                                color=MUTED,
                            ),
                        ),
                        rx.button(
                            "Continuar (demonstração)",
                            on_click=CampaignState.prepare_demo_checkout,
                            background=GOLD,
                            color=NAVY,
                            font_weight="800",
                            width="100%",
                            _hover={"background": GOLD_HOVER},
                        ),
                        rx.cond(
                            CampaignState.checkout_notice != "",
                            rx.callout(
                                CampaignState.checkout_notice,
                                icon="info",
                            style={
                                "background": WHITE,
                                "color": NAVY,
                                "border": "1px solid #0F2C59",
                            },
                            role="status",
                            ),
                            rx.fragment(),
                        ),
                        align="stretch",
                        spacing="4",
                    ),
                    style=CARD_STYLE,
                    padding="6",
                ),
                rx.card(
                    rx.vstack(
                        rx.badge("CAMPANHA DE EXEMPLO", background=GOLD, color=NAVY),
                        rx.heading("Resumo", size="5", color=NAVY),
                        rx.text(campaign["title"], color=TEXT, font_weight="600"),
                        rx.divider(),
                        rx.hstack(
                            rx.text("Valor escolhido", color=MUTED),
                            rx.spacer(),
                            rx.text(
                                "R$ ",
                                CampaignState.checkout_amount_label,
                                color=NAVY,
                                font_weight="700",
                            ),
                            width="100%",
                        ),
                        rx.text(
                            "A arrecadação e o resumo são fictícios. "
                            "Nenhuma doação será registrada.",
                            color=MUTED,
                            font_size="14px",
                        ),
                        align="stretch",
                        spacing="4",
                    ),
                    style=CARD_STYLE,
                    padding="6",
                    height="fit-content",
                ),
                width="100%",
                spacing="5",
                align="start",
                style={
                    "grid_template_columns": (
                        "repeat(auto-fit, minmax(min(100%, 320px), 1fr))"
                    )
                },
            ),
            width="100%",
            max_width="1100px",
            margin="0 auto",
            padding_y="6",
            padding_x="4",
            align="stretch",
            spacing="5",
        ),
        width="100%",
    )


def checkout_page() -> rx.Component:
    return rx.vstack(
        header(),
        rx.cond(
            CampaignState.selected_campaign_id != "",
            checkout_content(CampaignState.current_campaign),
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
