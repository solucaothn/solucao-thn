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
    """Foto de perfil, redonda e cortada (cover); sem foto, a inicial do nome
    ou, sem nome ainda, o ícone de pessoa. O círculo é decorativo (o nome está
    no rótulo do botão), por isso a foto tem alt vazio."""
    return rx.cond(
        LoginState.account_photo != "",
        rx.image(
            src=LoginState.account_photo,
            alt="",
            class_name="home-account-photo",
            width="100%",
            height="100%",
            object_fit="cover",
            border_radius="50%",
            display="block",
        ),
        rx.cond(
            HeaderState.account_initial != "",
            rx.text(HeaderState.account_initial, as_="span"),
            rx.icon("user", size=18, aria_hidden="true"),
        ),
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
                    overflow="hidden",
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


BACK_LINK_COLOR = "#166B3B"  # 6,1:1 sobre o creme


def back_link(label: str = "Voltar ao início", href: str = "/", class_name: str = "institutional-back-link") -> rx.Component:
    """“Voltar” das páginas com o cabeçalho de logotipo, da /explorar e da
    /categorias: seta e texto em verde escuro. A cor vale também visitado e
    com o mouse em cima, para não herdar o azul do tema do Radix."""
    fixed_color = {"color": BACK_LINK_COLOR}
    return rx.link(
        rx.icon("chevron-left", size=18, aria_hidden="true"),
        label,
        href=href,
        class_name=class_name,
        color=BACK_LINK_COLOR,
        display="inline-flex",
        align_items="center",
        gap="4px",
        min_height="44px",
        underline="hover",
        _visited=fixed_color,
        _hover=fixed_color,
        _focus_visible=FOCUS_RING,
    )


LOGO_WIDTH = rx.breakpoints(initial="100px", md="190px")


def account_control(touch: bool = False) -> rx.Component:
    """O menu da conta, com sessão, ou “Entrar”, sem sessão. Com `touch`
    (barra do celular), “Entrar” ganha 44 px de altura; no desktop fica como
    sempre foi."""
    touch_props = {"min_height": "44px"} if touch else {}
    return rx.cond(
        LoginState.auth_token,
        account_menu(),
        rx.button(
            "Entrar",
            variant="outline",
            color=GREEN,
            border_color=GREEN,
            size="2",
            on_click=rx.redirect(LoginState.login_href),
            **touch_props,
        ),
    )


def donate_link() -> rx.Component:
    return rx.link(
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
    )


def header_auth_controls(show_donate: bool = True) -> rx.Component:
    """“Entrar” ou o menu da conta, e “Quero Doar” (fora no cadastro de
    doação, que é a própria página). A entrada no chat é o botão flutuante
    (chat_fab), não um item do cabeçalho."""
    return rx.hstack(
        account_control(),
        *([donate_link()] if show_donate else []),
        spacing=rx.breakpoints(initial="2", sm="3"),
        align="center",
    )
