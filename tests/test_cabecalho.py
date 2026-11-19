"""Cabeçalho compartilhado (change explorar-categorias): o menu da conta não
calcula a inicial no navegador, o que quebrava a página com o nome ainda
indefinido (“Cannot read properties of undefined (reading 'toUpperCase')”)."""

import unittest
from types import SimpleNamespace

from doafacil.cabecalho import HeaderState, account_menu


class AccountInitialTests(unittest.TestCase):
    def _initial(self, name: object) -> str:
        return HeaderState.computed_vars["account_initial"].fget(SimpleNamespace(account_name=name))

    def test_initial_from_name(self) -> None:
        self.assertEqual(self._initial("ana"), "A")
        self.assertEqual(self._initial("  Érica "), "É")
        self.assertEqual(self._initial("Minha conta"), "M")

    def test_no_name_means_no_initial(self) -> None:
        for name in ("", "   ", None, 5):
            with self.subTest(name=name):
                self.assertEqual(self._initial(name), "")


class AccountMenuTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rendered = str(account_menu())

    def test_initial_comes_from_the_server(self) -> None:
        # Nada de indexar ou pôr em maiúsculas o nome no navegador.
        self.assertNotIn("toUpperCase", self.rendered)
        self.assertNotIn('account_name_rx_state_?.at?.(0)', self.rendered)
        self.assertIn("header_state.account_initial", self.rendered)

    def test_person_icon_without_name(self) -> None:
        self.assertIn("LucideUser", self.rendered)
        self.assertIn('"aria-label":("Menu da conta de "+', self.rendered)
        self.assertIn('["minHeight"] : "44px"', self.rendered)

    def test_home_explore_and_categories_use_the_safe_menu(self) -> None:
        from doafacil.doafacil import categories_page, explore_page, index

        for name, page in (("home", index), ("explorar", explore_page), ("categorias", categories_page)):
            with self.subTest(page=name):
                rendered = str(page())
                self.assertIn("header_state.account_initial", rendered)
                self.assertNotIn("toUpperCase", rendered)


if __name__ == "__main__":
    unittest.main()


class AccountPhotoTests(unittest.TestCase):
    """A foto de perfil no círculo do menu (roteiro 5.4 da change
    paginas-institucionais): foto quando houver; senão, inicial ou ícone."""

    def setUp(self) -> None:
        self.rendered = str(account_menu())

    def test_photo_first_then_initial_then_icon(self) -> None:
        photo = self.rendered.index("account_photo")
        initial = self.rendered.index("header_state.account_initial")
        self.assertLess(photo, initial)
        self.assertIn('className:"home-account-photo"', self.rendered)
        self.assertIn('alt:""', self.rendered)  # o nome já está no rótulo do botão
        self.assertIn('["objectFit"] : "cover"', self.rendered)
        self.assertIn('["overflow"] : "hidden"', self.rendered)
        self.assertIn("LucideUser", self.rendered)


def _load(state: object) -> None:
    import asyncio

    from doafacil.login import LoginState

    asyncio.run(LoginState.load_account.fn(state))


class LoadAccountPhotoTests(unittest.TestCase):
    """Uma requisição a mais (auth/profile), só na primeira carga do token."""

    def _state(self, **values: object) -> SimpleNamespace:
        base = {"auth_token": "tok", "account_name": "", "account_photo": "", "_account_token": ""}
        return SimpleNamespace(**{**base, **values})

    def _patches(self, photo: object = "https://x.example/f.jpg"):
        from unittest.mock import AsyncMock, patch

        return (
            patch("doafacil.login.auth_me_endpoint", return_value="https://a.example/auth/me"),
            patch("doafacil.login.auth_profile_endpoint", return_value="https://a.example/auth/profile"),
            patch("doafacil.login.request_authenticated_name", new_callable=AsyncMock, return_value="Ana"),
            patch(
                "doafacil.login.request_account_photo",
                new_callable=AsyncMock,
                **({"side_effect": photo} if isinstance(photo, Exception) else {"return_value": photo}),
            ),
        )

    def test_first_load_fetches_photo_once(self) -> None:
        state = self._state()
        me, profile, name, photo = self._patches()
        with me, profile, name, photo as request:
            _load(state)
            _load(state)
        self.assertEqual(request.await_count, 1)
        self.assertEqual(state.account_photo, "https://x.example/f.jpg")
        self.assertEqual(state.account_name, "Ana")

    def test_new_token_fetches_again(self) -> None:
        state = self._state(account_photo="https://x.example/velha.jpg", _account_token="outro")
        me, profile, name, photo = self._patches("")
        with me, profile, name, photo as request:
            _load(state)
        self.assertEqual(request.await_count, 1)
        self.assertEqual(state.account_photo, "")

    def test_rejected_token_clears_photo(self) -> None:
        from doafacil.login import AuthTokenRejectedError

        state = self._state()
        me, profile, name, photo = self._patches(AuthTokenRejectedError())
        with me, profile, name, photo:
            _load(state)
        self.assertEqual((state.auth_token, state.account_photo, state._account_token), ("", "", ""))

    def test_no_token_and_logout_clear_photo(self) -> None:
        from doafacil.login import LoginState

        state = self._state(auth_token="", account_photo="https://x.example/f.jpg", _account_token="tok")
        _load(state)
        self.assertEqual((state.account_photo, state._account_token), ("", ""))
        state = self._state(account_photo="https://x.example/f.jpg", _account_token="tok")
        state.password_reset_notice_pending = state.password_reset_notice_visible = False
        state.signup_notice_pending = state.signup_notice_visible = False
        LoginState.logout.fn(state)
        self.assertEqual((state.account_photo, state._account_token), ("", ""))


