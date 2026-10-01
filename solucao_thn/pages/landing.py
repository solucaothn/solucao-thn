"""Public institutional landing page."""

import reflex as rx

from ..state import CampaignState
from ..theme import BORDER, GOLD, GOLD_HOVER, MUTED, NAVY, PAGE, TEXT, WHITE

PRIMARY = {
    "dark": "#0F4D3A",
    "green": "#18A566",
    "light": "#E8F7EF",
    "yellow": "#F4B740",
    "cream": "#FFF9ED",
    "background": "#F8FAF8",
    "text": "#12352A",
    "muted": "#58786F",
}

CATEGORY_ITEMS = [
    {"name": "Roupas", "icon": "👕", "color": "#E8F7EF", "tag": "35 doações"},
    {"name": "Alimentos", "icon": "🥖", "color": "#FFF1D2", "tag": "24 doações"},
    {"name": "Móveis", "icon": "🪑", "color": "#EAF4FF", "tag": "18 doações"},
    {"name": "Livros", "icon": "📚", "color": "#FDE9D9", "tag": "22 doações"},
    {"name": "Eletrônicos", "icon": "💻", "color": "#E8F7EF", "tag": "16 doações"},
    {"name": "Outros", "icon": "🎁", "color": "#F4E9FF", "tag": "12 doações"},
]

DONATION_ITEMS = [
    {
        "title": "Kit de roupas",
        "category": "Roupas",
        "location": "São Paulo, SP",
        "description": "Conjunto de peças em bom estado para crianças e adolescentes.",
        "icon": "👕",
    },
    {
        "title": "Cesta de alimentos",
        "category": "Alimentos",
        "location": "São Paulo, SP",
        "description": "Itens essenciais para compor uma cesta de apoio familiar.",
        "icon": "🥖",
    },
    {
        "title": "Livros para estudantes",
        "category": "Livros",
        "location": "São Paulo, SP",
        "description": "Material escolar e de leitura para apoiar estudos e aprendizagem.",
        "icon": "📚",
    },
    {
        "title": "Mesa de escritório",
        "category": "Móveis",
        "location": "São Paulo, SP",
        "description": "Peça funcional para transformar um espaço de estudo ou trabalho.",
        "icon": "🪑",
    },
    {
        "title": "Brinquedos infantis",
        "category": "Outros",
        "location": "São Paulo, SP",
        "description": "Brinquedos em bom estado para alegrar pequenas histórias.",
        "icon": "🎁",
    },
    {
        "title": "Computador para estudos",
        "category": "Eletrônicos",
        "location": "São Paulo, SP",
        "description": "Equipamento útil para continuar estudos, trabalho e acesso ao futuro.",
        "icon": "💻",
    },
]


class LandingState(rx.State):
    carousel_index: int = 0

    def next(self) -> None:
        self.carousel_index = (self.carousel_index + 1) % len(DONATION_ITEMS)

    def prev(self) -> None:
        self.carousel_index = (self.carousel_index - 1) % len(DONATION_ITEMS)

    @rx.var
    def visible_cards(self) -> list[dict[str, str]]:
        return [
            DONATION_ITEMS[(self.carousel_index + offset) % len(DONATION_ITEMS)]
            for offset in range(4)
        ]


