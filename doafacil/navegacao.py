"""Navegação do site (change navegacao-celular, spec site-navigation).

- O menu do celular: o botão ☰ (abaixo de 992 px) e o painel lateral. É um
  rx.dialog à esquerda, como a gaveta de Categorias (categorias.py): o Radix
  prende o foco, fecha com Esc e com clique fora e devolve o foco ao ☰.
- O cabeçalho centralizado das páginas com logotipo no meio (institucionais,
  detalhe, perfil de quem doa, chat, Minhas doações, Editar doação, Editar
  perfil e cadastro de doação): “Voltar” à esquerda (quando há), logotipo no
  centro e, à direita, os controles da conta no desktop ou o ☰ no celular.

Fica num módulo próprio porque usa o ChatState (total de não lidas); o
cabecalho.py não pode importar o chat.py. O _header() do chat.py importa este
módulo dentro da função, para não criar import circular.
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from doafacil.cabecalho import (
    FOCUS_RING,
    GREEN,
    LOGO_WIDTH,
    HeaderState,
    _account_avatar,
    account_control,
    header_auth_controls,
)
from doafacil.chat import GREEN_TEXT, ChatState, unread_badge
from doafacil.login import LoginState

NAV_MENU_TITLE = "Menu"
NAV_MENU_TRIGGER_LABEL = "Abrir menu"
NAV_PANEL_WIDTH = "min(360px, 100vw)"
NAV_ITEM_COLOR = "#1F1F1F"
NAV_DIVIDER = "#D9D9D9"
EXPLORE_ROUTE = "/explorar"
# Iguais aos de rodape.py e explorar.py (que importam este módulo por
# tabela; um teste confere que continuam iguais).
HOW_IT_WORKS_ANCHOR = "/#como-funciona"

# (rótulo, destino, ícone) — itens para todos, nesta ordem (spec).
NAV_PUBLIC_ITEMS = (
    ("Explorar doações", EXPLORE_ROUTE, "compass"),
    ("Como funciona", HOW_IT_WORKS_ANCHOR, "circle-help"),
    ("Categorias", "/categorias", "layout-grid"),
)
NAV_DONATE_ITEM = ("Quero Doar", "/cadastro-doacao", "heart-handshake")
# Itens da conta (com sessão), antes do “Sair”.
NAV_ACCOUNT_ITEMS = (
    ("Minhas doações", "/minhas-doacoes", "package"),
    ("Editar perfil", "/perfil/editar", "user-pen"),
)
NAV_MESSAGES_ITEM = ("Mensagens", "/chat", "message-circle")


class NavMenuState(rx.State):
    """Painel do menu do celular aberto ou fechado."""

    open: bool = False

    @rx.event
    def set_open(self, is_open: bool) -> None:
        self.open = bool(is_open)

    @rx.event
    def close(self) -> None:
        self.open = False


_ITEM_STYLE: dict[str, Any] = {
    "display": "flex",
    "align_items": "center",
    "gap": "12px",
    "width": "100%",
    "min_height": "48px",
    "padding": "8px 16px",
    "border_radius": "8px",
    "color": NAV_ITEM_COLOR,
    "font_weight": "700",
    "font_size": "1rem",
    "underline": "none",
    "_hover": {"background": "#F2F7F3"},
    "_focus_visible": FOCUS_RING,
}


def _nav_item(label: str, href: str, icon: str, *extra: rx.Component, **props: Any) -> rx.Component:
    """Um destino do painel: ícone e texto; escolher fecha o painel."""
    class_name = props.pop("class_name", "nav-menu-item")
    style = {**_ITEM_STYLE, **props}
    return rx.el.li(
        rx.link(
            rx.icon(icon, size=20, color=GREEN, aria_hidden="true"),
            rx.text(label, as_="span", flex="1"),
            *extra,
            href=href,
            on_click=NavMenuState.close,
            class_name=class_name,
            **style,
        ),
        list_style="none",
    )


def _messages_item() -> rx.Component:
    """“Mensagens” com o total de não lidas já carregado na sessão (sem
    consulta nova); o total vai no rótulo acessível, e o selo é decorativo."""
    label, href, icon = NAV_MESSAGES_ITEM
    return _nav_item(
        label,
        href,
        icon,
        rx.cond(
            ChatState.unread_total > 0,
            unread_badge(ChatState.unread_total_text),
            rx.fragment(),
        ),
        aria_label=ChatState.unread_link_label,
    )


def _account_block() -> rx.Component:
    """Foto (ou inicial) e primeiro nome da conta, no topo dos itens da conta."""
    return rx.flex(
        rx.box(
            _account_avatar(),
            aria_hidden="true",
            display="flex",
            align_items="center",
            justify_content="center",
            width="40px",
            height="40px",
            flex_shrink="0",
            border_radius="50%",
            overflow="hidden",
            background="#EDEDED",
            border="1px solid #D6D6D6",
            color="#555555",
            font_weight="700",
        ),
        rx.text(
            LoginState.account_name,
            class_name="nav-menu-account-name",
            color=NAV_ITEM_COLOR,
            font_weight="700",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
            min_width="0",
        ),
        align="center",
        gap="12px",
        padding="8px 16px",
    )


def _logout_item() -> rx.Component:
    return rx.el.li(
        rx.el.button(
            rx.icon("log-out", size=20, color=GREEN, aria_hidden="true"),
            rx.text("Sair", as_="span"),
            type="button",
            on_click=[LoginState.logout, NavMenuState.close],
            class_name="nav-menu-item nav-menu-logout",
            background="transparent",
            border="none",
            cursor="pointer",
            font_family="inherit",
            text_align="left",
            **{k: v for k, v in _ITEM_STYLE.items() if k != "underline"},
        ),
        list_style="none",
    )


def _list(*items: rx.Component, **props: Any) -> rx.Component:
    return rx.el.ul(
        *items,
        display="flex",
        flex_direction="column",
        gap="4px",
        margin="0",
        padding="0",
        width="100%",
        **props,
    )


def nav_menu_items() -> rx.Component:
    """Os itens do painel: os destinos para todos, “Quero Doar”, e a conta
    (com sessão) ou “Entrar” (sem sessão)."""
    donate_label, donate_href, donate_icon = NAV_DONATE_ITEM
    logged_in = LoginState.auth_token != ""
    return rx.box(
        _list(
            *[_nav_item(label, href, icon) for label, href, icon in NAV_PUBLIC_ITEMS],
            _nav_item(
                donate_label,
                donate_href,
                donate_icon,
                class_name="nav-menu-item nav-menu-donate",
                background="#E8F3EC",
                color=GREEN_TEXT,
            ),
            class_name="nav-menu-public",
        ),
        rx.box(height="1px", background=NAV_DIVIDER, margin="12px 8px", aria_hidden="true"),
        rx.cond(
            logged_in,
            rx.box(
                _account_block(),
                _list(
                    _nav_item(*NAV_ACCOUNT_ITEMS[0]),
                    _messages_item(),
                    _nav_item(*NAV_ACCOUNT_ITEMS[1]),
                    _logout_item(),
                    class_name="nav-menu-account",
                ),
            ),
            _list(
                _nav_item("Entrar", "/login", "log-in"),
                class_name="nav-menu-visitor",
            ),
        ),
        padding="12px 8px",
        overflow_y="auto",
        flex="1",
    )


def nav_menu_trigger() -> rx.Component:
    return rx.el.button(
        rx.icon("menu", size=24, aria_hidden="true"),
        type="button",
        aria_label=NAV_MENU_TRIGGER_LABEL,
        aria_haspopup="dialog",
        class_name="nav-menu-trigger",
        display="inline-flex",
        align_items="center",
        justify_content="center",
        width="44px",
        height="44px",
        min_width="44px",
        min_height="44px",
        padding="0",
        margin="0",
        border="none",
        border_radius="8px",
        background="transparent",
        color=NAV_ITEM_COLOR,
        cursor="pointer",
        _hover={"background": "#F2F7F3"},
        _focus_visible=FOCUS_RING,
    )


def nav_menu() -> rx.Component:
    """O botão ☰ e o painel lateral à esquerda."""
    return rx.dialog.root(
        rx.dialog.trigger(nav_menu_trigger()),
        rx.dialog.content(
            rx.flex(
                rx.dialog.title(
                    NAV_MENU_TITLE,
                    color=NAV_ITEM_COLOR,
                    font_size="1.25rem",
                    font_weight="700",
                    margin="0",
                ),
                rx.dialog.close(
                    rx.button(
                        rx.icon("x", size=22, aria_hidden="true"),
                        aria_label="Fechar",
                        variant="ghost",
                        color="#333333",
                        min_width="44px",
                        min_height="44px",
                        _focus_visible=FOCUS_RING,
                    ),
                ),
                justify="between",
                align="center",
                padding="20px 16px 16px 20px",
                border_bottom=f"1px solid {NAV_DIVIDER}",
            ),
            rx.dialog.description(
                "Navegação do DoaFácil.",
                style={
                    "position": "absolute",
                    "width": "1px",
                    "height": "1px",
                    "overflow": "hidden",
                    "clip": "rect(0 0 0 0)",
                    "whiteSpace": "nowrap",
                },
            ),
            nav_menu_items(),
            class_name="nav-menu-panel",
            # Painel lateral: preso à esquerda, na altura toda da tela.
            position="fixed",
            top="0",
            left="0",
            bottom="0",
            width=NAV_PANEL_WIDTH,
            max_width=NAV_PANEL_WIDTH,
            height="100dvh",
            max_height="100dvh",
            margin="0",
            padding="0",
            border_radius="0",
            display="flex",
            flex_direction="column",
            background="white",
            transform="none",
            box_shadow="4px 0 24px rgba(0, 0, 0, 0.12)",
        ),
        open=NavMenuState.open,
        on_open_change=NavMenuState.set_open,
    )


def mobile_header_controls() -> rx.Component:
    """Barra do celular da home, da /explorar e da /categorias: a conta (ou
    “Entrar”) e o ☰. Some a partir de 992 px."""
    return rx.mobile_and_tablet(
        rx.hstack(account_control(touch=True), nav_menu(), spacing="2", align="center"),
    )


def responsive_header_controls() -> rx.Component:
    """Controles da home, da /explorar e da /categorias: os do desktop (como
    sempre) a partir de 992 px e os do celular abaixo disso."""
    return rx.fragment(
        rx.desktop_only(header_auth_controls()),
        mobile_header_controls(),
    )


def _right_controls(show_donate: bool) -> rx.Component:
    """Coluna da direita do cabeçalho centralizado: no desktop, a conta e
    “Quero Doar”; abaixo de 992 px, só o ☰ (a conta fica no painel)."""
    return rx.flex(
        rx.desktop_only(header_auth_controls(show_donate)),
        rx.mobile_and_tablet(nav_menu()),
        class_name="site-header-controls",
        justify_self="end",
        align_items="center",
        min_width="0",
    )


def _home_logo(alt: str = "DoaFácil — início") -> rx.Component:
    """O logotipo da home (mesma largura e 72 px de altura), levando a /."""
    return rx.link(
        rx.image(
            src="/logo.svg",
            alt=alt,
            style={"width": LOGO_WIDTH},
            height="72px",
            object_fit="contain",
        ),
        href="/",
        aria_label="DoaFácil — início",
        display="inline-flex",
        align_items="center",
        min_height="44px",
        _focus_visible=FOCUS_RING,
    )


# Cabeçalho centralizado (rodada 4 do roteiro): largura toda da tela, com
# respiro fixo das bordas (16 px abaixo de 992 px e 32 px a partir daí; no
# Reflex 0.9.12 o `md` vale 62em) e o padding vertical e o logotipo da home.
CENTERED_HEADER_PADDING = rx.breakpoints(initial="12px 16px", md="12px 32px")


def _header_shell(
    left: rx.Component | None,
    show_donate: bool,
    class_name: str,
    **props: Any,
) -> rx.Component:
    """Faixa branca na largura toda da tela com a grade “Voltar | logotipo |
    controles”: o “Voltar” no canto esquerdo e a conta e “Quero Doar” no
    direito, a 16 px (celular) ou 32 px (a partir de 992 px) das bordas, e o
    logotipo centralizado na tela, com a altura e o padding vertical do
    cabeçalho da home (12 px em cima e embaixo, logotipo de 72 px)."""
    return rx.box(
        rx.grid(
            left if left is not None else rx.box(),
            _home_logo(),
            _right_controls(show_donate),
            grid_template_columns="1fr auto 1fr",
            align_items="center",
            column_gap="8px",
            width="100%",
            padding=CENTERED_HEADER_PADDING,
            box_sizing="border-box",
        ),
        class_name=class_name,
        width="100%",
        flex_shrink="0",
        background="white",
        **props,
    )


def site_header(back: rx.Component | None = None, show_donate: bool = True) -> rx.Component:
    """Cabeçalho das páginas com Voltar e do cadastro de doação: “Voltar” à
    esquerda (quando há), logotipo no centro e os controles do site à
    direita, com a sombra leve que essas páginas já tinham."""
    return _header_shell(
        back,
        show_donate,
        "site-header",
        box_shadow="0 2px 8px rgba(39, 39, 39, 0.06)",
    )


def back_link_header(
    href: str | rx.Var,
    label: str,
    color: str = GREEN_TEXT,
    show_donate: bool = True,
) -> rx.Component:
    """Cabeçalho branco com um link de voltar na linha do logotipo.

    Como nos frames chat-1, detalhes-doacao e perfil-doador do Figma: o link
    fica à esquerda, na mesma linha do logotipo centralizado, sem faixa
    própria. À direita ficam os controles do site (change
    navegacao-celular). Em telas estreitas aparece só a seta, com o rótulo
    acessível e 44 px de área de toque.
    """
    back = rx.link(
        rx.hstack(
            rx.icon("chevron-left", size=20),
            rx.text(
                label,
                display=rx.breakpoints(initial="none", sm="inline"),
            ),
            spacing="1",
            align="center",
        ),
        href=href,
        color=color,
        font_weight="600",
        aria_label=label,
        justify_self="start",
        # Área de toque confortável mesmo quando só a seta aparece.
        display="inline-flex",
        align_items="center",
        min_height="44px",
        min_width="44px",
    )
    return site_header(back, show_donate)


def back_home_header() -> rx.Component:
    """“Voltar ao início” (para /) em #166B3B. Usado no /chat e no detalhe."""
    return back_link_header("/", "Voltar ao início", GREEN_TEXT)


def logo_header() -> rx.Component:
    """Cabeçalho das páginas institucionais (Figma): o logotipo centralizado,
    levando à home, e os controles do site à direita (change
    navegacao-celular)."""
    return _header_shell(None, True, "institutional-header")


__all__ = [
    "HeaderState",
    "NavMenuState",
    "back_home_header",
    "back_link_header",
    "logo_header",
    "mobile_header_controls",
    "nav_menu",
    "nav_menu_items",
    "responsive_header_controls",
    "site_header",
]