class AccountOncePerSessionTests(LoadAccountPhotoTests):
    """Change navegacao-celular: nome e foto uma vez por sessão (token), por
    causa do limite do plano grátis do Xano (10 pedidos a cada 20 s)."""

    def test_many_pages_one_request_each(self) -> None:
        state = self._state()
        me, profile, name, photo = self._patches()
        with me, profile, name as name_request, photo as photo_request:
            for _ in range(5):  # cinco páginas seguidas
                _load(state)
        self.assertEqual(name_request.await_count, 1)
        self.assertEqual(photo_request.await_count, 1)
        self.assertEqual(state._account_token, "tok")

    def test_new_login_loads_again(self) -> None:
        state = self._state(account_name="Ana", _account_token="tok")
        me, profile, name, photo = self._patches()
        with me, profile, name as name_request, photo:
            _load(state)
            self.assertEqual(name_request.await_count, 0)
            state.auth_token = "novo"
            _load(state)
        self.assertEqual(name_request.await_count, 1)
        self.assertEqual(state._account_token, "novo")

    def test_transient_failure_does_not_mark_and_retries(self) -> None:
        from unittest.mock import AsyncMock, patch

        from doafacil.login import ACCOUNT_FALLBACK_NAME, AuthAccountUnavailableError

        state = self._state()
        me, profile, _name, photo = self._patches()
        failing = patch(
            "doafacil.login.request_authenticated_name",
            new_callable=AsyncMock,
            side_effect=AuthAccountUnavailableError(),
        )
        with me, profile, failing as name_request, photo:
            _load(state)
            _load(state)
        self.assertEqual(name_request.await_count, 2)
        self.assertEqual(state.account_name, ACCOUNT_FALLBACK_NAME)
        self.assertEqual(state._account_token, "")

    def test_profile_edit_updates_without_request(self) -> None:
        import inspect

        from doafacil import editar_perfil

        # O Editar perfil grava o nome e a foto novos direto no estado da conta.
        source = inspect.getsource(editar_perfil)
        self.assertIn("self.account_name = first_name_of(", source)
        self.assertIn("self.account_photo = url", source)
        state = self._state(account_name="Ana", _account_token="tok")
        state.account_name = "Bia"  # nome salvo no Editar perfil
        me, profile, name, photo = self._patches()
        with me, profile, name as name_request, photo as photo_request:
            _load(state)
        self.assertEqual((name_request.await_count, photo_request.await_count), (0, 0))
        self.assertEqual(state.account_name, "Bia")


class RequestAccountPhotoTests(unittest.TestCase):
    def _run(self, response: object):
        import asyncio
        from unittest.mock import AsyncMock

        from doafacil.login import request_account_photo

        client = SimpleNamespace(get=AsyncMock(side_effect=response) if isinstance(response, Exception) else AsyncMock(return_value=response))
        return asyncio.run(request_account_photo(client, "https://a.example/auth/profile", "tok"))

    def _response(self, status: int, payload: object):
        import httpx

        return httpx.Response(status, json=payload, request=httpx.Request("GET", "https://a.example/auth/profile"))

    def test_photo_url_or_empty(self) -> None:
        self.assertEqual(self._run(self._response(200, {"photo": "https://x.example/f.jpg"})), "https://x.example/f.jpg")
        self.assertEqual(self._run(self._response(200, {"photo": None})), "")

    def test_failures_fall_back_to_initial(self) -> None:
        import httpx

        for response in (
            self._response(500, {}),
            self._response(200, {"photo": "javascript:alert(1)"}),
            self._response(200, ["x"]),
            httpx.ConnectError("x"),
        ):
            with self.subTest(response=response):
                self.assertEqual(self._run(response), "")

    def test_rejected_token(self) -> None:
        from doafacil.login import AuthTokenRejectedError

        with self.assertRaises(AuthTokenRejectedError):
            self._run(self._response(401, {}))
