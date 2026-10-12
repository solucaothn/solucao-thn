import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

import httpx
import reflex as rx

from doafacil.cadastro import BRAZILIAN_STATES, signup_page
from doafacil.doafacil import app
from doafacil.login import (
    AUTH_API_ENV,
    AUTH_SIGNUP_PATH,
    DUPLICATE_SIGNUP_MESSAGE,
    EmailAlreadyRegisteredError,
    LoginConfigurationError,
    LoginState,
    SignupRejectedError,
    SignupResult,
    SignupUnavailableError,
    auth_signup_endpoint,
    request_signup,
    signup_error_message,
    validate_signup_data,
)


VALID_FORM = {
    "name": " Pessoa Teste ",
    "email": " pessoa@example.test ",
    "city": " Cidade ",
    "state": "SP",
    "password": "senha123",
    "confirm_password": "senha123",
}


class SignupClientTests(unittest.TestCase):
    def test_auth_signup_endpoint_reuses_validated_environment_url(self) -> None:
        with patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api/"}):
            self.assertEqual(
                auth_signup_endpoint(),
                f"https://auth.example/api{AUTH_SIGNUP_PATH}",
            )

        with patch.dict(os.environ, {AUTH_API_ENV: "invalid"}):
            with self.assertRaises(LoginConfigurationError):
                auth_signup_endpoint()

    def test_signup_request_sends_only_xano_fields(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, AUTH_SIGNUP_PATH)
            self.assertEqual(
                request.read(),
                b'{"name":"Pessoa Teste","email":"pessoa@example.test",'
                b'"password":"senha123","city":"Cidade","state":"SP"}',
            )
            return httpx.Response(
                200, json={"authToken": "temporary-token", "user_id": 17}
            )

        async def run() -> SignupResult:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await request_signup(
                    client,
                    f"https://auth.example{AUTH_SIGNUP_PATH}",
                    **{
                        "name": VALID_FORM["name"],
                        "email": VALID_FORM["email"],
                        "password": VALID_FORM["password"],
                        "city": VALID_FORM["city"],
                        "state": VALID_FORM["state"],
                    },
                )

        result = asyncio.run(run())
        self.assertEqual(result.auth_token, "temporary-token")
        self.assertEqual(result.user_id, 17)
        self.assertNotIn("confirm_password", repr(result))

    def test_signup_duplicate_is_classified_only_by_exact_structured_message(self) -> None:
        async def duplicate_response(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                403,
                json={"error": {"message": DUPLICATE_SIGNUP_MESSAGE}},
                request=request,
            )

        async def run(handler: object) -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                await request_signup(
                    client,
                    f"https://auth.example{AUTH_SIGNUP_PATH}",
                    name="Pessoa",
                    email="pessoa@example.test",
                    password="senha123",
                    city="Cidade",
                    state="SP",
                )

        with self.assertRaises(EmailAlreadyRegisteredError) as raised:
            asyncio.run(run(duplicate_response))
        self.assertNotIn(DUPLICATE_SIGNUP_MESSAGE, str(raised.exception))
        self.assertEqual(
            signup_error_message(raised.exception),
            "Este e-mail já está cadastrado.",
        )

        async def similar_but_not_exact(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                403,
                json={"message": "An account with this email already exists"},
                request=request,
            )

        with self.assertRaises(SignupRejectedError):
            asyncio.run(run(similar_but_not_exact))

    def test_signup_generic_rejection_and_network_error_hide_details(self) -> None:
        async def reject(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                500,
                json={"message": "private server detail"},
                request=request,
            )

        async def fail_network(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("private transport detail", request=request)

        for handler, expected_error in (
            (reject, SignupRejectedError),
            (fail_network, SignupUnavailableError),
        ):
            with self.subTest(handler=handler.__name__):
                async def run() -> None:
                    async with httpx.AsyncClient(
                        transport=httpx.MockTransport(handler)
                    ) as client:
                        await request_signup(
                            client,
                            f"https://auth.example{AUTH_SIGNUP_PATH}",
                            name="Pessoa",
                            email="pessoa@example.test",
                            password="senha123",
                            city="Cidade",
                            state="SP",
                        )

                with self.assertRaises(expected_error) as raised:
                    asyncio.run(run())
                self.assertNotIn("private", str(raised.exception))
                self.assertNotIn("pessoa@example.test", str(raised.exception))
                self.assertNotIn("senha123", str(raised.exception))


class SignupValidationTests(unittest.TestCase):
    def test_valid_signup_data_passes(self) -> None:
        self.assertEqual(validate_signup_data(VALID_FORM), "")

    def test_required_fields_are_validated(self) -> None:
        messages = {
            "name": "Informe seu nome.",
            "email": "Informe seu e-mail.",
            "city": "Informe sua cidade.",
            "state": "Selecione seu estado.",
            "password": "Informe sua senha.",
            "confirm_password": "Confirme sua senha.",
        }
        for field, message in messages.items():
            with self.subTest(field=field):
                data = {**VALID_FORM, field: ""}
                self.assertEqual(validate_signup_data(data), message)

    def test_email_must_have_a_valid_basic_format(self) -> None:
        for email in ("invalid", "person@", "person@example", "person @example.test"):
            with self.subTest(email=email):
                data = {**VALID_FORM, "email": email}
                self.assertEqual(
                    validate_signup_data(data), "Informe um e-mail válido."
                )

    def test_password_requires_eight_characters_letter_and_digit(self) -> None:
        cases = (
            ("a123456", "A senha deve ter pelo menos 8 caracteres."),
            ("abcdefgh", "A senha deve conter pelo menos um número."),
            ("12345678", "A senha deve conter pelo menos uma letra."),
        )
        for password, message in cases:
            with self.subTest(password=password):
                data = {
                    **VALID_FORM,
                    "password": password,
                    "confirm_password": password,
                }
                self.assertEqual(validate_signup_data(data), message)

    def test_password_confirmation_must_match_exactly(self) -> None:
        data = {**VALID_FORM, "confirm_password": "senha1234"}
        self.assertEqual(validate_signup_data(data), "As senhas não coincidem.")


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


class SignupStateTests(unittest.TestCase):
    def test_signup_success_uses_shared_token_and_redirects_home(self) -> None:
        class State:
            is_loading = False
            error_message = ""
            auth_token = ""
            signup_password_visible = False
            signup_confirmation_visible = False

        state = State()
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_signup",
                new_callable=AsyncMock,
                return_value=SignupResult("temporary-token", 23),
            ) as request,
        ):
            async def run() -> list[rx.event.EventSpec]:
                events = []
                async for event in LoginState.signup.fn(state, VALID_FORM):
                    events.append(event)
                return events

            events = asyncio.run(run())

        self.assertEqual(state.auth_token, "temporary-token")
        self.assertFalse(state.is_loading)
        self.assertEqual(state.error_message, "")
        self.assertEqual(len(events), 1)
        self.assertIn("/", str(events[0]))
        request.assert_awaited_once()
        self.assertEqual(len(request.await_args.args), 7)
        state_fields = LoginState.__own_fields__
        self.assertNotIn("password", state_fields)
        self.assertNotIn("confirm_password", state_fields)
        self.assertNotIn("form_data", state_fields)

    def test_signup_errors_are_localized_and_clear_old_token(self) -> None:
        cases = (
            (
                EmailAlreadyRegisteredError(),
                "Este e-mail já está cadastrado.",
            ),
            (
                SignupRejectedError(),
                "Não foi possível criar sua conta. Confira os dados e tente novamente.",
            ),
            (
                SignupUnavailableError(),
                "Não foi possível conectar ao serviço de autenticação. Tente novamente.",
            ),
        )
        for error, expected_message in cases:
            with self.subTest(error=type(error).__name__):
                class State:
                    is_loading = False
                    error_message = ""
                    auth_token = "old-token"
                    signup_password_visible = False
                    signup_confirmation_visible = False

                state = State()
                with (
                    patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example"}),
                    patch(
                        "doafacil.login.request_signup",
                        new_callable=AsyncMock,
                        side_effect=error,
                    ),
                ):
                    async def run() -> list[rx.event.EventSpec]:
                        events = []
                        async for event in LoginState.signup.fn(state, VALID_FORM):
                            events.append(event)
                        return events

                    events = asyncio.run(run())

                self.assertEqual(state.error_message, expected_message)
                self.assertEqual(state.auth_token, "")
                self.assertFalse(state.is_loading)
                self.assertEqual(events, [])

    def test_signup_validates_before_request_and_blocks_duplicate_submission(self) -> None:
        class State:
            is_loading = False
            error_message = ""
            auth_token = ""

        invalid_state = State()
        with patch("doafacil.login.request_signup") as request:
            async def run_invalid() -> None:
                async for _ in LoginState.signup.fn(
                    invalid_state, {**VALID_FORM, "email": "invalid"}
                ):
                    pass

            asyncio.run(run_invalid())
        request.assert_not_called()
        self.assertEqual(invalid_state.error_message, "Informe um e-mail válido.")

        loading_state = State()
        loading_state.is_loading = True
        with patch("doafacil.login.request_signup") as request:
            async def run_loading() -> list[rx.event.EventSpec]:
                events = []
                async for event in LoginState.signup.fn(loading_state, VALID_FORM):
                    events.append(event)
                return events

            self.assertEqual(asyncio.run(run_loading()), [])
        request.assert_not_called()

    def test_signup_visibility_flags_toggle_independently(self) -> None:
        class State:
            signup_password_visible = False
            signup_confirmation_visible = False

        state = State()
        LoginState.toggle_signup_password_visibility.fn(state)
        self.assertTrue(state.signup_password_visible)
        self.assertFalse(state.signup_confirmation_visible)
        LoginState.toggle_signup_confirmation_visibility.fn(state)
        self.assertTrue(state.signup_password_visible)
        self.assertTrue(state.signup_confirmation_visible)
        LoginState.toggle_signup_password_visibility.fn(state)
        self.assertFalse(state.signup_password_visible)
        self.assertTrue(state.signup_confirmation_visible)


