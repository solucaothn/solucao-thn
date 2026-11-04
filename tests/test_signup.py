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
    AUTH_SIGNUP_RESEND_PATH,
    AUTH_SIGNUP_VERIFY_PATH,
    LoginConfigurationError,
    LoginState,
    RECOVERY_CODE_ERROR,
    SignupRejectedError,
    SignupUnavailableError,
    auth_signup_endpoint,
    auth_signup_resend_endpoint,
    auth_signup_verify_endpoint,
    request_signup,
    request_signup_resend,
    request_signup_verification,
    signup_error_message,
    validate_signup_data,
)
from doafacil.recuperacao_senha import verify_recovery_page


VALID_FORM = {
    "name": " Pessoa Teste ",
    "email": " pessoa@example.test ",
    "city": " Cidade ",
    "state": "SP",
    "password": "senha123",
    "confirm_password": "senha123",
}


class SignupClientTests(unittest.TestCase):
    def test_signup_endpoints_reuse_validated_environment_url(self) -> None:
        with patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api/"}):
            self.assertEqual(
                auth_signup_endpoint(),
                f"https://auth.example/api{AUTH_SIGNUP_PATH}",
            )
            self.assertEqual(
                auth_signup_resend_endpoint(),
                f"https://auth.example/api{AUTH_SIGNUP_RESEND_PATH}",
            )
            self.assertEqual(
                auth_signup_verify_endpoint(),
                f"https://auth.example/api{AUTH_SIGNUP_VERIFY_PATH}",
            )

        with patch.dict(os.environ, {AUTH_API_ENV: "invalid"}):
            for endpoint in (
                auth_signup_endpoint,
                auth_signup_resend_endpoint,
                auth_signup_verify_endpoint,
            ):
                with self.subTest(endpoint=endpoint.__name__):
                    with self.assertRaises(LoginConfigurationError):
                        endpoint()

    def test_signup_request_sends_only_xano_fields_and_needs_no_token(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, AUTH_SIGNUP_PATH)
            self.assertEqual(
                request.read(),
                b'{"name":"Pessoa Teste","email":"pessoa@example.test",'
                b'"password":"senha123","city":"Cidade","state":"SP"}',
            )
            return httpx.Response(200, json={"success": True})

        async def run() -> None:
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

        self.assertIsNone(asyncio.run(run()))

    def test_signup_rejection_does_not_disclose_duplicate_account(self) -> None:
        async def run(status_code: int, payload: dict[str, object]) -> None:
            async def respond(request: httpx.Request) -> httpx.Response:
                return httpx.Response(status_code, json=payload, request=request)

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
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

        for status_code, payload in (
            (200, {"success": False, "message": "email already exists"}),
            (403, {"error": {"message": "email already exists"}}),
        ):
            with self.subTest(status_code=status_code):
                with self.assertRaises(SignupRejectedError) as raised:
                    asyncio.run(run(status_code, payload))
                self.assertNotIn("email already exists", str(raised.exception))
                self.assertNotIn(
                    "já está cadastrado",
                    signup_error_message(raised.exception),
                )

    def test_signup_uses_same_neutral_success_shape_without_a_token(self) -> None:
        responses: list[dict[str, object]] = []

        async def respond(request: httpx.Request) -> httpx.Response:
            response_body = {"success": True}
            responses.append(response_body)
            return httpx.Response(200, json=response_body, request=request)

        async def run() -> list[None]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                results = []
                for email in ("new@example.test", "existing@example.test"):
                    results.append(
                        await request_signup(
                            client,
                            f"https://auth.example{AUTH_SIGNUP_PATH}",
                            name="Pessoa",
                            email=email,
                            password="senha123",
                            city="Cidade",
                            state="SP",
                        )
                    )
                return results

        self.assertEqual(asyncio.run(run()), [None, None])
        self.assertEqual(responses, [{"success": True}, {"success": True}])

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

    def test_resend_and_verification_send_only_expected_payloads(self) -> None:
        observed: list[tuple[str, bytes]] = []

        async def respond(request: httpx.Request) -> httpx.Response:
            observed.append((request.url.path, request.read()))
            return httpx.Response(200, json={"success": True})

        async def run() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await request_signup_resend(
                    client,
                    f"https://auth.example{AUTH_SIGNUP_RESEND_PATH}",
                    "pessoa@example.test",
                )
                await request_signup_verification(
                    client,
                    f"https://auth.example{AUTH_SIGNUP_VERIFY_PATH}",
                    "pessoa@example.test",
                    "123456",
                    "senha123",
                )

        asyncio.run(run())
        self.assertEqual(
            observed,
            [
                (
                    AUTH_SIGNUP_RESEND_PATH,
                    b'{"email":"pessoa@example.test"}',
                ),
                (
                    AUTH_SIGNUP_VERIFY_PATH,
                    b'{"email":"pessoa@example.test","code":"123456",'
                    b'"password":"senha123"}',
                ),
            ],
        )

    def test_signup_verification_rejects_bad_code_and_sanitizes_network_errors(
        self,
    ) -> None:
        async def respond(
            status_code: int, payload: dict[str, object]
        ) -> None:
            async def handler(request: httpx.Request) -> httpx.Response:
                return httpx.Response(status_code, json=payload, request=request)

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                await request_signup_verification(
                    client,
                    f"https://auth.example{AUTH_SIGNUP_VERIFY_PATH}",
                    "person@example.test",
                    "123456",
                    "private-password",
                )

        with self.assertRaises(SignupRejectedError):
            asyncio.run(respond(200, {"success": False}))

        async def fail_network(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("private transport detail", request=request)

        async def call() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(fail_network)
            ) as client:
                await request_signup_verification(
                    client,
                    f"https://auth.example{AUTH_SIGNUP_VERIFY_PATH}",
                    "person@example.test",
                    "123456",
                    "private-password",
                )

        with self.assertRaises(SignupUnavailableError) as raised:
            asyncio.run(call())
        self.assertNotIn("private", str(raised.exception))

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
    def test_signup_success_stores_only_transient_email_and_password(self) -> None:
        class State:
            is_loading = False
            error_message = ""
            auth_token = ""
            account_name = ""
            signup_password_visible = False
            signup_confirmation_visible = False
            password_reset_notice_pending = False
            password_reset_notice_visible = False
            signup_notice_pending = False
            signup_notice_visible = False

        state = State()
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_signup",
                new_callable=AsyncMock,
            ) as request,
        ):
            async def run() -> list[rx.event.EventSpec]:
                events = []
                async for event in LoginState.signup.fn(state, VALID_FORM):
                    events.append(event)
                return events

            events = asyncio.run(run())

        self.assertEqual(state.auth_token, "")
        self.assertEqual(state.signup_email, "pessoa@example.test")
        self.assertEqual(state._signup_password, "senha123")
        self.assertEqual(state.verification_flow, "signup")
        self.assertEqual(state.recovery_resend_seconds, 30)
        self.assertFalse(state.is_loading)
        self.assertEqual(state.error_message, "")
        self.assertTrue(any("/verificar-email" in str(event) for event in events))
        request.assert_awaited_once()
        self.assertEqual(len(request.await_args.args), 7)
        state_fields = LoginState.__own_fields__
        self.assertNotIn("password", state_fields)
        self.assertNotIn("confirm_password", state_fields)
        self.assertNotIn("code", state_fields)
        self.assertNotIn("form_data", state_fields)

    def test_signup_errors_are_generic_and_clear_old_token(self) -> None:
        cases = (
            (
                SignupRejectedError(),
                "Não foi possível iniciar seu cadastro. Confira os dados e tente novamente.",
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
                    account_name = ""
                    signup_password_visible = False
                    signup_confirmation_visible = False
                    password_reset_notice_pending = False
                    password_reset_notice_visible = False
                    signup_notice_pending = False
                    signup_notice_visible = False

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
            account_name = ""
            password_reset_notice_pending = False
            password_reset_notice_visible = False
            signup_notice_pending = False
            signup_notice_visible = False

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

    def test_empty_required_signup_fields_show_site_validation_message(self) -> None:
        class State:
            is_loading = False
            error_message = ""
            auth_token = ""
            account_name = ""
            password_reset_notice_pending = False
            password_reset_notice_visible = False
            signup_notice_pending = False
            signup_notice_visible = False

        state = State()
        with patch("doafacil.login.request_signup") as request:
            async def run() -> None:
                async for _ in LoginState.signup.fn(state, {}):
                    pass

            asyncio.run(run())

        self.assertEqual(state.error_message, "Informe seu nome.")
        self.assertFalse(state.is_loading)
        request.assert_not_called()

    def test_signup_verification_rejects_non_six_digit_code_without_request(self) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            verification_flow = "signup"
            signup_email = "pessoa@example.test"
            _signup_password = "senha123"
            recovery_resend_seconds = 30

        state = State()
        with patch("doafacil.login.request_signup_verification") as request:
            async def run() -> list[object]:
                events = []
                async for event in LoginState.verify_recovery_code.fn(
                    state, {"code": "12345"}
                ):
                    events.append(event)
                return events

            self.assertEqual(asyncio.run(run()), [])

        request.assert_not_called()
        self.assertEqual(state.recovery_error_message, RECOVERY_CODE_ERROR)
        self.assertFalse(hasattr(state, "code"))

    def test_signup_resend_respects_countdown_and_calls_resend_when_ready(self) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            recovery_resend_seconds = 30
            verification_flow = "signup"
            signup_email = "pessoa@example.test"
            _signup_password = "senha123"

        state = State()
        with patch("doafacil.login.request_signup_resend") as request:
            async def run() -> list[object]:
                events = []
                async for event in LoginState.resend_recovery_code.fn(state):
                    events.append(event)
                return events

            self.assertEqual(asyncio.run(run()), [])
        request.assert_not_called()

        state.recovery_resend_seconds = 0
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_signup_resend",
                new_callable=AsyncMock,
            ) as request,
        ):
            async def run_ready() -> list[object]:
                events = []
                async for event in LoginState.resend_recovery_code.fn(state):
                    events.append(event)
                return events

            events = asyncio.run(run_ready())

        request.assert_awaited_once()
        self.assertEqual(state.recovery_resend_seconds, 30)
        self.assertTrue(
            any("countdown_recovery_resend" in str(event) for event in events)
        )

    def test_signup_verification_success_clears_password_and_redirects_without_session(
        self,
    ) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            verification_flow = "signup"
            signup_email = "pessoa@example.test"
            _signup_password = "senha123"
            recovery_resend_seconds = 8
            signup_notice_pending = False
            signup_notice_visible = False
            auth_token = ""

        state = State()
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_signup_verification",
                new_callable=AsyncMock,
            ) as request,
        ):
            async def run() -> list[object]:
                events = []
                async for event in LoginState.verify_recovery_code.fn(
                    state, {"code": "123456"}
                ):
                    events.append(event)
                return events

            events = asyncio.run(run())

        request.assert_awaited_once()
        self.assertEqual(
            request.await_args.args[2:],
            ("pessoa@example.test", "123456", "senha123"),
        )
        self.assertEqual(state.signup_email, "")
        self.assertEqual(state._signup_password, "")
        self.assertEqual(state.verification_flow, "")
        self.assertEqual(state.recovery_resend_seconds, 0)
        self.assertTrue(state.signup_notice_pending)
        self.assertFalse(state.signup_notice_visible)
        self.assertEqual(state.auth_token, "")
        self.assertFalse(state.recovery_is_loading)
        self.assertTrue(any("/login" in str(event) for event in events))
        self.assertFalse(hasattr(state, "code"))

    def test_signup_verification_failure_uses_neutral_and_network_messages(self) -> None:
        cases = (
            (SignupRejectedError(), RECOVERY_CODE_ERROR),
            (SignupUnavailableError(), "Não foi possível conectar ao serviço de autenticação. Tente novamente."),
        )
        for error, expected in cases:
            with self.subTest(error=type(error).__name__):
                class State:
                    recovery_is_loading = False
                    recovery_error_message = ""
                    verification_flow = "signup"
                    signup_email = "pessoa@example.test"
                    _signup_password = "senha123"
                    recovery_resend_seconds = 30

                state = State()
                with (
                    patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
                    patch(
                        "doafacil.login.request_signup_verification",
                        new_callable=AsyncMock,
                        side_effect=error,
                    ),
                ):
                    async def run() -> list[object]:
                        events = []
                        async for event in LoginState.verify_recovery_code.fn(
                            state, {"code": "123456"}
                        ):
                            events.append(event)
                        return events

                    self.assertEqual(asyncio.run(run()), [])

                self.assertEqual(state.recovery_error_message, expected)
                self.assertEqual(state._signup_password, "senha123")
                self.assertFalse(state.recovery_is_loading)

    def test_using_another_signup_email_clears_password_and_flow(self) -> None:
        class State:
            verification_flow = "signup"
            signup_email = "pessoa@example.test"
            _signup_password = "senha123"
            recovery_error_message = "old error"
            recovery_resend_seconds = 12

        state = State()
        LoginState.use_another_recovery_email.fn(state)
        self.assertEqual(state.signup_email, "")
        self.assertEqual(state._signup_password, "")
        self.assertEqual(state.verification_flow, "")
        self.assertEqual(state.recovery_error_message, "")
        self.assertEqual(state.recovery_resend_seconds, 0)

    def test_verification_route_without_state_keeps_recovery_destination(self) -> None:
        class State:
            verification_flow = ""
            recovery_email = ""
            signup_email = ""
            _signup_password = ""

        redirect = LoginState.require_verification_email.fn(State())
        self.assertIn("/recuperar-senha", str(redirect))

    def test_signup_notice_is_consumed_once_and_cleared_on_input(self) -> None:
        class State:
            password_reset_notice_pending = False
            password_reset_notice_visible = False
            signup_notice_pending = True
            signup_notice_visible = False
            signup_email = "pessoa@example.test"
            _signup_password = "senha123"
            verification_flow = "signup"

        state = State()
        LoginState.consume_password_reset_notice.fn(state)
        self.assertTrue(state.signup_notice_visible)
        self.assertFalse(state.signup_notice_pending)
        self.assertEqual(state.signup_email, "")
        self.assertEqual(state._signup_password, "")
        self.assertEqual(state.verification_flow, "")
        LoginState.dismiss_password_reset_notice_on_input.fn(state, "a")
        self.assertFalse(state.signup_notice_visible)
        self.assertFalse(state.signup_notice_pending)
        state.signup_notice_visible = True
        LoginState.consume_password_reset_notice.fn(state)
        self.assertFalse(state.signup_notice_visible)

    def test_login_attempt_and_logout_clear_signup_notice(self) -> None:
        class State:
            is_loading = False
            error_message = ""
            auth_token = ""
            account_name = ""
            password_reset_notice_pending = False
            password_reset_notice_visible = False
            signup_notice_pending = True
            signup_notice_visible = True

        state = State()

        async def login_attempt() -> list[object]:
            events = []
            async for event in LoginState.login.fn(state, {}):
                events.append(event)
            return events

        self.assertEqual(asyncio.run(login_attempt()), [])
        self.assertFalse(state.signup_notice_pending)
        self.assertFalse(state.signup_notice_visible)

        state.signup_notice_pending = True
        state.signup_notice_visible = True
        LoginState.logout.fn(state)
        self.assertFalse(state.signup_notice_pending)
        self.assertFalse(state.signup_notice_visible)

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
    def test_login_displays_transient_signup_confirmation_notice(self) -> None:
        from doafacil.login import login_page

        page = login_page()
        self.assertIn(
            "Cadastro confirmado! Você já pode entrar com seu e-mail e sua senha.",
            _component_text(page),
        )
        self.assertIn("signup_notice_visible", str(page))

    def test_verification_page_supports_both_flows_and_destinations(self) -> None:
        page = verify_recovery_page()
        contents = _component_text(page)
        self.assertIn(
            "Se for possível confirmar este e-mail, enviaremos um código "
            "de 6 dígitos para",
            contents,
        )
        self.assertIn(
            "Se existir uma conta com esse e-mail, enviamos um código "
            "de 6 dígitos para",
            contents,
        )

        links = {
            _component_text(node): node
            for node in _component_nodes(page)
            if type(node).__name__ == "Link"
        }
        for label in ("← Voltar", "Usar outro e-mail"):
            self.assertIn(label, links)
            self.assertIn("/cadastro", str(links[label]))
            self.assertIn("/recuperar-senha", str(links[label]))
        self.assertIn("leave_verification_for_signup", str(links["← Voltar"]))
        self.assertIn(
            "use_another_recovery_email",
            str(links["Usar outro e-mail"]),
        )

    def test_verification_page_code_is_not_bound_to_reflex_state(self) -> None:
        code = next(
            node
            for node in _component_nodes(verify_recovery_page())
            if getattr(getattr(node, "name", None), "_var_value", None) == "code"
        )
        self.assertIsNone(getattr(code, "value", None))
        self.assertNotIn("code", LoginState.__own_fields__)

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

    def test_signup_animation_class_is_applied_only_to_the_card(self) -> None:
        nodes = _component_nodes(signup_page())
        animated_nodes = [
            node
            for node in nodes
            if getattr(node, "class_name", None) == "auth-card-enter"
        ]
        self.assertEqual(len(animated_nodes), 1)
        self.assertEqual(animated_nodes[0].background, "white")
        self.assertTrue(
            all(
                getattr(node, "class_name", None) != "auth-card-enter"
                for node in nodes
                if node is not animated_nodes[0]
            )
        )

    def test_signup_form_uses_site_validation_instead_of_native_validation(self) -> None:
        nodes = _component_nodes(signup_page())
        form = next(node for node in nodes if type(node).__name__ == "Form")
        self.assertTrue(
            getattr(form.no_validate, "_var_value", form.no_validate)
        )
        fields = [
            node
            for node in nodes
            if type(node).__name__ == "TextFieldRoot"
        ]
        self.assertTrue(
            all(getattr(field.required, "_var_value", field.required) for field in fields)
        )

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

    def test_login_and_signup_fields_have_scoped_autofill_styles(self) -> None:
        autofill_rules = [
            (selector, styles)
            for selector, styles in app.style.items()
            if ":-webkit-autofill" in selector
        ]
        self.assertEqual(len(autofill_rules), 1)
        selector, styles = autofill_rules[0]
        for field_id in (
            "login-email",
            "login-password",
            "signup-name",
            "signup-email",
            "signup-city",
            "signup-password",
            "signup-confirm-password",
        ):
            self.assertIn(f"#{field_id}:-webkit-autofill", selector)
            self.assertIn(f"#{field_id}:-webkit-autofill:hover", selector)
            self.assertIn(f"#{field_id}:-webkit-autofill:focus", selector)
        self.assertEqual(styles["background_color"], "white")
        self.assertEqual(styles["WebkitTextFillColor"], "#2b2b2b")
        self.assertIn("white inset", styles["box_shadow"])
        self.assertNotIn("public-home-search", selector)


if __name__ == "__main__":
    unittest.main()
