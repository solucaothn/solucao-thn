"""Change navegacao-celular (spec site-navigation): o menu do celular (☰ e
painel) e o cabeçalho comum com os controles do site."""

import re
import unittest

from doafacil import navegacao as nav
from doafacil.cadastro import signup_page
from doafacil.cadastro_doacao import donation_creation_page
from doafacil.categorias import categories_page
from doafacil.chat import ChatState, chat_page
from doafacil.detalhe_doacao import donation_detail_page
from doafacil.doafacil import app, index
from doafacil.editar_perfil import edit_profile_page
from doafacil.explorar import explore_page
from doafacil.institucional import (
    about_page,
    contact_page,
    help_category_page,
    help_page,
    privacy_page,
    security_page,
    terms_page,
)
from doafacil.login import LoginState, login_page
from doafacil.minhas_doacoes import edit_donation_page, my_donations_page
from doafacil.perfil_doador import donor_profile_page
from doafacil.recuperacao_senha import new_password_page, request_recovery_page, verify_recovery_page
from doafacil.rodape import HOW_IT_WORKS_ANCHOR

TRIGGER = '"aria-label":"Abrir menu"'
DESKTOP_ONLY = '["@media screen and (min-width: 62em)"] : ({ ["display"] : "block" })'
MOBILE_ONLY = '["@media screen and (min-width: 62em)"] : ({ ["display"] : "none" })'

# Páginas com o cabeçalho centralizado e o menu (spec site-navigation).
CENTERED_PAGES = {
    "detalhe": donation_detail_page,
    "perfil de quem doa": donor_profile_page,
    "chat": chat_page,
    "minhas doações": my_donations_page,
    "editar doação": edit_donation_page,
    "editar perfil": edit_profile_page,
    "cadastro de doação": donation_creation_page,
    "dúvidas": help_page,
    "dúvidas por categoria": help_category_page,
    "segurança": security_page,
    "termos": terms_page,
    "privacidade": privacy_page,
    "quem somos": about_page,
    "contato": contact_page,
}
AUTH_PAGES = {
    "login": login_page,
    "cadastro": signup_page,
    "recuperar senha": request_recovery_page,
    "verificar e-mail": verify_recovery_page,
    "nova senha": new_password_page,
}


def _walk(component) -> list:
    nodes = [component]
    for child in getattr(component, "children", []) or []:
        nodes.extend(_walk(child))
    return nodes


def _session_cond(component):
    """O rx.cond com sessão / sem sessão do painel."""
    return next(
        node
        for node in _walk(component)
        if type(node).__name__ == "Cond" and "auth_token" in str(getattr(node, "cond", ""))
    )


def _links(rendered: str) -> list[str]:
    return re.findall(r'to:"([^"]*)"', rendered)


class NavMenuPanelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.menu = str(nav.nav_menu())
        self.items = str(nav.nav_menu_items())

    def test_trigger_label_size_and_dialog(self) -> None:
        trigger = str(nav.nav_menu_trigger())
        self.assertIn(TRIGGER, trigger)
        self.assertIn('"aria-haspopup":"dialog"', trigger)
        for prop in ('["width"] : "44px"', '["height"] : "44px"', '["minWidth"] : "44px"', '["minHeight"] : "44px"'):
            self.assertIn(prop, trigger)
        self.assertIn("LucideMenu", trigger)

    def test_panel_is_a_left_dialog_with_title_and_close(self) -> None:
        self.assertIn("RadixThemesDialog.Root", self.menu)
        self.assertIn("RadixThemesDialog.Title", self.menu)
        self.assertIn('"Menu"', self.menu)
        self.assertIn('"aria-label":"Fechar"', self.menu)
        self.assertIn("RadixThemesDialog.Description", self.menu)
        self.assertIn('className:"nav-menu-panel"', self.menu)
        self.assertIn('["left"] : "0"', self.menu)
        self.assertIn('["width"] : "min(360px, 100vw)"', self.menu)
        self.assertIn('["maxWidth"] : "min(360px, 100vw)"', self.menu)
        # Aberto/fechado pelo estado, para os itens fecharem o painel.
        self.assertIn("nav_menu_state.open", self.menu)

    def test_public_items_in_order(self) -> None:
        links = _links(self.items)
        self.assertEqual(links[:4], ["/explorar", "/#como-funciona", "/categorias", "/cadastro-doacao"])
        for label in ("Explorar doa\\u00e7\\u00f5es", "Como funciona", "Categorias", "Quero Doar"):
            self.assertIn(f'"{label}"', self.items)
        self.assertEqual(nav.HOW_IT_WORKS_ANCHOR, HOW_IT_WORKS_ANCHOR)

    def test_session_and_visitor_items(self) -> None:
        cond = _session_cond(nav.nav_menu_items())
        authenticated, visitor = (str(child) for child in cond.children)
        self.assertEqual(_links(authenticated), ["/minhas-doacoes", "/chat", "/perfil/editar"])
        for label in ("Minhas doa\\u00e7\\u00f5es", "Mensagens", "Editar perfil", "Sair"):
            self.assertIn(f'"{label}"', authenticated)
        self.assertIn("account_name", authenticated)  # nome da conta
        self.assertIn("LucideUser", authenticated)  # avatar (foto, inicial ou ícone)
        self.assertNotIn("Entrar", authenticated)
        self.assertEqual(_links(visitor), ["/login"])
        self.assertIn('"Entrar"', visitor)
        for label in ("Mensagens", "Sair", "Minhas doa"):
            self.assertNotIn(label, visitor)

    def test_messages_shows_loaded_unread_total_without_query(self) -> None:
        item = str(nav._messages_item())
        self.assertIn("unread_total_text", item)
        self.assertIn("unread_link_label", item)  # “Mensagens, N não lidas”
        self.assertIn("chat-unread-badge", item)
        self.assertNotIn("load_unread_total", str(nav.nav_menu()))

    def test_items_close_panel_and_logout_ends_session(self) -> None:
        nodes = _walk(nav.nav_menu_items())
        items = [n for n in nodes if "nav-menu-item" in str(getattr(n, "class_name", "") or "")]
        self.assertEqual(len({id(n) for n in items}), 4 + 4 + 1)  # públicos + conta + Entrar
        for item in items:
            with self.subTest(item=str(item)[:60]):
                self.assertIn("NavMenuState.close", str(item.event_triggers.get("on_click")))
        logout = next(n for n in items if "nav-menu-logout" in str(n.class_name))
        self.assertIn("LoginState.logout", str(logout.event_triggers["on_click"]))

    def test_items_have_touch_height(self) -> None:
        self.assertGreaterEqual(self.items.count('["minHeight"] : "48px"'), 9)


class SiteHeaderTests(unittest.TestCase):
    def test_centered_header_columns_and_responsive_controls(self) -> None:
        header = nav.back_link_header("/x", "Voltar", "#007A42")
        rendered = str(header)
        self.assertEqual(header.class_name, "site-header")
        self.assertIn('["gridTemplateColumns"] : "1fr auto 1fr"', rendered)
        self.assertIn('to:"/x"', rendered)
        self.assertIn('className:"site-header-controls"', rendered)
        controls = rendered[rendered.index('className:"site-header-controls"') :]
        desktop, mobile = controls.index(DESKTOP_ONLY), controls.index(MOBILE_ONLY)
        # Desktop: conta e “Quero Doar”; celular: só o ☰.
        self.assertIn("home-account-menu", controls[:mobile])
        self.assertIn('"Quero Doar"', controls[:mobile])
        self.assertIn(TRIGGER, controls[mobile:])
        self.assertNotIn("home-account-menu", controls[mobile:].split("nav-menu-panel")[0])
        self.assertLess(desktop, mobile)

    def test_without_donate(self) -> None:
        rendered = str(nav.site_header(show_donate=False))
        bar = rendered.split("nav-menu-panel")[0]
        self.assertNotIn('"Quero Doar"', bar)
        self.assertIn("home-account-menu", bar)
        self.assertIn(TRIGGER, bar)

    def test_back_home_header_is_a_back_link_header(self) -> None:
        self.assertEqual(str(nav.back_home_header()), str(nav.back_link_header("/", "Voltar ao início", "#166B3B")))

    def test_logo_header_keeps_centered_logo(self) -> None:
        rendered = str(nav.logo_header())
        self.assertIn('className:"institutional-header"', rendered)
        self.assertIn('"aria-label":"DoaF\\u00e1cil \\u2014 in\\u00edcio"', rendered)
        self.assertIn('["gridTemplateColumns"] : "1fr auto 1fr"', rendered)
        self.assertIn(TRIGGER, rendered)


