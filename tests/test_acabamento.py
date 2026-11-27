"""Change acabamento: volta à origem depois do login (next seguro), página
404, títulos e favicon, doação indisponível, chat vazio e contêiner."""

import unittest
from types import SimpleNamespace

from doafacil.rotas import current_path, login_redirect, login_url, safe_next, signup_url


def _router(path: str, query: str = "") -> SimpleNamespace:
    return SimpleNamespace(url=SimpleNamespace(path=path, query=query, query_parameters={}))


class SafeNextTests(unittest.TestCase):
    def test_accepts_internal_paths(self) -> None:
        for value in ("/", "/doacao/7", "/doacao/7/quem-doa", "/explorar?q=mesa&uf=SP", "/chat?conversa=3", "/login-x"):
            with self.subTest(value=value):
                self.assertEqual(safe_next(value), value)

    def test_rejects_external_or_unsafe(self) -> None:
        for value in (
            None,
            "",
            7,
            "https://evil.example",
            "http:/evil.example",
            "//evil.example",
            "///evil.example",
            "/\\evil.example",
            "\\\\evil.example",
            "javascript:alert(1)",
            "doacao/7",
            "/a b",
            "/a\tb",
            "/a\nb",
            "/a\x00b",
            "/a\x7fb",
            "/" + "a" * 600,
            "/login",
            "/login?next=/doacao/7",
            "/cadastro",
            "/recuperar-senha",
            "/verificar-email",
            "/nova-senha/x",
        ):
            with self.subTest(value=value):
                self.assertEqual(safe_next(value), "")

    def test_login_and_signup_urls(self) -> None:
        self.assertEqual(login_url("/doacao/7"), "/login?next=/doacao/7")
        self.assertEqual(login_url("/explorar?q=mesa&uf=SP"), "/login?next=/explorar%3Fq%3Dmesa%26uf%3DSP")
        self.assertEqual(login_url("https://evil.example"), "/login")
        self.assertEqual(login_url(""), "/login")
        self.assertEqual(signup_url("/doacao/7"), "/cadastro?next=/doacao/7")
        self.assertEqual(signup_url("//evil.example"), "/cadastro")

    def test_current_path_and_redirect(self) -> None:
        self.assertEqual(current_path(_router("/doacao/7")), "/doacao/7")
        self.assertEqual(current_path(_router("/explorar", "q=mesa")), "/explorar?q=mesa")
        self.assertEqual(current_path(None), "")
        self.assertIn("/login?next=/doacao/7", str(login_redirect(SimpleNamespace(router=_router("/doacao/7")))))
        # Estado sem router (testes antigos): /login puro.
        self.assertIn('"/login"', str(login_redirect(SimpleNamespace())))


if __name__ == "__main__":
    unittest.main()


