"""Rodapé público e rotas institucionais (change paginas-institucionais).

O rodapé saiu de doafacil.py sem mudança visual, para as páginas
institucionais (institucional.py) o reaproveitarem sem import circular.
"""

from __future__ import annotations

import reflex as rx

from doafacil.chat import CHAT_FAB_CLEARANCE
from doafacil.explorar import EXPLORE_ROUTE, RECENT_DONATIONS_ANCHOR

# Páginas institucionais. Substituem as “rotas futuras” da change
# landing-nova: todas existem desde a change paginas-institucionais.
INSTITUTIONAL_ROUTES = {
    "quem_somos": "/quem-somos",
    "contato": "/contato",
    "privacidade": "/privacidade",
    "termos": "/termos",
    "duvidas": "/duvidas",
    "seguranca": "/seguranca",
}
CONTACT_ROUTE = INSTITUTIONAL_ROUTES["contato"]
# E-mail de contato do projeto. PENDÊNCIA: o grupo ainda não definiu um.
# Enquanto vazio, os convites de contato levam a /contato; preenchido, viram
# mailto:. Nunca usar um endereço que o projeto não tenha.
CONTACT_EMAIL = ""
# “Como funciona” é a seção institucional da home (não há página própria).
HOW_IT_WORKS_ANCHOR = "/#como-funciona"

FOOTER_LINK_GROUPS = (
    (("Quem somos", INSTITUTIONAL_ROUTES["quem_somos"]), ("Doações", EXPLORE_ROUTE)),
    (("Criar doações", "/cadastro-doacao"), ("Doações mais recentes", RECENT_DONATIONS_ANCHOR)),
    (("Política de privacidade", INSTITUTIONAL_ROUTES["privacidade"]), ("Termos de uso", INSTITUTIONAL_ROUTES["termos"])),
    (("Dúvidas frequentes", INSTITUTIONAL_ROUTES["duvidas"]), ("Segurança e transparência", INSTITUTIONAL_ROUTES["seguranca"])),
)
FOOTER_FOCUS_RING = {"outline": "2px solid #2DBF72", "outlineOffset": "2px"}


def contact_href() -> str:
    """Destino dos convites de contato: o mailto quando há e-mail definido;
    senão, a página /contato."""
    email = CONTACT_EMAIL.strip()
    return f"mailto:{email}" if email else CONTACT_ROUTE


def _footer_link(label: str, href: str) -> rx.Component:
    """Link do rodapé: #F5F5F5 sobre #252525 (14,6:1), sem sublinhado.
    Um `mailto:` também funciona: o Link do React Router trata URLs com
    esquema como externas e gera um <a href> comum."""
    return rx.link(
        label,
        href=href,
        color="#F5F5F5",
        font_size="13px",
        underline="hover",
        _focus_visible=FOOTER_FOCUS_RING,
    )


def public_home_footer() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.image(
                src="/logo.svg",
                alt="DoaFácil",
                width="160px",
                height="58px",
                object_fit="contain",
            ),
            rx.flex(
                rx.vstack(
                    rx.text(
                        "Fale conosco",
                        font_size="15px",
                        font_weight="700",
                        color="#2DBF72",
                    ),
                    _footer_link("Clique aqui para falar conosco", contact_href()),
                    align="start",
                    spacing="1",
                    style={"width": rx.breakpoints(initial="100%", md="28%")},
                ),
                rx.vstack(
                    rx.text(
                        "Links rápidos",
                        font_size="15px",
                        font_weight="700",
                        color="#2DBF72",
                    ),
                    rx.flex(
                        *[
                            rx.vstack(
                                *[_footer_link(label, href) for label, href in group],
                                align="start",
                                spacing="0",
                                style={
                                    "rowGap": "6px",
                                    "width": rx.breakpoints(
                                        initial="50%", md="25%"
                                    )
                                },
                            )
                            for group in FOOTER_LINK_GROUPS
                        ],
                        wrap="wrap",
                        align="start",
                        gap="0",
                        width="100%",
                    ),
                    align="start",
                    spacing="2",
                    style={
                        "width": rx.breakpoints(
                            initial="100%", md="calc(72% - 16px)"
                        )
                    },
                ),
                style={
                    "flexDirection": rx.breakpoints(
                        initial="column", md="row"
                    )
                },
                align="start",
                gap="4",
                width="100%",
            ),
            rx.text(
                "Projeto acadêmico DoaFácil",
                color="#D7D7D7",
                font_size="12px",
                border_top="1px solid #515151",
                padding_top="20px",
                width="100%",
            ),
            align="start",
            spacing="5",
            width="100%",
            max_width="1200px",
            margin="0 auto",
            padding_top="48px",
            padding_x="24px",
            # Espaço do botão flutuante: nada do rodapé fica sob ele.
            padding_bottom=CHAT_FAB_CLEARANCE,
        ),
        width="100%",
        background="#252525",
        color="white",
    )
