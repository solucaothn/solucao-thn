import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

import httpx
import reflex as rx

from doafacil.doafacil import app, index
from doafacil.login import (
    AUTH_API_ENV,
    AUTH_LOGIN_PATH,
    InvalidCredentialsError,
    LoginConfigurationError,
    LoginResult,
    LoginState,
    LoginUnavailableError,
    auth_login_endpoint,
    login_page,
    login_error_message,
    request_login,
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
            },
            {
                "is_loading": (bool, False),
                "error_message": (str, ""),
                "auth_token": (str, ""),
                "password_visible": (bool, False),
            },
        )

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
        self.assertEqual(len(events), 1)
        self.assertIn("/", str(events[0]))

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
                self.assertEqual(events, [])

    def test_login_state_blocks_concurrent_submit(self) -> None:
        class State:
            is_loading = True
            error_message = ""
            auth_token = ""

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
                self.assertEqual(
                    app.style[f"#{field_id}::placeholder"],
                    {"color": "#6b6b6b", "opacity": "1"},
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

        no_action_labels = {"Esqueci minha senha", "Criar conta"}
        for node in nodes:
            if _component_text(node) in no_action_labels:
                self.assertFalse(getattr(node, "href", None))
                self.assertFalse(getattr(node, "event_triggers", {}))

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
            if _component_text(node) == "Entrar"
        )
        self.assertIn("on_click", getattr(enter, "event_triggers", {}))
        self.assertIn("/login", str(enter.event_triggers["on_click"]))

        for node in nodes:
            if node is not enter:
                self.assertFalse(getattr(node, "event_triggers", {}))


if __name__ == "__main__":
    unittest.main()
