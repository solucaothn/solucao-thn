"""Public institutional landing page."""

import reflex as rx

from ..state import CampaignState
from ..theme import (
    BORDER,
    CARD_STYLE,
    GOLD,
    GOLD_HOVER,
    MUTED,
    NAVY,
    PAGE,
    TEXT,
    WHITE,
)
from .home import campaign_card


def landing_header() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.link(
                rx.hstack(
                    rx.box(
                        "♥",
                        color=GOLD,
                        font_size="27px",
                        font_weight="900",
                    ),
                    rx.text(
                        "DoaFácil",
                        color=WHITE,
                        font_size="23px",
                        font_weight="800",
                    ),
                    spacing="2",
                    align="center",
                ),
                href="/",
                text_decoration="none",
            ),
            rx.hstack(
                rx.link("Doar", href="#causas", color=WHITE),
                rx.link("Arrecadar", href="/vaquinhas", color=WHITE),
                rx.link("Sobre", href="#sobre", color=WHITE),
                spacing="5",
                align="center",
            ),
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Buscar uma causa",
                        value=CampaignState.search_text,
                        on_change=CampaignState.set_search_text,
                        aria_label="Buscar campanhas demonstrativas",
                        background=WHITE,
                        color=TEXT,
                        border=f"1px solid {BORDER}",
                        border_radius="999px",
                        width="min(100%, 240px)",
                    ),
                    rx.link(
                        rx.button(
                            "Buscar",
                            type_="submit",
                            background=GOLD,
                            color=NAVY,
                            _hover={"background": GOLD_HOVER},
                        ),
                        href="#descobrir",
                    ),
                    spacing="2",
                    align="center",
                ),
                on_submit=CampaignState.scroll_to_results,
            ),
            rx.hstack(
                rx.link(
                    rx.button(
                        "Entrar",
                        variant="outline",
                        color=WHITE,
                        border_color=WHITE,
                    ),
                    href="/app#login",
                ),
                rx.link(
                    rx.button(
                        "Criar Campanha",
                        background=GOLD,
                        color=NAVY,
                        font_weight="700",
                        _hover={"background": GOLD_HOVER},
                    ),
                    href="/app#login",
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
            max_width="1280px",
            margin="0 auto",
            padding="16px 24px",
            align="center",
            justify="between",
            flex_wrap="wrap",
            spacing="4",
        ),
        position="sticky",
        top="0",
        z_index="100",
        background=NAVY,
        width="100%",
        box_shadow="0 4px 18px rgba(15, 44, 89, 0.16)",
    )


def hero_section() -> rx.Component:
    return rx.box(
        rx.grid(
            rx.vstack(
                rx.badge(
                    "SOLIDARIEDADE QUE APROXIMA",
                    background="rgba(212, 175, 55, 0.18)",
                    color=GOLD,
                    padding="8px 12px",
                    border_radius="999px",
                ),
                rx.heading(
                    "Pequenas atitudes. Grandes transformações.",
                    size="9",
                    color=WHITE,
                    line_height="1.05",
                    max_width="700px",
                ),
                rx.text(
                    "Encontre doações, apoie boas causas e faça parte de uma "
                    "comunidade que acredita no poder de ajudar.",
                    color="#E2E8F0",
                    font_size="19px",
                    line_height="1.7",
                    max_width="610px",
                ),
                rx.hstack(
                    rx.link(
                        rx.button(
                            "Encontrar doações",
                            background=GOLD,
                            color=NAVY,
                            font_weight="800",
                            size="3",
                            _hover={"background": GOLD_HOVER},
                        ),
                        href="#causas",
                    ),
                    rx.link(
                        rx.button(
                            "Quero arrecadar",
                            variant="outline",
                            color=WHITE,
                            border_color=WHITE,
                            size="3",
                        ),
                        href="/vaquinhas",
                    ),
                    spacing="3",
                    wrap="wrap",
                ),
                rx.text(
                    "Experiência pública • campanhas financeiras demonstrativas",
                    color="#CBD5E1",
                    font_size="13px",
                ),
                align="start",
                spacing="5",
            ),
            rx.box(
                rx.image(
                    src="/campaigns/community.svg",
                    alt="Ilustração conceitual de solidariedade comunitária",
                    width="100%",
                    height="340px",
                    object_fit="cover",
                    border_radius="24px",
                ),
                rx.badge(
                    "Ilustração demonstrativa",
                    position="absolute",
                    bottom="14px",
                    left="14px",
                    background=WHITE,
                    color=NAVY,
                ),
                position="relative",
                border=f"1px solid rgba(255, 255, 255, 0.2)",
                border_radius="24px",
                overflow="hidden",
                box_shadow="0 20px 50px rgba(0, 0, 0, 0.18)",
            ),
            width="100%",
            align="center",
            spacing="8",
            style={
                "grid_template_columns": (
                    "repeat(auto-fit, minmax(min(100%, 360px), 1fr))"
                )
            },
        ),
        background=(
            "radial-gradient(circle at 82% 15%, #244B7F 0%, "
            "#0F2C59 52%, #0A1F40 100%)"
        ),
        width="100%",
        padding_y="72px",
        padding_x="24px",
    )