class NoBareLoginRedirectTests(unittest.TestCase):
    """As páginas com sessão vão ao login com `next` (login_redirect); só o
    fluxo de autenticação (login.py) pode ir ao /login puro."""

    def test_pages_use_login_redirect(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parent.parent / "doafacil"
        for path in sorted(root.glob("*.py")):
            if path.name == "login.py":
                continue  # verificação e nova senha: fluxo de autenticação
            with self.subTest(module=path.name):
                self.assertNotIn('rx.redirect("/login")', path.read_text(encoding="utf-8"))


def _run_events(generator) -> list:
    import asyncio

    async def run():
        return [event async for event in generator]

    return asyncio.run(run())


def _query_router(path: str, **query: str) -> SimpleNamespace:
    from urllib.parse import urlencode

    return SimpleNamespace(url=SimpleNamespace(path=path, query=urlencode(query), query_parameters=query))


class LoginNextFlowTests(unittest.TestCase):
    ENV = {"XANO_AUTH_API_URL": "https://auth.example/api"}

    def _login(self, router) -> list:
        from unittest.mock import AsyncMock, patch

        from doafacil.login import LoginResult, LoginState

        state = SimpleNamespace(
            is_loading=False,
            error_message="",
            auth_token="",
            account_name="",
            password_reset_notice_pending=False,
            password_reset_notice_visible=False,
            signup_notice_pending=False,
            signup_notice_visible=False,
            router=router,
        )
        with (
            patch.dict("os.environ", self.ENV),
            patch("doafacil.login.request_login", new_callable=AsyncMock, return_value=LoginResult("tok", 1)),
            patch("doafacil.login.rx.redirect", side_effect=lambda path: f"redirect:{path}"),
        ):
            events = _run_events(LoginState.login.fn(state, {"email": "a@b.test", "password": "x"}))
        # O primeiro é o envio do “Entrando...”, antes do pedido (change
        # correcoes-revisao); aqui interessa só o destino do redirecionamento.
        self.assertIsNone(events[0])
        return events[1:]

    def test_login_returns_to_safe_next(self) -> None:
        self.assertEqual(self._login(_query_router("/login", next="/doacao/7")), ["redirect:/doacao/7"])
        self.assertEqual(
            self._login(_query_router("/login", next="/explorar?q=mesa")), ["redirect:/explorar?q=mesa"]
        )

    def test_login_ignores_unsafe_next(self) -> None:
        for bad in ("https://evil.example", "//evil.example", "/\\evil.example", "/login"):
            with self.subTest(next=bad):
                self.assertEqual(self._login(_query_router("/login", next=bad)), ["redirect:/"])
        self.assertEqual(self._login(_query_router("/login")), ["redirect:/"])

    def test_signup_carries_next_to_login(self) -> None:
        from unittest.mock import AsyncMock, patch

        from doafacil.login import LoginState

        state = SimpleNamespace(
            is_loading=False,
            error_message="",
            auth_token="",
            account_name="",
            signup_password_visible=False,
            signup_confirmation_visible=False,
            password_reset_notice_pending=False,
            password_reset_notice_visible=False,
            signup_notice_pending=False,
            signup_notice_visible=False,
            router=_query_router("/cadastro", next="/doacao/7"),
        )
        form = {
            "name": "Pessoa Teste",
            "email": "pessoa@example.test",
            "password": "senha123",
            "confirm_password": "senha123",
            "city": "Recife",
            "state": "PE",
        }
        with (
            patch.dict("os.environ", self.ENV),
            patch("doafacil.login.request_signup", new_callable=AsyncMock),
        ):
            _run_events(LoginState.signup.fn(state, form))
        self.assertEqual(state._auth_next, "/doacao/7")

        verify = SimpleNamespace(
            recovery_is_loading=False,
            recovery_error_message="",
            verification_flow="signup",
            signup_email="pessoa@example.test",
            _signup_password="senha123",
            recovery_resend_seconds=8,
            signup_notice_pending=False,
            signup_notice_visible=False,
            auth_token="",
            account_name="",
            _auth_next=state._auth_next,
        )
        with (
            patch.dict("os.environ", self.ENV),
            patch("doafacil.login.request_signup_verification", new_callable=AsyncMock),
            patch("doafacil.login.rx.redirect", side_effect=lambda path: f"redirect:{path}"),
        ):
            events = _run_events(LoginState.verify_recovery_code.fn(verify, {"code": "123456"}))
        self.assertIn("redirect:/login?next=/doacao/7", events)
        self.assertEqual(verify._auth_next, "")

    def test_links_carry_next(self) -> None:
        from doafacil.login import LoginState

        state = SimpleNamespace(router=_query_router("/doacao/7"))
        self.assertEqual(LoginState.computed_vars["login_href"].fget(state), "/login?next=/doacao/7")
        on_login = SimpleNamespace(router=_query_router("/login", next="/doacao/7"))
        self.assertEqual(LoginState.computed_vars["signup_href"].fget(on_login), "/cadastro?next=/doacao/7")
        on_signup = SimpleNamespace(router=_query_router("/cadastro", next="/doacao/7"))
        self.assertEqual(LoginState.computed_vars["login_from_signup_href"].fget(on_signup), "/login?next=/doacao/7")
        # Numa tela de autenticação, o “Entrar” vai ao /login puro.
        self.assertEqual(LoginState.computed_vars["login_href"].fget(on_login), "/login")


ASSETS = __import__("pathlib").Path(__file__).resolve().parent.parent / "assets"
FAVICON_FILES = ("favicon-32.png", "apple-touch-icon.png")


class FaviconTests(unittest.TestCase):
    def test_head_declares_png_icons(self) -> None:
        from doafacil.doafacil import FAVICON_HEAD

        rendered = " ".join(str(link) for link in FAVICON_HEAD)
        self.assertIn('href:"/favicon-32.png"', rendered)
        self.assertIn('sizes:"32x32"', rendered)
        self.assertIn('rel:"apple-touch-icon"', rendered)
        self.assertIn('href:"/apple-touch-icon.png"', rendered)
        self.assertIn('sizes:"180x180"', rendered)

    def test_pymupdf_only_in_dev_requirements(self) -> None:
        root = ASSETS.parent
        self.assertNotIn("pymupdf", (root / "requirements.txt").read_text(encoding="utf-8").lower())
        self.assertIn("pymupdf", (root / "requirements-dev.txt").read_text(encoding="utf-8").lower())

    @unittest.skipUnless(
        all((ASSETS / name).is_file() for name in FAVICON_FILES),
        "rode scripts/gerar_favicon.py (pip install -r requirements-dev.txt)",
    )
    def test_generated_files(self) -> None:
        from PIL import Image

        with Image.open(ASSETS / "favicon.ico") as ico:
            self.assertEqual(ico.format, "ICO")
            self.assertTrue({(16, 16), (32, 32), (48, 48)} <= set(ico.info.get("sizes", set())))
        with Image.open(ASSETS / "favicon-32.png") as png:
            self.assertEqual((png.format, png.size), ("PNG", (32, 32)))
            alpha = png.convert("RGBA").getchannel("A")
            # tobytes(): um byte por pixel no canal "L" (o getdata sai no Pillow 14).
            transparent = sum(1 for value in alpha.tobytes() if value < 16)
            self.assertLess(transparent / (32 * 32), 0.6)  # o símbolo ocupa o ícone
        with Image.open(ASSETS / "apple-touch-icon.png") as touch:
            self.assertEqual((touch.format, touch.size), ("PNG", (180, 180)))
            self.assertEqual(touch.convert("RGBA").getextrema()[3][0], 255)  # opaco


class NotFoundAndTitlesTests(unittest.TestCase):
    def test_every_page_has_doafacil_title(self) -> None:
        from doafacil.doafacil import app

        self.assertGreaterEqual(len(app._unevaluated_pages), 23)
        for route, page in app._unevaluated_pages.items():
            with self.subTest(route=route):
                title = str(page.title or "")
                self.assertTrue(title.endswith(" | DoaFácil"), title)
                self.assertGreater(len(title), len(" | DoaFácil"))
                self.assertNotIn("Doafacil", title)

    def test_custom_404_registered(self) -> None:
        from doafacil.doafacil import app
        from doafacil.login import LoginState

        page = app._unevaluated_pages["404"]
        self.assertEqual(page.title, "Página não encontrada | DoaFácil")
        handlers = page.on_load if isinstance(page.on_load, list) else [page.on_load]
        self.assertIn(LoginState.load_account.fn, [handler.fn for handler in handlers])

    def test_404_content(self) -> None:
        from doafacil.nao_encontrada import NOT_FOUND_TEXT, not_found_page

        rendered = str(not_found_page())
        self.assertIn('className:"site-header"', rendered)  # cabeçalho comum
        self.assertIn('as:"h1"', rendered)
        self.assertIn(__import__("json").dumps("Página não encontrada"), rendered)
        self.assertIn(__import__("json").dumps(NOT_FOUND_TEXT), rendered)
        self.assertIn('to:"/"', rendered)
        self.assertIn('to:"/explorar"', rendered)
        self.assertIn(__import__("json").dumps("Voltar ao início"), rendered)
        self.assertIn(__import__("json").dumps("Explorar doações"), rendered)
        self.assertIn("page-fade-enter", rendered)
        self.assertGreaterEqual(rendered.count('["minHeight"] : "44px"'), 2)
        for english in ("Not Found", "not found", "404"):
            self.assertNotIn(english, rendered)


class UnavailableChatAndContainerTests(unittest.TestCase):
    def test_unavailable_donation_explains_and_offers_paths(self) -> None:
        import json

        from doafacil.detalhe_doacao import (
            DONATION_NOT_FOUND_MESSAGE,
            DONATION_UNAVAILABLE_TEXT,
            donation_detail_page,
        )

        rendered = str(donation_detail_page())
        title_at = rendered.index(json.dumps(DONATION_NOT_FOUND_MESSAGE))
        text_at = rendered.index(json.dumps(DONATION_UNAVAILABLE_TEXT))
        explore_at = rendered.index('className:"detail-unavailable-explore"')
        home_at = rendered.index('className:"detail-unavailable-home"')
        self.assertLess(title_at, text_at)
        self.assertLess(text_at, explore_at)
        self.assertLess(explore_at, home_at)
        explore = rendered[explore_at : explore_at + 900]
        home = rendered[home_at : home_at + 900]
        self.assertIn(json.dumps("Ver outras doações"), explore)
        self.assertIn('to:"/explorar"', explore)
        self.assertIn(json.dumps("Voltar ao início"), home)
        self.assertIn('to:"/"', home)
        for link in (explore, home):
            self.assertIn('["minHeight"] : "44px"', link)
        # Não diz qual foi o caso.
        self.assertIn("reservada, conclu", DONATION_UNAVAILABLE_TEXT)

    def test_empty_chat_offers_explore(self) -> None:
        import json

        from doafacil.chat import EMPTY_LIST_MESSAGE, chat_page

        rendered = str(chat_page())
        message_at = rendered.index(json.dumps(EMPTY_LIST_MESSAGE))
        link_at = rendered.index('className:"chat-empty-explore"')
        self.assertLess(message_at, link_at)
        link = rendered[link_at : link_at + 800]
        self.assertIn(json.dumps("Explorar doações"), link)
        self.assertIn('to:"/explorar"', link)
        self.assertIn('["minHeight"] : "44px"', link)

    def test_three_pages_use_the_my_donations_container(self) -> None:
        from doafacil.detalhe_doacao import donation_detail_page
        from doafacil.editar_perfil import edit_profile_page
        from doafacil.perfil_doador import donor_profile_page

        for name, page in (
            ("perfil de quem doa", donor_profile_page),
            ("detalhe", donation_detail_page),
            ("Editar perfil", edit_profile_page),
        ):
            with self.subTest(pagina=name):
                rendered = str(page())
                self.assertIn('["maxWidth"] : "1200px"', rendered)
                self.assertIn('["paddingInlineStart"] : "16px"', rendered)
                self.assertIn('["paddingInlineStart"] : "24px"', rendered)
                for old in ('"1396px"', '"1440px"', '"1236px"'):
                    self.assertNotIn(old, rendered)

    def test_detail_grid_unchanged(self) -> None:
        from doafacil.detalhe_doacao import donation_detail_page

        rendered = str(donation_detail_page())
        for expected in (
            '["gridTemplateColumns"] : "minmax(0, 1fr)"',
            '["gridTemplateColumns"] : "minmax(0, 2.6fr) minmax(280px, 1fr)"',
            "'gallery' 'summary' 'title' 'details' 'location' 'donor'",
            "'main side'",
        ):
            self.assertIn(expected, rendered)