def landing_header() -> rx.Component:
    return rx.box(
        rx.container(
            rx.hstack(
                rx.link(
                    rx.hstack(
                        rx.box(
                            "♥",
                            color=PRIMARY["green"],
                            font_size="1.8rem",
                            font_weight="900",
                        ),
                        rx.text(
                            "DoaFácil",
                            color=PRIMARY["dark"],
                            font_size="1.5rem",
                            font_weight="800",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    href="/",
                    style={"text_decoration": "none"},
                ),
                rx.hstack(
                    rx.link("Explorar doações", href="#explorar", color=PRIMARY["text"], text_decoration="none"),
                    rx.link("Como funciona", href="#como-funciona", color=PRIMARY["text"], text_decoration="none"),
                    rx.link("Categorias", href="#categorias", color=PRIMARY["text"], text_decoration="none"),
                    spacing="7",
                    display=["none", "none", "flex"],
                ),
                rx.hstack(
                    rx.link(
                        rx.button(
                            "Entrar",
                            variant="ghost",
                            color=PRIMARY["dark"],
                            bg="transparent",
                            border="1px solid rgba(18,53,42,0.12)",
                            border_radius="999px",
                            px="4",
                            py="2",
                        ),
                        href="/app#login",
                    ),
                    rx.link(
                        rx.button(
                            "Quero doar",
                            bg=PRIMARY["green"],
                            color="white",
                            border_radius="999px",
                            px="5",
                            py="2.5",
                            box_shadow="0 10px 24px rgba(24,165,102,0.28)",
                        ),
                        href="#explorar",
                    ),
                    spacing="3",
                ),
                align="center",
                justify="between",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="4",
        ),
        width="100%",
        background="rgba(255,255,255,0.9)",
        backdrop_filter="blur(10px)",
        border_bottom="1px solid rgba(18,53,42,0.06)",
        position="sticky",
        top="0",
        z_index="10",
    )


def hero_section() -> rx.Component:
    return rx.box(
        rx.container(
            rx.hstack(
                rx.vstack(
                    rx.box(
                        rx.text(
                            "DOAR PODE TRANSFORMAR UM DIA",
                            color=PRIMARY["green"],
                            font_size="0.76rem",
                            font_weight="700",
                            letter_spacing="0.13em",
                        ),
                        bg="rgba(24,165,102,0.08)",
                        border="1px solid rgba(24,165,102,0.14)",
                        border_radius="999px",
                        px="3",
                        py="2",
                    ),
                    rx.heading(
                        "Uma doação simples pode fazer toda a diferença.",
                        size="7",
                        color=PRIMARY["dark"],
                        line_height="1.06",
                        width="100%",
                    ),
                    rx.text(
                        "Conecte itens que não são usados mais com pessoas ou comunidades que podem dar um novo destino a eles.",
                        color=PRIMARY["muted"],
                        font_size="1.08rem",
                        line_height="1.7",
                        max_width="560px",
                    ),
                    rx.hstack(
                        rx.link(
                            rx.button(
                                "Quero doar",
                                bg=PRIMARY["green"],
                                color="white",
                                border_radius="999px",
                                px="6",
                                py="3",
                                box_shadow="0 16px 30px rgba(24,165,102,0.24)",
                            ),
                            href="#explorar",
                        ),
                        rx.link(
                            rx.button(
                                "Encontrar uma doação",
                                bg="white",
                                color=PRIMARY["dark"],
                                border="1px solid rgba(18,53,42,0.1)",
                                border_radius="999px",
                                px="6",
                                py="3",
                            ),
                            href="#explorar",
                        ),
                        spacing="4",
                        wrap="wrap",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text("1.240+", font_weight="800", font_size="1.3rem", color=PRIMARY["dark"]),
                            rx.text("doações em circulação", color=PRIMARY["muted"], font_size="0.82rem"),
                            spacing="0",
                        ),
                        rx.vstack(
                            rx.text("680+", font_weight="800", font_size="1.3rem", color=PRIMARY["dark"]),
                            rx.text("pessoas alcançadas", color=PRIMARY["muted"], font_size="0.82rem"),
                            spacing="0",
                        ),
                        spacing="8",
                        align="start",
                        wrap="wrap",
                    ),
                    spacing="5",
                    align="start",
                    width=["100%", "100%", "55%"],
                    min_width="0",
                ),
                rx.box(
                    rx.box(
                        rx.box(
                            rx.box(
                                rx.text("💚", font_size="1.6rem"),
                                bg="rgba(255,255,255,0.65)",
                                border_radius="50%",
                                width="52px",
                                height="52px",
                                display="flex",
                                align_items="center",
                                justify_content="center",
                                box_shadow="0 14px 30px rgba(17,61,49,0.12)",
                            ),
                            rx.box(
                                rx.text("Nova oportunidade", color=PRIMARY["dark"], font_size="0.8rem", font_weight="700"),
                                rx.text("3 pessoas próximas", color=PRIMARY["muted"], font_size="0.72rem"),
                                spacing="0",
                            ),
                            justify="between",
                            align="center",
                            width="100%",
                            padding="4",
                        ),
                        rx.box(
                            rx.text("Roupas", color=PRIMARY["dark"], font_size="0.75rem", font_weight="700", bg="rgba(255,255,255,0.8)", px="3", py="2", border_radius="999px"),
                            rx.text("🔔 8 pedidos recentes", color=PRIMARY["dark"], font_size="0.75rem", font_weight="600"),
                            justify="between",
                            align="center",
                            width="100%",
                            margin_top="4",
                        ),
                        rx.box(
                            rx.text("Cesta de alimentos", color=PRIMARY["dark"], font_size="1.6rem", font_weight="700"),
                            rx.text("Ajuda imediata para famílias do entorno.", color=PRIMARY["muted"], font_size="0.9rem"),
                            spacing="1",
                            margin_top="4",
                        ),
                        rx.box(
                            rx.hstack(
                                rx.box(
                                    rx.text("32%", font_weight="700", color=PRIMARY["dark"]),
                                    rx.text("de pessoas já responderam", color=PRIMARY["muted"], font_size="0.68rem"),
                                    spacing="0",
                                ),
                                rx.button("Ver doação", bg=PRIMARY["green"], color="white", border_radius="999px", px="4", py="2"),
                                justify="between",
                                align="center",
                                width="100%",
                            ),
                            margin_top="5",
                        ),
                        bg="rgba(255,255,255,0.8)",
                        border="1px solid rgba(17,61,49,0.08)",
                        border_radius="28px",
                        box_shadow="0 26px 60px rgba(17,61,49,0.13)",
                        padding="5",
                        width="100%",
                        position="relative",
                        z_index="2",
                    ),
                    rx.box(
                        rx.box(
                            rx.text("📚", font_size="1.4rem"),
                            rx.text("Livros", font_size="0.82rem", color=PRIMARY["dark"], font_weight="700"),
                            spacing="2",
                            align="center",
                            bg="white",
                            border_radius="18px",
                            box_shadow="0 16px 26px rgba(17,61,49,0.12)",
                            padding="3",
                        ),
                        position="absolute",
                        right="-16px",
                        top="50px",
                        z_index="3",
                    ),
                    rx.box(
                        rx.box(
                            rx.text("🧥", font_size="1.2rem"),
                            rx.text("Roupas", font_size="0.72rem", color=PRIMARY["dark"], font_weight="700"),
                            spacing="2",
                            align="center",
                            bg="white",
                            border_radius="15px",
                            box_shadow="0 16px 26px rgba(17,61,49,0.12)",
                            padding="3",
                        ),
                        position="absolute",
                        left="-18px",
                        bottom="62px",
                        z_index="3",
                    ),
                    rx.box(
                        rx.text("+680 pessoas alcançadas", color=PRIMARY["dark"], font_weight="700", bg="rgba(255,255,255,0.78)", border_radius="999px", px="4", py="2"),
                        position="absolute",
                        bottom="-18px",
                        right="52px",
                        z_index="4",
                    ),
                    bg="linear-gradient(135deg, #F7EED4 0%, #EAF7F0 100%)",
                    border_radius="32px",
                    width=["100%", "100%", "45%"],
                    min_height="540px",
                    position="relative",
                    border="1px solid rgba(18,53,42,0.04)",
                    padding="6",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                justify="between",
                align="center",
                width="100%",
                spacing="6",
                wrap="wrap",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y=["10", "12", "16"],
        ),
        width="100%",
        background=PRIMARY["cream"],
    )


def search_section() -> rx.Component:
    return rx.box(
        rx.container(
            rx.box(
                rx.vstack(
                    rx.text("Encontre algo que pode fazer a diferença", color=PRIMARY["dark"], font_size="1.4rem", font_weight="700"),
                    rx.hstack(
                        rx.input(
                            placeholder="O que você está procurando?",
                            bg="#F7F9F8",
                            border="1px solid rgba(18,53,42,0.08)",
                            border_radius="18px",
                            px="4",
                            py="4",
                            width="100%",
                        ),
                        rx.button(
                            "Buscar",
                            bg=PRIMARY["green"],
                            color="white",
                            border_radius="18px",
                            px="7",
                            py="4",
                            min_width="130px",
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                        wrap="wrap",
                    ),
                    rx.hstack(
                        rx.foreach(
                            ["Roupas", "Alimentos", "Livros", "Móveis", "Eletrônicos", "Outros"],
                            lambda tag: rx.button(
                                tag,
                                variant="soft",
                                color=PRIMARY["dark"],
                                bg="rgba(24,165,102,0.08)",
                                border_radius="999px",
                                px="4",
                                py="2",
                            ),
                        ),
                        spacing="3",
                        wrap="wrap",
                    ),
                    spacing="4",
                    width="100%",
                ),
                bg="white",
                border="1px solid rgba(18,53,42,0.06)",
                border_radius="28px",
                box_shadow="0 24px 44px rgba(17,61,49,0.06)",
                padding=["5", "5", "6"],
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="0",
        ),
        width="100%",
        background="white",
        margin_top="-26px",
        padding_bottom="8",
        id="explorar",
    )


def impact_stats() -> rx.Component:
    return rx.box(
        rx.container(
            rx.hstack(
                rx.vstack(
                    rx.text("1.240+", color=PRIMARY["dark"], font_size="2.1rem", font_weight="800"),
                    rx.text("Doações compartilhadas", color=PRIMARY["muted"], font_size="0.95rem"),
                    spacing="1",
                    align="center",
                ),
                rx.vstack(
                    rx.text("680+", color=PRIMARY["dark"], font_size="2.1rem", font_weight="800"),
                    rx.text("Pessoas alcançadas", color=PRIMARY["muted"], font_size="0.95rem"),
                    spacing="1",
                    align="center",
                ),
                rx.vstack(
                    rx.text("32", color=PRIMARY["dark"], font_size="2.1rem", font_weight="800"),
                    rx.text("Categorias", color=PRIMARY["muted"], font_size="0.95rem"),
                    spacing="1",
                    align="center",
                ),
                rx.vstack(
                    rx.text("100%", color=PRIMARY["dark"], font_size="2.1rem", font_weight="800"),
                    rx.text("Feito para conectar pessoas", color=PRIMARY["muted"], font_size="0.95rem"),
                    spacing="1",
                    align="center",
                ),
                justify="between",
                align="stretch",
                width="100%",
                spacing="0",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="7",
        ),
        width="100%",
        background=PRIMARY["light"],
        border_top="1px solid rgba(18,53,42,0.03)",
        border_bottom="1px solid rgba(18,53,42,0.03)",
    )


def category_section() -> rx.Component:
    cards = []
    for item in CATEGORY_ITEMS:
        cards.append(
            rx.box(
                rx.box(
                    rx.text(item["icon"], font_size="2.4rem"),
                    bg=item["color"],
                    border_radius="22px",
                    width="64px",
                    height="64px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.heading(item["name"], size="5", color=PRIMARY["dark"]),
                rx.text(
                    "Descubra itens que podem ajudar alguém com facilidade e propósito.",
                    color=PRIMARY["muted"],
                    font_size="0.94rem",
                    line_height="1.7",
                ),
                rx.hstack(
                    rx.text(item["tag"], color=PRIMARY["green"], font_size="0.78rem", font_weight="700"),
                    rx.text("→", color=PRIMARY["dark"], font_weight="700"),
                    justify="between",
                    width="100%",
                    margin_top="4",
                ),
                bg="white",
                border="1px solid rgba(18,53,42,0.06)",
                border_radius="24px",
                padding="5",
                width="100%",
                box_shadow="0 14px 30px rgba(17,61,49,0.04)",
                transition="transform 0.2s ease, box-shadow 0.2s ease",
                _hover={"transform": "translateY(-4px)", "box_shadow": "0 18px 34px rgba(17,61,49,0.08)"},
            )
        )
    return rx.box(
        rx.container(
            rx.vstack(
                rx.heading("Encontre uma forma de ajudar", size="7", color=PRIMARY["dark"]),
                rx.text(
                    "Explore as categorias e descubra onde sua doação pode fazer a diferença.",
                    color=PRIMARY["muted"],
                    font_size="1.05rem",
                    text_align="center",
                ),
                rx.grid(*cards, columns="3", spacing="4", width="100%"),
                spacing="6",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background="white",
        id="categorias",
    )


def featured_section() -> rx.Component:
    return rx.box(
        rx.container(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Doações em destaque", size="7", color=PRIMARY["dark"]),
                        rx.text(
                            "Talvez aquilo que você procura esteja esperando por você.",
                            color=PRIMARY["muted"],
                            font_size="1.04rem",
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.hstack(
                        rx.button(
                            "←",
                            on_click=LandingState.prev,
                            bg="white",
                            color=PRIMARY["dark"],
                            border="1px solid rgba(18,53,42,0.08)",
                            border_radius="999px",
                            width="48px",
                            height="48px",
                        ),
                        rx.button(
                            "→",
                            on_click=LandingState.next,
                            bg=PRIMARY["green"],
                            color="white",
                            border_radius="999px",
                            width="48px",
                            height="48px",
                        ),
                        spacing="3",
                    ),
                    justify="between",
                    width="100%",
                    align="end",
                ),
                rx.grid(
                    rx.foreach(
                        LandingState.visible_cards,
                        lambda item: rx.box(
                            rx.box(
                                rx.box(
                                    rx.text(item["icon"], font_size="2rem"),
                                    bg="rgba(255,255,255,0.72)",
                                    border_radius="18px",
                                    px="3",
                                    py="2",
                                ),
                                rx.text(item["category"], color=PRIMARY["dark"], font_weight="700", font_size="0.7rem", bg="rgba(255,255,255,0.78)", px="3", py="2", border_radius="999px"),
                                justify="between",
                                align="center",
                                width="100%",
                                padding="4",
                            ),
                            rx.vstack(
                                rx.text(item["title"], color=PRIMARY["dark"], font_size="1.4rem", font_weight="700"),
                                rx.text(item["location"], color=PRIMARY["muted"], font_size="0.82rem"),
                                rx.text(item["description"], color=PRIMARY["muted"], font_size="0.92rem", line_height="1.7"),
                                rx.button(
                                    "Ver doação",
                                    bg=PRIMARY["green"],
                                    color="white",
                                    border_radius="999px",
                                    px="4",
                                    py="2",
                                ),
                                spacing="3",
                                width="100%",
                                padding="4",
                            ),
                            bg="white",
                            border_radius="26px",
                            border="1px solid rgba(18,53,42,0.06)",
                            box_shadow="0 20px 36px rgba(17,61,49,0.06)",
                            overflow="hidden",
                            width="100%",
                        ),
                    ),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                rx.hstack(
                    rx.foreach(
                        range(len(DONATION_ITEMS)),
                        lambda idx: rx.box(
                            width="10px",
                            height="10px",
                            border_radius="999px",
                            bg=rx.cond(LandingState.carousel_index == idx, PRIMARY["green"], "rgba(18,53,42,0.18)"),
                            transition="all 0.2s ease",
                        ),
                    ),
                    spacing="2",
                    justify="center",
                    width="100%",
                ),
                spacing="6",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background=PRIMARY["light"],
    )


def how_it_works() -> rx.Component:
    return rx.box(
        rx.container(
            rx.vstack(
                rx.heading("Doar é mais simples do que parece", size="7", color=PRIMARY["dark"]),
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.text("01", color=PRIMARY["green"], font_weight="800", font_size="0.96rem"),
                            rx.text("ENCONTRE", color=PRIMARY["dark"], font_weight="700", font_size="1.1rem"),
                            rx.text("Encontre algo que você pode doar.", color=PRIMARY["muted"], font_size="0.95rem", line_height="1.7"),
                            spacing="3",
                            align="start",
                            width="100%",
                        ),
                        rx.box(
                            rx.text("02", color=PRIMARY["green"], font_weight="800", font_size="0.96rem"),
                            rx.text("CONECTE", color=PRIMARY["dark"], font_weight="700", font_size="1.1rem"),
                            rx.text("Converse com quem precisa.", color=PRIMARY["muted"], font_size="0.95rem", line_height="1.7"),
                            spacing="3",
                            align="start",
                            width="100%",
                        ),
                        rx.box(
                            rx.text("03", color=PRIMARY["green"], font_weight="800", font_size="0.96rem"),
                            rx.text("TRANSFORME", color=PRIMARY["dark"], font_weight="700", font_size="1.1rem"),
                            rx.text("Sua doação ganha um novo destino.", color=PRIMARY["muted"], font_size="0.95rem", line_height="1.7"),
                            spacing="3",
                            align="start",
                            width="100%",
                        ),
                        justify="between",
                        align="stretch",
                        width="100%",
                        spacing="5",
                    ),
                    width="100%",
                    position="relative",
                    padding_top="3",
                ),
                spacing="6",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background="white",
        id="como-funciona",
    )


def trust_section() -> rx.Component:
    return rx.box(
        rx.container(
            rx.vstack(
                rx.heading("Doar deve ser simples. E seguro.", size="7", color="white"),
                rx.text(
                    "O DoaFácil foi pensado para aproximar pessoas de forma clara, responsável e transparente.",
                    color="rgba(255,255,255,0.82)",
                    font_size="1.05rem",
                    text_align="center",
                    max_width="760px",
                ),
                rx.grid(
                    rx.box(
                        rx.text("🔒", font_size="2rem"),
                        rx.heading("Dados protegidos", size="5", color="white"),
                        rx.text("Suas informações merecem cuidado.", color="rgba(255,255,255,0.8)", font_size="0.95rem"),
                        bg="rgba(255,255,255,0.12)",
                        border="1px solid rgba(255,255,255,0.12)",
                        border_radius="22px",
                        padding="5",
                    ),
                    rx.box(
                        rx.text("✓", font_size="2rem"),
                        rx.heading("Informações claras", size="5", color="white"),
                        rx.text("Saiba o que está sendo oferecido antes de entrar em contato.", color="rgba(255,255,255,0.8)", font_size="0.95rem"),
                        bg="rgba(255,255,255,0.12)",
                        border="1px solid rgba(255,255,255,0.12)",
                        border_radius="22px",
                        padding="5",
                    ),
                    rx.box(
                        rx.text("🛡", font_size="2rem"),
                        rx.heading("Experiência segura", size="5", color="white"),
                        rx.text("Recursos pensados para tornar a jornada mais confiável.", color="rgba(255,255,255,0.8)", font_size="0.95rem"),
                        bg="rgba(255,255,255,0.12)",
                        border="1px solid rgba(255,255,255,0.12)",
                        border_radius="22px",
                        padding="5",
                    ),
                    rx.box(
                        rx.text("💚", font_size="2rem"),
                        rx.heading("Comunidade", size="5", color="white"),
                        rx.text("Uma plataforma feita para aproximar quem pode ajudar de quem precisa.", color="rgba(255,255,255,0.8)", font_size="0.95rem"),
                        bg="rgba(255,255,255,0.12)",
                        border="1px solid rgba(255,255,255,0.12)",
                        border_radius="22px",
                        padding="5",
                    ),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                spacing="6",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background=PRIMARY["dark"],
    )


def impact_story() -> rx.Component:
    return rx.box(
        rx.container(
            rx.hstack(
                rx.vstack(
                    rx.heading("Pequenos gestos podem mudar grandes histórias.", size="7", color=PRIMARY["dark"]),
                    rx.text(
                        "Quando você doa aquilo que não usa mais, abre espaço para que outra pessoa encontre uma solução real, acolhedora e útil.",
                        color=PRIMARY["muted"],
                        font_size="1.05rem",
                        line_height="1.8",
                    ),
                    rx.hstack(
                        rx.box(
                            rx.text("+1.240", color=PRIMARY["dark"], font_weight="800", font_size="1.7rem"),
                            rx.text("doações", color=PRIMARY["muted"], font_size="0.88rem"),
                            spacing="1",
                            align="center",
                        ),
                        rx.box(
                            rx.text("+680", color=PRIMARY["dark"], font_weight="800", font_size="1.7rem"),
                            rx.text("pessoas", color=PRIMARY["muted"], font_size="0.88rem"),
                            spacing="1",
                            align="center",
                        ),
                        rx.box(
                            rx.text("+32", color=PRIMARY["dark"], font_weight="800", font_size="1.7rem"),
                            rx.text("categorias", color=PRIMARY["muted"], font_size="0.88rem"),
                            spacing="1",
                            align="center",
                        ),
                        spacing="6",
                        wrap="wrap",
                    ),
                    spacing="5",
                    align="start",
                    width=["100%", "100%", "52%"],
                ),
                rx.box(
                    rx.box(
                        rx.box(
                            rx.text("💛", font_size="2rem"),
                            rx.text("+1.240\ndoações", color=PRIMARY["dark"], font_weight="700", line_height="1.3"),
                            bg="white",
                            border_radius="22px",
                            box_shadow="0 18px 30px rgba(17,61,49,0.08)",
                            padding="4",
                            width="170px",
                        ),
                        rx.box(
                            rx.text("🧥", font_size="2rem"),
                            rx.text("+680\npessoas", color=PRIMARY["dark"], font_weight="700", line_height="1.3"),
                            bg="rgba(255,255,255,0.7)",
                            border_radius="22px",
                            box_shadow="0 18px 30px rgba(17,61,49,0.08)",
                            padding="4",
                            width="170px",
                        ),
                        rx.box(
                            rx.text("📚", font_size="2rem"),
                            rx.text("+32\ncategorias", color=PRIMARY["dark"], font_weight="700", line_height="1.3"),
                            bg="white",
                            border_radius="22px",
                            box_shadow="0 18px 30px rgba(17,61,49,0.08)",
                            padding="4",
                            width="170px",
                        ),
                        position="relative",
                        z_index="2",
                        spacing="4",
                    ),
                    rx.box(
                        rx.text("”", color=PRIMARY["green"], font_size="4rem", font_weight="700"),
                        position="absolute",
                        top="-10px",
                        right="36px",
                    ),
                    bg="linear-gradient(135deg, rgba(24,165,102,0.08) 0%, rgba(244,183,64,0.14) 100%)",
                    border="1px solid rgba(24,165,102,0.08)",
                    border_radius="32px",
                    min_height="350px",
                    width=["100%", "100%", "48%"],
                    position="relative",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    padding="6",
                ),
                justify="between",
                align="center",
                width="100%",
                spacing="6",
                wrap="wrap",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background=PRIMARY["cream"],
    )


def emotional_cta() -> rx.Component:
    return rx.box(
        rx.container(
            rx.box(
                rx.vstack(
                    rx.text("O que não faz mais falta para você pode significar muito para alguém.", font_size="2.2rem", font_weight="700", color="white", line_height="1.15", max_width="820px"),
                    rx.text(
                        "Uma peça de roupa, um livro, um móvel ou uma cesta de alimentos pode começar uma nova história.",
                        color="rgba(255,255,255,0.82)",
                        font_size="1.08rem",
                        line_height="1.8",
                        max_width="780px",
                    ),
                    rx.button(
                        "Quero fazer uma doação",
                        bg=PRIMARY["yellow"],
                        color=PRIMARY["dark"],
                        border_radius="999px",
                        px="7",
                        py="3",
                        box_shadow="0 18px 32px rgba(244,183,64,0.3)",
                    ),
                    spacing="5",
                    align="start",
                ),
                bg=PRIMARY["green"],
                border_radius="30px",
                padding=["6", "6", "7"],
                width="100%",
                position="relative",
                overflow="hidden",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="6",
        ),
        width="100%",
        background="white",
    )


def final_cta() -> rx.Component:
    return rx.box(
        rx.container(
            rx.box(
                rx.vstack(
                    rx.text("Pronto para fazer a diferença?", color=PRIMARY["dark"], font_size="2.2rem", font_weight="700"),
                    rx.text(
                        "Comece com uma pequena doação e ajude algo que você não usa mais a encontrar um novo destino.",
                        color=PRIMARY["muted"],
                        font_size="1.05rem",
                        max_width="620px",
                        text_align="center",
                    ),
                    rx.button(
                        "Começar agora",
                        bg=PRIMARY["green"],
                        color="white",
                        border_radius="999px",
                        px="7",
                        py="3",
                        box_shadow="0 18px 30px rgba(24,165,102,0.2)",
                    ),
                    spacing="5",
                    align="center",
                ),
                bg="rgba(24,165,102,0.05)",
                border="1px solid rgba(24,165,102,0.08)",
                border_radius="28px",
                padding=["8", "6", "9"],
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="7",
        ),
        width="100%",
        background="white",
    )


def institutional_footer() -> rx.Component:
    return rx.box(
        rx.container(
            rx.grid(
                rx.vstack(
                    rx.text("DoaFácil", color="white", font_size="2rem", font_weight="700"),
                    rx.text(
                        "Uma plataforma para conectar doações com pessoas que precisam de ajuda de forma simples e acolhedora.",
                        color="rgba(255,255,255,0.72)",
                        line_height="1.8",
                    ),
                    rx.text("© 2026 DoaFácil. Todos os direitos reservados.", color="rgba(255,255,255,0.62)", font_size="0.88rem"),
                    spacing="4",
                    align="start",
                ),
                rx.vstack(
                    rx.text("Sobre nós", color="white", font_weight="700"),
                    rx.link("Como funciona", href="#como-funciona", style={"color": "rgba(255,255,255,0.7)", "text_decoration": "none"}),
                    rx.link("Categorias", href="#categorias", style={"color": "rgba(255,255,255,0.7)", "text_decoration": "none"}),
                    rx.link("Explorar doações", href="#explorar", style={"color": "rgba(255,255,255,0.7)", "text_decoration": "none"}),
                    spacing="3",
                    align="start",
                ),
                rx.vstack(
                    rx.text("Ajuda", color="white", font_weight="700"),
                    rx.text("Central de ajuda", color="rgba(255,255,255,0.7)"),
                    rx.text("Termos", color="rgba(255,255,255,0.7)"),
                    rx.text("Privacidade", color="rgba(255,255,255,0.7)"),
                    spacing="3",
                    align="start",
                ),
                rx.vstack(
                    rx.text("Comunidade", color="white", font_weight="700"),
                    rx.text("Explorar doações", color="rgba(255,255,255,0.7)"),
                    rx.text("Quero doar", color="rgba(255,255,255,0.7)"),
                    rx.link("Entrar", href="/app#login", style={"color": "rgba(255,255,255,0.7)", "text_decoration": "none"}),
                    spacing="3",
                    align="start",
                ),
                columns="4",
                spacing="8",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background=PRIMARY["dark"],
    )


def landing_page() -> rx.Component:
    return rx.vstack(
        landing_header(),
        hero_section(),
        search_section(),
        impact_stats(),
        category_section(),
        featured_section(),
        how_it_works(),
        trust_section(),
        impact_story(),
        emotional_cta(),
        final_cta(),
        institutional_footer(),
        width="100%",
        min_height="100vh",
        background=PRIMARY["background"],
        color=PRIMARY["text"],
        spacing="0",
    )