class PagesTests(unittest.TestCase):
    def test_centered_pages_have_menu_and_desktop_controls(self) -> None:
        for name, page in CENTERED_PAGES.items():
            with self.subTest(page=name):
                rendered = str(page())
                self.assertEqual(rendered.count(TRIGGER), 1)
                self.assertIn('className:"site-header-controls"', rendered)
                self.assertIn("home-account-menu", rendered)

    def test_donation_creation_without_donate_in_header(self) -> None:
        page = donation_creation_page()
        header = str(page.children[0]).split("nav-menu-panel")[0]
        self.assertNotIn('"Quero Doar"', header)
        # Rodada 3: a seta “Voltar ao início” fica na linha do logotipo.
        self.assertIn('"aria-label":"Voltar ao in\\u00edcio"', str(page.children[0]))
        self.assertNotIn('"aria-label":"Voltar ao in\\u00edcio"', str(page.children[1]))

    def test_chat_header_same_as_other_back_pages(self) -> None:
        chat_header = str(chat_page().children[0])
        self.assertEqual(chat_header, str(nav.back_home_header()))
        self.assertIn('"aria-label":"Voltar ao in\\u00edcio"', chat_header)

    def test_home_explore_and_categories_keep_desktop_and_add_mobile_bar(self) -> None:
        for name, page in (("home", index), ("explorar", explore_page), ("categorias", categories_page)):
            with self.subTest(page=name):
                rendered = str(page())
                self.assertEqual(rendered.count(TRIGGER), 1)
                # Desktop: conta e “Quero Doar”, como antes.
                desktop = rendered[rendered.index(DESKTOP_ONLY) :]
                self.assertIn('"Quero Doar"', desktop)
        # Os links do menu da home continuam só no desktop.
        header = str(index().children[0].children[0])
        links_box = header[header.index(DESKTOP_ONLY) :]
        self.assertIn("home-categories-trigger", links_box)

    def test_mobile_bar_has_account_and_menu_without_donate(self) -> None:
        bar = str(nav.mobile_header_controls())
        self.assertIn(MOBILE_ONLY, bar)
        before_panel = bar.split("nav-menu-panel")[0]
        self.assertIn("home-account-menu", before_panel)
        self.assertIn('"Entrar"', before_panel)
        self.assertIn('["minHeight"] : "44px"', before_panel)
        self.assertNotIn('"Quero Doar"', before_panel)
        self.assertIn(TRIGGER, before_panel)

    def test_auth_pages_have_no_menu(self) -> None:
        for name, page in AUTH_PAGES.items():
            with self.subTest(page=name):
                rendered = str(page())
                self.assertNotIn(TRIGGER, rendered)
                self.assertNotIn("home-account-menu", rendered)
                self.assertNotIn("site-header-controls", rendered)