class SignupPageTests(unittest.TestCase):
    def test_signup_page_has_required_fields_and_27_states(self) -> None:
        page = signup_page()
        self.assertEqual(page.min_height, "100vh")
        self.assertEqual(page.background, "#FFF6E8")
        contents = _component_text(page)
        for label in (
            "Criar sua conta",
            "Nome",
            "E-mail",
            "Cidade",
            "Estado",
            "Senha",
            "Confirmar senha",
            "Criar",
        ):
            self.assertIn(label, contents)
        self.assertNotIn("Telefone", contents)
        self.assertEqual(len(BRAZILIAN_STATES), 27)
        self.assertEqual(len(set(BRAZILIAN_STATES)), 27)

        nodes = _component_nodes(page)
        fields = {
            getattr(node.name, "_var_value", node.name): node
            for node in nodes
            if type(node).__name__ == "TextFieldRoot"
        }
        self.assertEqual(
            list(fields),
            ["name", "email", "city", "password", "confirm_password"],
        )
        ordered_labels = (
            "Nome",
            "E-mail",
            "Cidade",
            "Estado",
            "Senha",
            "Confirmar senha",
        )
        self.assertEqual(
            [contents.index(label) for label in ordered_labels],
            sorted(contents.index(label) for label in ordered_labels),
        )
        select = next(node for node in nodes if type(node).__name__ == "SelectRoot")
        self.assertEqual(getattr(select.name, "_var_value", select.name), "state")
        self.assertTrue(getattr(select.required, "_var_value", select.required))
        option_values = [
            getattr(node.value, "_var_value", node.value)
            for node in nodes
            if type(node).__name__ == "SelectItem"
        ]
        self.assertEqual(option_values, list(BRAZILIAN_STATES))

    def test_signup_password_buttons_are_accessible_and_independent(self) -> None:
        nodes = _component_nodes(signup_page())
        password_inputs = [
            node
            for node in nodes
            if type(node).__name__ == "TextFieldRoot"
            and getattr(getattr(node, "name", None), "_var_value", None)
            in {"password", "confirm_password"}
        ]
        self.assertEqual(len(password_inputs), 2)
        for field in password_inputs:
            self.assertIn("signup_", str(field.type))

        buttons = [
            node
            for node in nodes
            if getattr(getattr(node, "type", None), "_var_value", None) == "button"
            and "aria-label" in getattr(node, "custom_attrs", {})
        ]
        self.assertEqual(len(buttons), 2)
        self.assertTrue(
            all(
                "Mostrar senha" in str(button.custom_attrs["aria-label"])
                and "Ocultar senha" in str(button.custom_attrs["aria-label"])
                for button in buttons
            )
        )
        self.assertNotEqual(
            str(buttons[0].event_triggers["on_click"]),
            str(buttons[1].event_triggers["on_click"]),
        )

    def test_signup_form_binds_loading_errors_and_submit_event(self) -> None:
        nodes = _component_nodes(signup_page())
        form = next(node for node in nodes if type(node).__name__ == "Form")
        submit_button = next(
            node
            for node in nodes
            if type(node).__name__ == "Button"
            and getattr(getattr(node, "type", None), "_var_value", None)
            == "submit"
        )
        self.assertTrue(form.event_triggers.get("on_submit"))
        self.assertIn("is_loading", str(submit_button.disabled))
        self.assertIn("is_loading", str(submit_button.children))
        self.assertIn("error_message", str(nodes))

    def test_signup_page_registers_route_and_has_back_navigation(self) -> None:
        self.assertIn("cadastro", app._unevaluated_pages)
        self.assertEqual(app._unevaluated_pages["cadastro"].route, "cadastro")
        back_link = next(
            node
            for node in _component_nodes(signup_page())
            if _component_text(node) == "← Voltar"
        )
        route_link = back_link.children[0]
        self.assertEqual(
            getattr(route_link.to, "_var_value", route_link.to), "/login"
        )


if __name__ == "__main__":
    unittest.main()
