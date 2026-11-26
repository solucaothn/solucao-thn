import asyncio
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import reflex as rx

from doafacil.doafacil import FIELD_PLACEHOLDER_SELECTOR, app, index
from doafacil.login import (
    ACCOUNT_FALLBACK_NAME,
    AUTH_API_ENV,
    AUTH_LOGIN_PATH,
    AUTH_ME_PATH,
    AuthAccountUnavailableError,
    AuthTokenRejectedError,
    InvalidCredentialsError,
    LoginConfigurationError,
    LoginResult,
    LoginState,
    LoginUnavailableError,
    auth_me_endpoint,
    auth_login_endpoint,
    login_page,
    login_error_message,
    request_login,
    request_authenticated_name,
)


def _component_nodes(component: object) -> list[object]:
    nodes: list[object] = []

    def collect(value: object) -> None:
        if hasattr(value, "tag") or hasattr(value, "component_name"):
            nodes.append(value)
        if hasattr(value, "children"):
            collect(value.children)
        elif isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return nodes


def _component_text(component: object) -> str:
    values: list[str] = []

    def collect(value: object) -> None:
        if hasattr(value, "contents"):
            text = value.contents
            if isinstance(text, str):
                values.append(text)
            elif type(text).__name__ == "LiteralStringVar":
                values.append(text._var_value)
        if hasattr(value, "children"):
            collect(value.children)
        elif isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return " ".join(values)


