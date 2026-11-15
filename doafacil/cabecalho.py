"""Partes do cabeçalho compartilhadas entre a home, a /explorar e a
/categorias (change explorar-categorias): o menu da conta e os controles de
sessão (“Entrar” ou o menu, e “Quero Doar”).

Fica num módulo próprio para que explorar.py e categorias.py não precisem
importar doafacil.py, o que criaria um import circular.
"""

from __future__ import annotations

import reflex as rx

from doafacil.login import LoginState

GREEN = "#168447"
FOCUS_RING = {"outline": f"2px solid {GREEN}", "outlineOffset": "2px"}
# Bordas do conteúdo do cabeçalho: até 1200 px, com 16 px de margem no
# celular e 24 px a partir de md.
HEADER_MAX_WIDTH = "1200px"
HEADER_PADDING_X = rx.breakpoints(initial="16px", md="24px")
HEADER_PADDING = rx.breakpoints(initial="12px 16px", md="12px 24px")


class HeaderState(LoginState):
    """Dados do cabeçalho calculados no servidor. A inicial era calculada no
    navegador (`account_name[0].toUpperCase()`) e quebrava a página com o nome
    ainda indefinido, enquanto o perfil carregava."""

    @rx.var
    def account_initial(self) -> str:
        name = self.account_name
        if not isinstance(name, str):
            return ""
        cleaned = name.strip()
        return cleaned[0].upper() if cleaned else ""


def _account_avatar() -> rx.Component:
    """Inicial do nome ou, sem nome ainda, o ícone de pessoa."""
    return rx.cond(
        HeaderState.account_initial != "",
        rx.text(HeaderState.account_initial, as_="span"),
        rx.icon("user", size=18, aria_hidden="true"),
    )


def account_menu() -> rx.Component:
    """Menu da conta (change landing-nova): inicial e primeiro nome, com
    “Minhas doações”, “Editar perfil” e “Sair”. O Radix cuida do teclado
    (setas, Enter, Esc) e do foco."""
    name = LoginState.account_name
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.box(
                    _account_avatar(),
                    aria_hidden="true",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    width="32px",
                    height="32px",
                    flex_shrink="0",
                    border_radius="50%",
                    background="#EDEDED",
                    border="1px solid #D6D6D6",
                    color="#555555",
                    font_weight="700",
                ),
                rx.text(
                    name,
                    class_name="home-account-name",
                    color="#333333",
                    font_weight="700",
                    white_space="nowrap",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    min_width="0",
                    max_width=rx.breakpoints(initial="80px", lg="120px"),
                    # Abaixo de 768 px (sm) fica só a inicial (o nome continua
                    # no rótulo acessível), para o cabeçalho caber em 360 px.
                    display=rx.breakpoints(initial="none", sm="block"),
                ),
                rx.icon("chevron-down", size=16, color="#333333", aria_hidden="true"),
                aria_label=rx.Var.create("Menu da conta de ") + name,
                class_name="home-account-menu",
                variant="ghost",
                display="inline-flex",
                align_items="center",
                gap="8px",
                min_height="44px",
                padding="0 8px",
                cursor="pointer",
                _focus_visible=FOCUS_RING,
            ),
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("package", size=16, aria_hidden="true"),
                "Minhas doações",
                on_select=rx.redirect("/minhas-doacoes"),
            ),
            rx.menu.item(
                rx.icon("user-pen", size=16, aria_hidden="true"),
                "Editar perfil",
                on_select=rx.redirect("/perfil/editar"),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("log-out", size=16, aria_hidden="true"),
                "Sair",
                on_select=LoginState.logout,
            ),
            align="end",
        ),
    )


def header_auth_controls() -> rx.Component:
    """“Entrar” ou o menu da conta, e “Quero Doar”. A entrada no chat é o
    botão flutuante (chat_fab), não um item do cabeçalho."""
    return rx.hstack(
        rx.cond(
            LoginState.auth_token,
            account_menu(),
            rx.button(
                "Entrar",
                variant="outline",
                color=GREEN,
                border_color=GREEN,
                size="2",
                on_click=rx.redirect("/login"),
            ),
        ),
        rx.link(
            "Quero Doar",
            href="/cadastro-doacao",
            background=GREEN,
            color="white",
            padding="8px 16px",
            border_radius="6px",
            font_size="14px",
            font_weight="500",
            white_space="nowrap",
            display="inline-flex",
            align_items="center",
            min_height="44px",
            _hover={"background": "#126f3b"},
            _focus_visible=FOCUS_RING,
        ),
        spacing=rx.breakpoints(initial="2", sm="3"),
        align="center",
    )