def discovery_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.text(
                        "⌕",
                        color=NAVY,
                        font_size="32px",
                        font_weight="700",
                    ),
                    width="52px",
                    height="52px",
                    display="grid",
                    place_items="center",
                    border_radius="14px",
                    background="#FEF7DE",
                ),
                rx.vstack(
                    rx.heading("Encontre uma causa para apoiar", size="5", color=NAVY),
                    rx.text(
                        "Explore apenas campanhas de exemplo nesta demonstração.",
                        color=MUTED,
                    ),
                    spacing="1",
                    align="start",
                ),
                align="center",
                spacing="3",
            ),
            rx.form(
                rx.grid(
                    rx.input(
                        placeholder="Palavra-chave",
                        value=CampaignState.search_text,
                        on_change=CampaignState.set_search_text,
                        aria_label="Pesquisar por palavra-chave",
                        background=WHITE,
                        color=TEXT,
                        border=f"1px solid {BORDER}",
                        border_radius="10px",
                    ),
                    rx.select(
                        CampaignState.categories,
                        value=CampaignState.selected_category,
                        on_change=CampaignState.set_category,
                        aria_label="Selecionar categoria",
                        style={
                            "background": WHITE,
                            "color": TEXT,
                            "border": f"1px solid {BORDER}",
                            "border_radius": "10px",
                        },
                    ),
                    rx.input(
                        placeholder="Localidade de exemplo",
                        value=CampaignState.search_location,
                        on_change=CampaignState.set_search_location,
                        aria_label="Filtrar por localidade demonstrativa",
                        background=WHITE,
                        color=TEXT,
                        border=f"1px solid {BORDER}",
                        border_radius="10px",
                    ),
                    rx.button(
                        "Buscar causas",
                        type_="submit",
                        background=GOLD,
                        color=NAVY,
                        font_weight="700",
                        _hover={"background": GOLD_HOVER},
                    ),
                    width="100%",
                    spacing="3",
                    style={
                        "grid_template_columns": (
                            "repeat(auto-fit, minmax(min(100%, 190px), 1fr))"
                        )
                    },
                ),
                on_submit=CampaignState.scroll_to_results,
                width="100%",
            ),
            rx.hstack(
                rx.text(
                    "Exemplos disponíveis:",
                    color=MUTED,
                    font_size="13px",
                ),
                rx.foreach(
                    ["São Paulo", "Recife", "Belo Horizonte", "Curitiba"],
                    lambda location: rx.button(
                        location,
                        on_click=CampaignState.set_search_location(location),
                        variant="outline",
                        size="1",
                        color=NAVY,
                        border_color=BORDER,
                    ),
                ),
                spacing="2",
                wrap="wrap",
            ),
            align="stretch",
            spacing="4",
        ),
        width="calc(100% - 32px)",
        max_width="1120px",
        margin="-34px auto 0",
        position="relative",
        z_index="2",
        background=WHITE,
        border=f"1px solid {BORDER}",
        border_radius="20px",
        box_shadow="0 18px 44px rgba(15, 44, 89, 0.12)",
        padding="24px",
        id="descobrir",
    )


def trust_card(icon: str, title: str, description: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.box(
                rx.text(icon, color=NAVY, font_size="23px", font_weight="800"),
                background="#FEF7DE",
                border_radius="12px",
                width="48px",
                height="48px",
                display="grid",
                place_items="center",
            ),
            rx.heading(title, size="4", color=NAVY),
            rx.text(description, color=MUTED, line_height="1.65"),
            align="start",
            spacing="3",
        ),
        style=CARD_STYLE,
        padding="5",
        width="100%",
        height="100%",
    )


def trust_section() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.badge("CONFIANÇA E CUIDADO", color=NAVY, background="#FEF7DE"),
            rx.heading("Você está seguro no DoaFácil", size="7", color=NAVY),
            rx.text(
                "Conheça os princípios que orientam a experiência. As campanhas "
                "e números exibidos nesta landing são exemplos e não representam "
                "campanhas verificadas.",
                color=MUTED,
                max_width="760px",
                text_align="center",
                line_height="1.7",
            ),
            align="center",
            spacing="3",
        ),
        rx.grid(
            trust_card(
                "✓",
                "Regras no lugar certo",
                "As operações de conta e de propriedade de itens são validadas "
                "no backend, não apenas pela interface.",
            ),
            trust_card(
                "◉",
                "Transparência",
                "Valores, localidades e progresso desta página estão marcados "
                "como demonstrativos enquanto campanhas reais não são integradas.",
            ),
            trust_card(
                "♡",
                "Solidariedade",
                "A plataforma aproxima pessoas por meio de doações de itens e "
                "experiências de apoio a causas.",
            ),
            trust_card(
                "→",
                "Passos claros",
                "Explore as campanhas de exemplo ou acesse a aplicação para "
                "conhecer o catálogo de doações existente.",
            ),
            width="100%",
            spacing="4",
            style={
                "grid_template_columns": (
                    "repeat(auto-fit, minmax(min(100%, 235px), 1fr))"
                )
            },
        ),
        width="100%",
        max_width="1200px",
        margin="0 auto",
        padding="76px 24px",
        align="center",
        spacing="7",
        id="sobre",
    )