class LoginClientTests(unittest.TestCase):
    def test_auth_endpoint_uses_valid_environment_url_and_trims_slashes(self) -> None:
        with patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api/"}):
            self.assertEqual(
                auth_login_endpoint(),
                f"https://auth.example/api{AUTH_LOGIN_PATH}",
            )

    def test_auth_endpoint_rejects_missing_or_invalid_environment_url(self) -> None:
        for value in ("", "not-a-url", "ftp://auth.example", "https:///missing"):
            with self.subTest(configured=value):
                with patch.dict(os.environ, {AUTH_API_ENV: value}):
                    with self.assertRaises(LoginConfigurationError):
                        auth_login_endpoint()

        with patch.dict(os.environ):
            os.environ.pop(AUTH_API_ENV, None)
            with self.assertRaises(LoginConfigurationError):
                auth_login_endpoint()

    def test_auth_me_endpoint_uses_the_authentication_base_url(self) -> None:
        with patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api/"}):
            self.assertEqual(
                auth_me_endpoint(),
                f"https://auth.example/api{AUTH_ME_PATH}",
            )

    def test_authenticated_name_request_uses_bearer_and_keeps_only_first_name(
        self,
    ) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, AUTH_ME_PATH)
            self.assertEqual(
                request.headers["Authorization"], "Bearer private-token"
            )
            return httpx.Response(
                200,
                json={
                    "name": "Maria da Silva",
                    "email": "private@example.test",
                    "role": "user",
                },
                request=request,
            )

        async def run() -> str:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await request_authenticated_name(
                    client,
                    f"https://auth.example{AUTH_ME_PATH}",
                    "private-token",
                )

        self.assertEqual(asyncio.run(run()), "Maria")

    def test_authenticated_name_request_classifies_rejected_tokens(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                401, json={"message": "private detail"}, request=request
            )

        async def run() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await request_authenticated_name(
                    client,
                    f"https://auth.example{AUTH_ME_PATH}",
                    "private-token",
                )

        with self.assertRaises(AuthTokenRejectedError) as raised:
            asyncio.run(run())
        self.assertNotIn("private-token", str(raised.exception))
        self.assertNotIn("private detail", str(raised.exception))

    def test_authenticated_name_request_uses_fallback_or_hides_failures(
        self,
    ) -> None:
        async def empty_name(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"name": "  "}, request=request)

        async def malformed(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=["invalid"], request=request)

        async def unavailable(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"detail": "private"}, request=request)

        async def request_name(handler: object) -> str:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                return await request_authenticated_name(
                    client,
                    f"https://auth.example{AUTH_ME_PATH}",
                    "private-token",
                )

        self.assertEqual(
            asyncio.run(request_name(empty_name)), ACCOUNT_FALLBACK_NAME
        )
        with self.assertRaises(AuthAccountUnavailableError):
            asyncio.run(request_name(malformed))
        with self.assertRaises(AuthAccountUnavailableError) as raised:
            asyncio.run(request_name(unavailable))
        self.assertNotIn("private", str(raised.exception))

    def test_login_request_sends_only_email_and_password(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, AUTH_LOGIN_PATH)
            self.assertEqual(
                request.read(),
                b'{"email":"person@example.test","password":"test-password"}',
            )
            return httpx.Response(
                200, json={"authToken": "temporary-token", "user_id": 17}
            )

        async def run() -> object:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await request_login(
                    client,
                    f"https://auth.example{AUTH_LOGIN_PATH}",
                    "person@example.test",
                    "test-password",
                )

        result = asyncio.run(run())
        self.assertEqual(result.auth_token, "temporary-token")
        self.assertEqual(result.user_id, 17)

    def test_login_rejection_is_classified_without_response_details(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                403,
                json={"message": "private account-specific detail"},
                request=request,
            )

        async def run() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await request_login(
                    client,
                    f"https://auth.example{AUTH_LOGIN_PATH}",
                    "person@example.test",
                    "test-password",
                )

        with self.assertRaises(InvalidCredentialsError) as raised:
            asyncio.run(run())
        self.assertNotIn("person@example.test", str(raised.exception))
        self.assertNotIn("test-password", str(raised.exception))
        self.assertNotIn("private account-specific detail", str(raised.exception))

    def test_malformed_success_response_is_classified_as_unavailable(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, json={"authToken": "", "user_id": True}, request=request
            )

        async def run() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await request_login(
                    client,
                    f"https://auth.example{AUTH_LOGIN_PATH}",
                    "person@example.test",
                    "test-password",
                )

        with self.assertRaises(LoginUnavailableError):
            asyncio.run(run())

    def test_http_and_network_failures_are_classified_without_details(self) -> None:
        async def http_response(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                503,
                json={"message": "private server detail"},
                request=request,
            )

        async def raise_network_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("private transport detail", request=request)

        for handler in (http_response, raise_network_error):
            with self.subTest(handler=handler.__name__):
                async def run() -> None:
                    async with httpx.AsyncClient(
                        transport=httpx.MockTransport(handler)
                    ) as client:
                        await request_login(
                            client,
                            f"https://auth.example{AUTH_LOGIN_PATH}",
                            "person@example.test",
                            "test-password",
                        )

                with self.assertRaises(LoginUnavailableError) as raised:
                    asyncio.run(run())
                self.assertNotIn("private", str(raised.exception))

    def test_login_state_declares_transient_only_fields(self) -> None:
        self.assertEqual(
            {
                name: (field.annotated_type, field.default)
                for name, field in LoginState.__own_fields__.items()
                if name in {
                    "is_loading",
                    "error_message",
                    "auth_token",
                    "account_name",
                    "password_visible",
                    "signup_password_visible",
                    "signup_confirmation_visible",
                }
            },
            {
                "is_loading": (bool, False),
                "error_message": (str, ""),
                "auth_token": (str, ""),
                "account_name": (str, ""),
                "password_visible": (bool, False),
                "signup_password_visible": (bool, False),
                "signup_confirmation_visible": (bool, False),
            },
        )

    def test_account_state_clears_rejected_token_and_falls_back_on_errors(
        self,
    ) -> None:
        class State:
            auth_token = "private-token"
            account_name = "Old name"
            _account_token = ""
            password_reset_notice_pending = False
            password_reset_notice_visible = False

        rejected_state = State()
        with (
            patch.dict(
                os.environ, {AUTH_API_ENV: "https://auth.example/api"}
            ),
            patch(
                "doafacil.login.request_authenticated_name",
                new_callable=AsyncMock,
                side_effect=AuthTokenRejectedError(),
            ),
        ):
            asyncio.run(LoginState.load_account.fn(rejected_state))
        self.assertEqual(rejected_state.auth_token, "")
        self.assertEqual(rejected_state.account_name, "")

        transient_state = State()
        with (
            patch.dict(
                os.environ, {AUTH_API_ENV: "https://auth.example/api"}
            ),
            patch(
                "doafacil.login.request_authenticated_name",
                new_callable=AsyncMock,
                side_effect=AuthAccountUnavailableError(),
            ),
        ):
            asyncio.run(LoginState.load_account.fn(transient_state))
        self.assertEqual(transient_state.auth_token, "private-token")
        self.assertEqual(transient_state.account_name, ACCOUNT_FALLBACK_NAME)

    def test_account_state_without_token_skips_request_and_logout_clears_values(
        self,
    ) -> None:
        class State:
            auth_token = ""
            account_name = "Old name"
            password_reset_notice_pending = False
            password_reset_notice_visible = False

        state = State()
        with (
            patch.dict(
                os.environ, {AUTH_API_ENV: "https://auth.example/api"}
            ),
            patch(
                "doafacil.login.request_authenticated_name",
                new_callable=AsyncMock,
            ) as request,
        ):
            asyncio.run(LoginState.load_account.fn(state))
        request.assert_not_awaited()
        self.assertEqual(state.account_name, "")

        state.auth_token = "private-token"
        state.account_name = "Maria"
        state.password_reset_notice_pending = True
        state.password_reset_notice_visible = True
        LoginState.logout.fn(state)
        self.assertEqual(state.auth_token, "")
        self.assertEqual(state.account_name, "")
        self.assertFalse(state.password_reset_notice_pending)
        self.assertFalse(state.password_reset_notice_visible)

    def test_password_visibility_state_toggles_on_each_activation(self) -> None:
        class State:
            password_visible = False

        state = State()
        LoginState.toggle_password_visibility.fn(state)
        self.assertTrue(state.password_visible)
        LoginState.toggle_password_visibility.fn(state)
        self.assertFalse(state.password_visible)

    def test_login_error_messages_are_generic_and_distinct(self) -> None:
        invalid_credentials = login_error_message(InvalidCredentialsError())
        unavailable = login_error_message(LoginUnavailableError())
        self.assertEqual(invalid_credentials, "E-mail ou senha incorretos.")
        self.assertIn("conectar", unavailable)
        self.assertNotEqual(invalid_credentials, unavailable)

    def test_login_state_success_stores_token_and_redirects_to_home(self) -> None:
        class State:
            is_loading = False
            error_message = ""
            auth_token = ""
            password_reset_notice_pending = True
            password_reset_notice_visible = True

        state = State()
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_login",
                new_callable=AsyncMock,
                return_value=LoginResult("transient-token", 23),
            ),
        ):
            async def run() -> list[rx.event.EventSpec]:
                events = []
                async for event in LoginState.login.fn(
                    state,
                    {"email": "person@example.test", "password": "test-password"},
                ):
                    events.append(event)
                return events

            events = asyncio.run(run())

        self.assertEqual(state.auth_token, "transient-token")
        self.assertFalse(state.is_loading)
        self.assertEqual(state.error_message, "")
        self.assertFalse(state.password_reset_notice_pending)
        self.assertFalse(state.password_reset_notice_visible)
        # O primeiro é o envio do “Entrando...”, antes do pedido (change
        # correcoes-revisao); o segundo, o redirecionamento.
        self.assertEqual(len(events), 2)
        self.assertIsNone(events[0])
        self.assertIn("/", str(events[1]))

    def test_login_state_errors_clear_token_and_end_loading(self) -> None:
        cases = (
            (
                InvalidCredentialsError(),
                "E-mail ou senha incorretos.",
            ),
            (
                LoginUnavailableError(),
                "Não foi possível conectar ao serviço de autenticação. Tente novamente.",
            ),
        )
        for error, expected_message in cases:
            with self.subTest(error=type(error).__name__):
                class State:
                    is_loading = False
                    error_message = ""
                    auth_token = "old-token"
                    password_reset_notice_pending = False
                    password_reset_notice_visible = False

                state = State()
                with (
                    patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
                    patch(
                        "doafacil.login.request_login",
                        new_callable=AsyncMock,
                        side_effect=error,
                    ),
                ):
                    async def run() -> list[rx.event.EventSpec]:
                        events = []
                        async for event in LoginState.login.fn(
                            state,
                            {
                                "email": "person@example.test",
                                "password": "test-password",
                            },
                        ):
                            events.append(event)
                        return events

                    events = asyncio.run(run())

                self.assertEqual(state.error_message, expected_message)
                self.assertEqual(state.auth_token, "")
                self.assertFalse(state.is_loading)
                # Só o envio do “Entrando...”, antes do pedido (change
                # correcoes-revisao).
                self.assertEqual(events, [None])

    def test_login_state_blocks_concurrent_submit(self) -> None:
        class State:
            is_loading = True
            error_message = ""
            auth_token = ""
            password_reset_notice_pending = False
            password_reset_notice_visible = False

        state = State()
        with patch(
            "doafacil.login.request_login", new_callable=AsyncMock
        ) as request:
            async def run() -> list[rx.event.EventSpec]:
                events = []
                async for event in LoginState.login.fn(
                    state,
                    {"email": "person@example.test", "password": "test-password"},
                ):
                    events.append(event)
                return events

            events = asyncio.run(run())

        request.assert_not_awaited()
        self.assertEqual(events, [])
        self.assertTrue(state.is_loading)