class RoutesTests(unittest.TestCase):
    def _handlers(self, route: str) -> list:
        on_load = app._unevaluated_pages[route].on_load
        on_load = on_load if isinstance(on_load, list) else [on_load]
        return [handler.fn for handler in on_load]

    def test_pages_with_header_load_account_once_per_session(self) -> None:
        for route in (
            "doacao/[id]",
            "doacao/[id]/quem-doa",
            "minhas-doacoes",
            "minhas-doacoes/[id]/editar",
            "perfil/editar",
            "chat",
            "cadastro-doacao",
        ):
            with self.subTest(route=route):
                self.assertIn(LoginState.load_account.fn, self._handlers(route))

    def test_no_new_unread_queries(self) -> None:
        for route in (
            "doacao/[id]",
            "doacao/[id]/quem-doa",
            "minhas-doacoes",
            "minhas-doacoes/[id]/editar",
            "perfil/editar",
            "chat",
            "cadastro-doacao",
        ):
            with self.subTest(route=route):
                self.assertNotIn(ChatState.load_unread_total.fn, self._handlers(route))


if __name__ == "__main__":
    unittest.main()


class HeaderContainerTests(unittest.TestCase):
    """Rodada 1 do roteiro: o cabeçalho centralizado usa o contêiner, as
    margens, o padding e o logotipo da home; o /chat não corta o logotipo."""

    def test_full_width_with_fixed_edges_and_home_logo(self) -> None:
        # Rodada 4: largura toda, “Voltar” e controles a 16 px (celular) ou
        # 32 px (a partir de 992 px) das bordas, e o padding vertical e o
        # logotipo da home.
        home = str(index().children[0].children[0])
        for name, header in (
            ("site_header", nav.site_header()),
            ("back_link_header", nav.back_link_header("/x", "Voltar")),
            ("back_home_header (detalhe e /chat)", nav.back_home_header()),
            ("logo_header (institucionais)", nav.logo_header()),
        ):
            with self.subTest(header=name):
                rendered = str(header)
                grid = rendered[rendered.index("RadixThemesGrid") :]
                grid = grid[: grid.index("})},") + 3]
                self.assertNotIn("maxWidth", grid)
                self.assertIn('["width"] : "100%"', grid)
                self.assertIn('["boxSizing"] : "border-box"', grid)
                self.assertIn('(min-width: 0px)"] : ({ ["padding"] : "12px 16px" })', grid)
                self.assertIn('(min-width: 62em)"] : ({ ["padding"] : "12px 32px" })', grid)
                self.assertIn('["gridTemplateColumns"] : "1fr auto 1fr"', grid)
                # Mesmo padding vertical (12 px) e logotipo (72 px, 190 px de
                # largura a partir de 992 px) da home: sem corte em cima.
                self.assertIn('["padding"] : "12px 16px"', home)
                self.assertIn('["height"] : "72px"', rendered)
                self.assertIn('["height"] : "72px"', home)
                self.assertIn('"190px"', rendered)
                self.assertNotIn('"140px"', rendered)

    def test_home_explore_and_categories_headers_unchanged(self) -> None:
        # Continuam no contêiner de 1200 px com 24 px a partir de 992 px.
        home = str(index().children[0].children[0])
        self.assertIn('["maxWidth"] : "1200px"', home)
        self.assertIn('(min-width: 62em)"] : ({ ["padding"] : "12px 24px" })', home)
        explore = str(explore_page())
        self.assertIn('["maxWidth"] : "1200px"', explore)

    def test_chat_area_fills_the_rest_of_the_screen(self) -> None:
        rendered = str(chat_page())
        self.assertNotIn("calc(100vh - 64px)", rendered)
        self.assertIn('["height"] : "100dvh"', rendered)
        self.assertIn('["flexDirection"] : "column"', rendered)
        area = rendered[rendered.index('className:"page-fade-enter"') :][:400]
        self.assertIn('["flex"] : "1"', area)
        self.assertIn('["minHeight"] : "0"', area)