def featured_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.badge("CAUSES EM DESTAQUE", background="#FEF7DE", color=NAVY),
                    rx.heading("Toda ajuda começa com uma descoberta", size="7", color=NAVY),
                    rx.text(
                        "Campanhas ilustrativas para conhecer a experiência.",
                        color=MUTED,
                    ),
                    spacing="2",
                    align="start",
                ),
                rx.spacer(),
                rx.link(
                    rx.button(
                        "Ver todas",
                        variant="outline",
                        color=NAVY,
                        border_color=NAVY,
                    ),
                    href="/vaquinhas",
                ),
                width="100%",
                align="center",
                wrap="wrap",
            ),
            rx.text(
                "Destaques demonstrativos — valores e apoiadores são fictícios.",
                color=MUTED,
                font_size="14px",
            ),
            rx.grid(
                rx.foreach(CampaignState.filtered_campaigns, campaign_card),
                width="100%",
                spacing="5",
                style={
                    "grid_template_columns": (
                        "repeat(auto-fit, minmax(min(100%, 265px), 1fr))"
                    )
                },
            ),
            rx.cond(
                CampaignState.filtered_campaigns.length() == 0,
                rx.text(
                    "Nenhuma causa de exemplo corresponde aos filtros.",
                    color=MUTED,
                ),
                rx.fragment(),
            ),
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding="72px 24px",
            align="stretch",
            spacing="4",
        ),
        background=WHITE,
        width="100%",
        id="causas",
    )


def footer_link(label: str, href: str) -> rx.Component:
    return rx.link(label, href=href, color="#CBD5E1", _hover={"color": GOLD})


def institutional_footer() -> rx.Component:
    return rx.box(
        rx.grid(
            rx.vstack(
                rx.hstack(
                    rx.text("♥", color=GOLD, font_size="25px", font_weight="900"),
                    rx.text(
                        "DoaFácil",
                        color=WHITE,
                        font_size="22px",
                        font_weight="800",
                    ),
                    spacing="2",
                ),
                rx.text(
                    "Conectando generosidade a quem precisa.",
                    color="#CBD5E1",
                    max_width="320px",
                    line_height="1.7",
                ),
                rx.badge(
                    "Projeto em evolução • pagamentos não integrados",
                    background="rgba(212, 175, 55, 0.16)",
                    color=GOLD,
                    white_space="normal",
                ),
                align="start",
                spacing="3",
            ),
            rx.vstack(
                rx.heading("Explore", size="3", color=WHITE),
                footer_link("Encontrar doações", "/app#catalogo-criar-doacao"),
                footer_link("Arrecadar", "/vaquinhas"),
                footer_link("Criar campanha", "/app#login"),
                align="start",
                spacing="3",
            ),
            rx.vstack(
                rx.heading("Informações", size="3", color=WHITE),
                footer_link("Quem somos", "#sobre"),
                footer_link("Políticas", "#politicas"),
                footer_link("Dúvidas", "#duvidas"),
                align="start",
                spacing="3",
            ),
            rx.vstack(
                rx.heading("Contacto", size="3", color=WHITE),
                rx.text("Canal de contacto em breve.", color="#CBD5E1"),
                rx.text("Redes sociais em breve.", color="#CBD5E1"),
                align="start",
                spacing="3",
            ),
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding="56px 24px 36px",
            spacing="8",
            style={
                "grid_template_columns": (
                    "repeat(auto-fit, minmax(min(100%, 210px), 1fr))"
                )
            },
        ),
        rx.box(
            rx.vstack(
                rx.heading("Privacidade e políticas", size="3", color=WHITE),
                rx.text(
                    "Dados de contacto não são exibidos publicamente. As "
                    "campanhas mostradas nesta página são exemplos locais.",
                    color="#CBD5E1",
                    id="politicas",
                ),
                rx.heading("Dúvidas frequentes", size="3", color=WHITE, margin_top="3"),
                rx.text(
                    "Posso contribuir financeiramente agora? Ainda não: o "
                    "checkout e os pagamentos estão apenas em demonstração.",
                    color="#CBD5E1",
                    id="duvidas",
                ),
                align="start",
                spacing="2",
                width="100%",
                max_width="1200px",
                margin="0 auto",
                padding="0 24px 28px",
            ),
        ),
        background=NAVY,
        width="100%",
    )


def landing_page() -> rx.Component:
    return rx.vstack(
        landing_header(),
        hero_section(),
        discovery_section(),
        trust_section(),
        featured_section(),
        institutional_footer(),
        width="100%",
        min_height="100vh",
        background=PAGE,
        spacing="0",
    )