class LoginPageTests(unittest.TestCase):
    def test_auth_card_stylesheet_registers_animation_and_reduced_motion(self) -> None:
        stylesheet = Path(__file__).parents[1] / "assets" / "auth-card.css"
        css = stylesheet.read_text(encoding="utf-8")

        self.assertIn("/auth-card.css", app.stylesheets)
        self.assertIn("@keyframes auth-card-enter", css)
        self.assertIn("translateY(12px)", css)
        self.assertIn("0.3s ease-out 1 both", css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        reduced_motion_rules = css.split(
            "@media (prefers-reduced-motion: reduce)", maxsplit=1
        )[1]
        self.assertIn(".auth-card-enter", reduced_motion_rules)
        self.assertIn(".page-fade-enter", reduced_motion_rules)
        self.assertIn("animation: none;", reduced_motion_rules)

    def test_login_page_has_email_only_form_and_non_navigating_controls(self) -> None:
        page = login_page()
        self.assertEqual(page.min_height, "100vh")
        self.assertEqual(page.background, "#FFF6E8")
        contents = _component_text(page)
        for text in (
            "Bem-vindo",
            "Entre com seu e-mail e senha",
            "E-mail",
            "Senha",
            "Esqueci minha senha",
            "Criar conta",
        ):
            with self.subTest(text=text):
                self.assertIn(text, contents)

        nodes = _component_nodes(page)
        inputs = [
            node
            for node in nodes
            if type(node).__name__ == "TextFieldRoot"
        ]

        def literal(value: object) -> object:
            return getattr(value, "_var_value", value)

        fields = {
            literal(node.name): node
            for node in inputs
        }
        self.assertEqual(
            {name: literal(node.placeholder) for name, node in fields.items()},
            {"email": "Insira seu e-mail", "password": "Insira sua senha"},
        )
        self.assertEqual(literal(fields["email"].type), "email")
        self.assertIn("password_visible", str(fields["password"].type))
        for name, field_id in (
            ("email", "login-email"),
            ("password", "login-password"),
        ):
            with self.subTest(field=name):
                field = fields[name]
                self.assertEqual(
                    getattr(field.id, "_var_value", field.id),
                    field_id,
                )
                self.assertEqual(field.color, "#333333")
                # O placeholder vem da regra global dos campos.
                self.assertNotIn(f"#{field_id}::placeholder", app.style)
                self.assertEqual(
                    app.style[FIELD_PLACEHOLDER_SELECTOR]["color"],
                    "#6B6B6B !important",
                )
        self.assertNotIn("CPF", contents)
        self.assertIn("login", app._unevaluated_pages)
        self.assertEqual(app._unevaluated_pages["login"].route, "login")
        logo = next(
            node
            for node in nodes
            if getattr(getattr(node, "alt", None), "_var_value", None)
            == "DoaFácil"
        )
        self.assertEqual(getattr(logo.src, "_var_value", logo.src), "/logo.svg")

        forgot_password = next(
            node
            for node in nodes
            if _component_text(node) == "Esqueci minha senha"
        )
        self.assertIn("/recuperar-senha", str(forgot_password))
        self.assertIn("on_click", forgot_password.event_triggers)

        create_account = next(
            node for node in nodes if _component_text(node) == "Criar conta"
        )
        self.assertIn("on_click", create_account.event_triggers)
        self.assertIn(
            "navigate_to_signup_from_login",
            str(create_account.event_triggers["on_click"]),
        )

        back_link = next(
            node for node in nodes if _component_text(node) == "← Voltar"
        )
        route_link = back_link.children[0]
        self.assertEqual(getattr(route_link.to, "_var_value", route_link.to), "/")

    def test_login_form_has_loading_and_error_state_bindings(self) -> None:
        page_nodes = _component_nodes(login_page())
        form = next(node for node in page_nodes if type(node).__name__ == "Form")
        card = next(
            node
            for node in page_nodes
            if getattr(node, "background", None) == "white"
            and getattr(node, "children", None) == [form]
        )
        submit = next(
            node
            for node in page_nodes
            if type(node).__name__ == "Button"
            and getattr(getattr(node, "type", None), "_var_value", None)
            == "submit"
        )
        self.assertTrue(getattr(form, "event_triggers", {}).get("on_submit"))
        self.assertEqual(card.width, "100%")
        self.assertEqual(card.border_radius, "16px")
        self.assertIn("is_loading", str(submit.disabled))
        self.assertIn("is_loading", str(submit.children))
        self.assertIn("error_message", str(page_nodes))

    def test_login_animation_class_is_applied_only_to_the_card(self) -> None:
        nodes = _component_nodes(login_page())
        animated_nodes = [
            node
            for node in nodes
            if getattr(node, "class_name", None) == "auth-card-enter"
        ]
        self.assertEqual(len(animated_nodes), 1)
        card = animated_nodes[0]
        self.assertEqual(card.background, "white")
        self.assertTrue(
            all(
                getattr(node, "class_name", None) != "auth-card-enter"
                for node in nodes
                if node is not card
            )
        )

    def test_password_visibility_button_is_accessible_and_not_submit(self) -> None:
        page_nodes = _component_nodes(login_page())
        visibility_button = next(
            node
            for node in page_nodes
            if getattr(getattr(node, "type", None), "_var_value", None)
            == "button"
            and "aria-label" in getattr(node, "custom_attrs", {})
        )
        password_input = next(
            node
            for node in page_nodes
            if type(node).__name__ == "TextFieldRoot"
            and getattr(getattr(node, "name", None), "_var_value", None)
            == "password"
        )
        self.assertIn("password_visible", str(password_input.type))
        accessible_label = str(visibility_button.custom_attrs["aria-label"])
        self.assertIn("Mostrar senha", accessible_label)
        self.assertIn("Ocultar senha", accessible_label)
        icon_branches = str(visibility_button.children)
        self.assertIn("LucideEyeOff", icon_branches)
        self.assertIn("LucideEye", icon_branches)
        self.assertTrue(
            getattr(visibility_button, "event_triggers", {}).get("on_click")
        )
        self.assertEqual(
            getattr(visibility_button.style["color"], "_var_value", None),
            "#168447",
        )

    def test_home_header_enters_login_and_keeps_other_home_controls(self) -> None:
        page = index()
        nodes = _component_nodes(page)
        enter = next(
            node
            for node in nodes
            if type(node).__name__ == "Button"
            and _component_text(node) == "Entrar"
        )
        self.assertIn("on_click", getattr(enter, "event_triggers", {}))
        self.assertIn("login_href", str(enter.event_triggers["on_click"]))  # /login com o next da página (change acabamento)

        # Change landing-nova: o “Sair” fica no menu da conta, junto do nome.
        logout = next(
            node
            for node in nodes
            if type(node).__name__ == "DropdownMenuItem"
            and "Sair" in _component_text(node)
        )
        self.assertIn("on_select", getattr(logout, "event_triggers", {}))
        self.assertIn("LoginState.logout", str(logout.event_triggers["on_select"]))
        self.assertIn("home-account-menu", str(page))
        self.assertIn("account_name", str(page))

        # Só o “Entrar”, os itens do menu da conta, a busca e a gaveta de
        # categorias (change explorar-categorias) têm eventos.
        allowed = {"DropdownMenuItem", "Form", "DialogRoot"}
        for node in nodes:
            # O link de cada categoria da gaveta fecha a gaveta ao navegar.
            if getattr(node, "class_name", None) == "category-link":
                self.assertIn("close_drawer", str(node.event_triggers.get("on_click")))
                continue
            # Itens do painel do celular (change navegacao-celular): fecham o
            # painel ao navegar; o “Sair” também encerra a sessão.
            if "nav-menu-item" in str(getattr(node, "class_name", "") or ""):
                self.assertIn("NavMenuState.close", str(node.event_triggers.get("on_click")))
                continue
            # Pausa dos vídeos com movimento reduzido (change videos-home).
            if getattr(node, "id", None) == "como-funciona":
                self.assertEqual(set(node.event_triggers), {"on_mount"})
                continue
            # “Tentar de novo” da gaveta de categorias (change navegacao-celular).
            if getattr(node, "class_name", None) == "category-retry":
                self.assertIn("reload_categories", str(node.event_triggers.get("on_click")))
                continue
            # “Tentar de novo” da contagem e das recentes (change correcoes-finais).
            if getattr(node, "class_name", None) in {"home-count-retry", "home-recent-retry"}:
                self.assertIn("retry_home_data", str(node.event_triggers.get("on_click")))
                continue
            # O “Entrar” da barra do celular, igual ao do desktop.
            if type(node).__name__ == "Button" and _component_text(node) == "Entrar":
                self.assertIn("login_href", str(node.event_triggers["on_click"]))  # change acabamento
                continue
            if node is not enter and type(node).__name__ not in allowed:
                self.assertFalse(getattr(node, "event_triggers", {}))

    def test_messages_link_only_in_authenticated_header(self) -> None:
        page = index()
        header_conds = [
            node
            for node in _component_nodes(page)
            if type(node).__name__ == "Cond"
            and "auth_token" in str(getattr(node, "cond", ""))
            and "Sair" in str(node.children[0])
        ]
        # Barra do desktop, barra do celular e painel do celular (change
        # navegacao-celular).
        panel = [cond for cond in header_conds if "nav-menu-account" in str(cond)]
        bars = [cond for cond in header_conds if "nav-menu-account" not in str(cond)]
        self.assertEqual((len(bars), len(panel)), (2, 1))
        for bar in bars:
            authenticated, visitor = (str(child) for child in bar.children)
            # A entrada no chat saiu do cabeçalho: virou o botão flutuante.
            for header in (authenticated, visitor):
                self.assertNotIn("Mensagens", header)
                self.assertNotIn("/chat", header)
                self.assertNotIn("unread_total", header)
                self.assertNotIn("chat-unread-badge", header)
            self.assertIn("Sair", authenticated)
        # No painel, “Mensagens” só com sessão.
        authenticated, visitor = (str(child) for child in panel[0].children)
        self.assertIn("Mensagens", authenticated)
        self.assertIn('"/chat"', authenticated)
        self.assertNotIn("Mensagens", visitor)

    def test_home_has_floating_messages_button(self) -> None:
        rendered = str(index())
        self.assertEqual(rendered.count("chat-fab"), 1)

    def test_home_fades_static_content_without_animating_header_or_xano_data(self) -> None:
        nodes = _component_nodes(index())
        animated_nodes = [
            node
            for node in nodes
            if "page-fade-enter"
            in str(getattr(node, "class_name", "")).split()
        ]

        self.assertEqual(len(animated_nodes), 4)
        self.assertTrue(
            any("Doar é fácil." in _component_text(node) for node in animated_nodes)
        )
        self.assertTrue(
            any(
                "Pessoas reunidas na comunidade DoaFácil"
                == getattr(getattr(node, "alt", None), "_var_value", None)
                for node in animated_nodes
            )
        )
        self.assertTrue(
            all(
                "HomeState" not in str(_component_nodes(node))
                for node in animated_nodes
            )
        )

        header = next(
            node
            for node in nodes
            if getattr(node, "background", None) == "white"
            and any(
                _component_text(child) == "Entrar"
                for child in _component_nodes(node)
            )
        )
        self.assertNotIn("page-fade-enter", str(header.class_name).split())

        footer = next(
            node
            for node in nodes
            if "Projeto acadêmico DoaFácil" in _component_text(node)
            and "Fale conosco" in _component_text(node)
        )
        self.assertNotIn("page-fade-enter", str(footer.class_name).split())


if __name__ == "__main__":
    unittest.main()


class AuthPendingStateTests(unittest.TestCase):
    """Change correcoes-revisao: login, cadastro e recuperação de senha mandam
    o botão em carregamento ao navegador (o primeiro `yield`) antes do pedido
    ao Xano, com um único pedido; uma validação que falha não emite nada."""

    ENV = {AUTH_API_ENV: "https://auth.example/api"}
    SIGNUP_FORM = {
        "name": "Pessoa Teste",
        "email": "pessoa@example.test",
        "city": "Cidade",
        "state": "SP",
        "password": "senha123",
        "confirm_password": "senha123",
    }

    @staticmethod
    def _state(**overrides):
        from types import SimpleNamespace

        values = dict(
            is_loading=False,
            error_message="",
            auth_token="",
            account_name="",
            password_reset_notice_pending=False,
            password_reset_notice_visible=False,
            signup_notice_pending=False,
            signup_notice_visible=False,
            recovery_is_loading=False,
            recovery_error_message="",
            recovery_email="",
            recovery_resend_seconds=0,
            verification_flow="",
            signup_email="",
            _signup_password="",
            _reset_token="",
            _auth_next="",
            router=None,
        )
        values.update(overrides)
        return SimpleNamespace(**values)

    def _steps(self, state, generator, target: str, flag: str, result=None):
        """(evento, flag) a cada `yield` e o valor da flag no momento do pedido."""
        seen: list[bool] = []

        async def fake(*args, **kwargs):
            seen.append(getattr(state, flag))
            return result

        async def collect():
            return [(event, getattr(state, flag)) async for event in generator]

        with patch.dict(os.environ, self.ENV), patch(f"doafacil.login.{target}", side_effect=fake):
            steps = asyncio.run(collect())
        return steps, seen

    def test_every_auth_action_shows_loading_before_the_request(self) -> None:
        from types import SimpleNamespace

        cases = [
            ("login", "request_login", "is_loading", {},
             lambda s: LoginState.login.fn(s, {"email": "pessoa@example.test", "password": "senha123"}),
             LoginResult(auth_token="token", user_id=1)),
            ("signup", "request_signup", "is_loading", {},
             lambda s: LoginState.signup.fn(s, dict(self.SIGNUP_FORM)), None),
            ("pedir código", "request_password_reset_code", "recovery_is_loading", {},
             lambda s: LoginState.request_recovery_code.fn(s, {"email": "pessoa@example.test"}), None),
            ("reenviar (recuperação)", "request_password_reset_code", "recovery_is_loading",
             {"recovery_email": "pessoa@example.test", "verification_flow": "recovery"},
             lambda s: LoginState.resend_recovery_code.fn(s), None),
            ("reenviar (cadastro)", "request_signup_resend", "recovery_is_loading",
             {"signup_email": "pessoa@example.test", "_signup_password": "senha123", "verification_flow": "signup"},
             lambda s: LoginState.resend_recovery_code.fn(s), None),
            ("verificar (recuperação)", "request_password_reset_verification", "recovery_is_loading",
             {"recovery_email": "pessoa@example.test", "verification_flow": "recovery"},
             lambda s: LoginState.verify_recovery_code.fn(s, {"code": "123456"}),
             SimpleNamespace(reset_token="reset")),
            ("verificar (cadastro)", "request_signup_verification", "recovery_is_loading",
             {"signup_email": "pessoa@example.test", "_signup_password": "senha123", "verification_flow": "signup"},
             lambda s: LoginState.verify_recovery_code.fn(s, {"code": "123456"}), None),
            ("nova senha", "request_password_reset_confirmation", "recovery_is_loading",
             {"_reset_token": "reset"},
             lambda s: LoginState.confirm_recovery_password.fn(
                 s, {"password": "novaSenha1", "password_confirmation": "novaSenha1"}),
             None),
        ]
        for name, target, flag, overrides, start, result in cases:
            with self.subTest(acao=name):
                state = self._state(**overrides)
                with patch("doafacil.login.rx.redirect", side_effect=lambda path: f"redirect:{path}"):
                    steps, seen = self._steps(state, start(state), target, flag, result)
                self.assertEqual(steps[0], (None, True))
                self.assertEqual(seen, [True])
                self.assertFalse(getattr(state, flag))

    def test_local_rejections_emit_nothing_and_make_no_request(self) -> None:
        cases = [
            ("login sem senha", "request_login", "is_loading", {},
             lambda s: LoginState.login.fn(s, {"email": "pessoa@example.test", "password": ""})),
            ("cadastro inválido", "request_signup", "is_loading", {},
             lambda s: LoginState.signup.fn(s, {**self.SIGNUP_FORM, "confirm_password": "outra123"})),
            ("e-mail inválido", "request_password_reset_code", "recovery_is_loading", {},
             lambda s: LoginState.request_recovery_code.fn(s, {"email": "sem-arroba"})),
            ("código curto", "request_password_reset_verification", "recovery_is_loading",
             {"recovery_email": "pessoa@example.test"},
             lambda s: LoginState.verify_recovery_code.fn(s, {"code": "123"})),
            ("senhas diferentes", "request_password_reset_confirmation", "recovery_is_loading",
             {"_reset_token": "reset"},
             lambda s: LoginState.confirm_recovery_password.fn(
                 s, {"password": "novaSenha1", "password_confirmation": "outraSenha2"})),
        ]
        for name, target, flag, overrides, start in cases:
            with self.subTest(caso=name):
                state = self._state(**overrides)
                steps, seen = self._steps(state, start(state), target, flag)
                self.assertEqual(steps, [])
                self.assertEqual(seen, [])
                self.assertFalse(getattr(state, flag))
                self.assertTrue(state.error_message or state.recovery_error_message)

    def test_buttons_show_loading_texts(self) -> None:
        from doafacil.cadastro import signup_page

        self.assertIn("Entrando...", str(login_page()))
        self.assertIn("Criando...", str(signup_page()))
