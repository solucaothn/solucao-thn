import asyncio
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx

from doafacil.doafacil import app
from doafacil.login import (
    AUTH_API_ENV,
    RECOVERY_CODE_ERROR,
    RECOVERY_UNAVAILABLE_MESSAGE,
    LoginConfigurationError,
    LoginState,
    PasswordRecoveryUnavailableError,
    RecoveryCodeRejectedError,
    RecoveryTokenRejectedError,
    RecoveryTokenResult,
    password_reset_confirm_endpoint,
    password_reset_request_endpoint,
    password_reset_verify_endpoint,
    request_password_reset_code,
    request_password_reset_confirmation,
    request_password_reset_verification,
    validate_recovery_password,
)
from doafacil.recuperacao_senha import (
    new_password_page,
    request_recovery_page,
    verify_recovery_page,
)


VALID_RESET_FORM = {
    "password": "senha123",
    "password_confirmation": "senha123",
}


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


class RecoveryClientTests(unittest.TestCase):
    def test_endpoint_paths_reuse_the_validated_auth_environment(self) -> None:
        with patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api/"}):
            self.assertEqual(
                password_reset_request_endpoint(),
                "https://auth.example/api/reset/request_code",
            )
            self.assertEqual(
                password_reset_verify_endpoint(),
                "https://auth.example/api/reset/verify_code",
            )
            self.assertEqual(
                password_reset_confirm_endpoint(),
                "https://auth.example/api/reset/confirm_password",
            )

        with patch.dict(os.environ, {AUTH_API_ENV: "invalid"}):
            with self.assertRaises(LoginConfigurationError):
                password_reset_request_endpoint()

    def test_helpers_send_only_the_defined_xano_payloads(self) -> None:
        observed: list[tuple[str, bytes]] = []

        async def respond(request: httpx.Request) -> httpx.Response:
            observed.append((request.url.path, request.read()))
            if request.url.path.endswith("verify_code"):
                return httpx.Response(
                    200, json={"success": True, "reset_token": "ephemeral-token"}
                )
            return httpx.Response(200, json={"success": True})

        async def run() -> RecoveryTokenResult:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await request_password_reset_code(
                    client,
                    "https://auth.example/reset/request_code",
                    "person@example.test",
                )
                result = await request_password_reset_verification(
                    client,
                    "https://auth.example/reset/verify_code",
                    "person@example.test",
                    "123456",
                )
                await request_password_reset_confirmation(
                    client,
                    "https://auth.example/reset/confirm_password",
                    "ephemeral-token",
                    "senha123",
                    "senha123",
                )
                return result

        result = asyncio.run(run())
        self.assertEqual(
            observed,
            [
                (
                    "/reset/request_code",
                    b'{"email":"person@example.test"}',
                ),
                (
                    "/reset/verify_code",
                    b'{"email":"person@example.test","code":"123456"}',
                ),
                (
                    "/reset/confirm_password",
                    b'{"reset_token":"ephemeral-token","password":"senha123",'
                    b'"password_confirmation":"senha123"}',
                ),
            ],
        )
        self.assertEqual(result.reset_token, "ephemeral-token")
        self.assertNotIn("ephemeral-token", repr(result))

    def test_rejected_responses_have_generic_secret_free_errors(self) -> None:
        async def reject(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("verify_code"):
                return httpx.Response(200, json={"success": False})
            return httpx.Response(200, json={"success": False})

        async def run_verification() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(reject)
            ) as client:
                await request_password_reset_verification(
                    client,
                    "https://auth.example/reset/verify_code",
                    "person@example.test",
                    "000000",
                )

        async def run_confirmation() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(reject)
            ) as client:
                await request_password_reset_confirmation(
                    client,
                    "https://auth.example/reset/confirm_password",
                    "private-token",
                    "senha123",
                    "senha123",
                )

        with self.assertRaises(RecoveryCodeRejectedError) as code_error:
            asyncio.run(run_verification())
        with self.assertRaises(RecoveryTokenRejectedError) as token_error:
            asyncio.run(run_confirmation())
        self.assertEqual(str(code_error.exception), "")
        self.assertEqual(str(token_error.exception), "")
        self.assertNotIn("private-token", str(token_error.exception))

    def test_network_and_malformed_responses_are_sanitized(self) -> None:
        async def fail_network(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("private transport detail", request=request)

        async def malformed(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"unexpected": "private detail"})

        async def call(handler: object) -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                await request_password_reset_code(
                    client,
                    "https://auth.example/reset/request_code",
                    "private@example.test",
                )

        for handler in (fail_network, malformed):
            with self.subTest(handler=handler.__name__):
                with self.assertRaises(PasswordRecoveryUnavailableError) as raised:
                    asyncio.run(call(handler))
                self.assertNotIn("private", str(raised.exception))


class RecoveryStateTests(unittest.TestCase):
    def test_password_validation_matches_signup_rules(self) -> None:
        cases = (
            ("a123456", "a123456", "A senha deve ter pelo menos 8 caracteres."),
            ("abcdefgh", "abcdefgh", "A senha deve conter pelo menos um número."),
            ("12345678", "12345678", "A senha deve conter pelo menos uma letra."),
            ("senha123", "senha456", "As senhas não coincidem."),
        )
        for password, confirmation, message in cases:
            with self.subTest(password=password):
                self.assertEqual(
                    validate_recovery_password(password, confirmation), message
                )
        self.assertEqual(validate_recovery_password("senha123", "senha123"), "")

    def test_login_state_contains_no_code_or_password_fields(self) -> None:
        fields = LoginState.__own_fields__
        for forbidden in ("code", "password", "password_confirmation", "form_data"):
            self.assertNotIn(forbidden, fields)
        self.assertIn("recovery_email", fields)
        self.assertIn("_reset_token", fields)
        self.assertNotIn("_reset_token", LoginState.vars)

    def test_request_success_stores_email_sets_timer_and_advances(self) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            recovery_email = ""
            recovery_resend_seconds = 0

        state = State()
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_password_reset_code",
                new_callable=AsyncMock,
            ) as request,
        ):
            async def run() -> list[object]:
                events = []
                async for event in LoginState.request_recovery_code.fn(
                    state, {"email": " person@example.test "}
                ):
                    events.append(event)
                return events

            events = asyncio.run(run())

        request.assert_awaited_once()
        self.assertEqual(state.recovery_email, "person@example.test")
        self.assertEqual(state.recovery_resend_seconds, 30)
        self.assertFalse(state.recovery_is_loading)
        self.assertTrue(any("/verificar-email" in str(event) for event in events))
        self.assertTrue(
            any("countdown_recovery_resend" in str(event) for event in events)
        )

    def test_recovery_request_failure_is_neutral_and_keeps_form_available(self) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            recovery_email = ""
            recovery_resend_seconds = 0

        state = State()
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_password_reset_code",
                new_callable=AsyncMock,
                side_effect=PasswordRecoveryUnavailableError(),
            ),
        ):
            async def run() -> list[object]:
                events = []
                async for event in LoginState.request_recovery_code.fn(
                    state, {"email": "person@example.test"}
                ):
                    events.append(event)
                return events

            events = asyncio.run(run())

        self.assertEqual(events, [])
        self.assertEqual(state.recovery_error_message, RECOVERY_UNAVAILABLE_MESSAGE)
        self.assertEqual(state.recovery_email, "")
        self.assertFalse(state.recovery_is_loading)

    def test_recovery_request_blocks_duplicate_submission(self) -> None:
        class State:
            recovery_is_loading = True
            recovery_error_message = ""
            recovery_email = ""
            recovery_resend_seconds = 0

        state = State()
        with patch("doafacil.login.request_password_reset_code") as request:
            async def run() -> list[object]:
                events = []
                async for event in LoginState.request_recovery_code.fn(
                    state, {"email": "person@example.test"}
                ):
                    events.append(event)
                return events

            self.assertEqual(asyncio.run(run()), [])
        request.assert_not_called()

    def test_verification_rejection_uses_one_generic_message(self) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            recovery_email = "person@example.test"
            _reset_token = ""

        state = State()
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_password_reset_verification",
                new_callable=AsyncMock,
                side_effect=RecoveryCodeRejectedError(),
            ),
        ):
            async def run() -> list[object]:
                events = []
                async for event in LoginState.verify_recovery_code.fn(
                    state, {"code": "123456"}
                ):
                    events.append(event)
                return events

            events = asyncio.run(run())

        self.assertEqual(events, [])
        self.assertEqual(state.recovery_error_message, RECOVERY_CODE_ERROR)
        self.assertFalse(state.recovery_is_loading)

    def test_verification_success_keeps_token_only_in_state_and_redirects(self) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            recovery_email = "person@example.test"
            _reset_token = ""

        state = State()
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_password_reset_verification",
                new_callable=AsyncMock,
                return_value=RecoveryTokenResult("ephemeral-token"),
            ),
        ):
            async def run() -> list[object]:
                events = []
                async for event in LoginState.verify_recovery_code.fn(
                    state, {"code": "123456"}
                ):
                    events.append(event)
                return events

            events = asyncio.run(run())

        self.assertEqual(state._reset_token, "ephemeral-token")
        self.assertFalse(state.recovery_is_loading)
        self.assertTrue(any("/nova-senha" in str(event) for event in events))
        self.assertNotIn("ephemeral-token", str(events))

    def test_invalid_password_is_rejected_before_request(self) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            _reset_token = "ephemeral-token"

        state = State()
        with patch("doafacil.login.request_password_reset_confirmation") as request:
            async def run() -> None:
                async for _ in LoginState.confirm_recovery_password.fn(
                    state,
                    {"password": "weak", "password_confirmation": "weak"},
                ):
                    pass

            asyncio.run(run())

        request.assert_not_called()
        self.assertEqual(
            state.recovery_error_message,
            "A senha deve ter pelo menos 8 caracteres.",
        )

    def test_confirmation_success_clears_flow_and_arms_one_time_notice(self) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            _reset_token = "ephemeral-token"
            recovery_email = "person@example.test"
            recovery_resend_seconds = 30
            password_reset_notice_pending = False
            password_reset_notice_visible = False

        state = State()
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_password_reset_confirmation",
                new_callable=AsyncMock,
            ),
        ):
            async def run() -> list[object]:
                events = []
                async for event in LoginState.confirm_recovery_password.fn(
                    state, VALID_RESET_FORM
                ):
                    events.append(event)
                return events

            events = asyncio.run(run())

        self.assertEqual(state._reset_token, "")
        self.assertEqual(state.recovery_email, "")
        self.assertEqual(state.recovery_resend_seconds, 0)
        self.assertTrue(state.password_reset_notice_pending)
        self.assertFalse(state.password_reset_notice_visible)
        self.assertFalse(state.recovery_is_loading)
        self.assertTrue(any("/login" in str(event) for event in events))

    def test_token_rejection_clears_flow_and_shows_recovery_link_message(self) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            _reset_token = "ephemeral-token"
            recovery_email = "person@example.test"

        state = State()
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_password_reset_confirmation",
                new_callable=AsyncMock,
                side_effect=RecoveryTokenRejectedError(),
            ),
        ):
            async def run() -> None:
                async for _ in LoginState.confirm_recovery_password.fn(
                    state, VALID_RESET_FORM
                ):
                    pass

            asyncio.run(run())

        self.assertEqual(state._reset_token, "")
        self.assertEqual(state.recovery_email, "")
        self.assertEqual(
            state.recovery_error_message,
            "O tempo para trocar a senha acabou. Peça um novo código.",
        )

    def test_notice_is_consumed_and_dismissed_on_input(self) -> None:
        class State:
            password_reset_notice_pending = True
            password_reset_notice_visible = False

        state = State()
        LoginState.consume_password_reset_notice.fn(state)
        self.assertTrue(state.password_reset_notice_visible)
        self.assertFalse(state.password_reset_notice_pending)
        LoginState.dismiss_password_reset_notice_on_input.fn(state, "a")
        self.assertFalse(state.password_reset_notice_visible)
        self.assertFalse(state.password_reset_notice_pending)
        state.password_reset_notice_visible = True
        LoginState.consume_password_reset_notice.fn(state)
        self.assertFalse(state.password_reset_notice_visible)

    def test_using_another_email_clears_email_token_and_timer(self) -> None:
        class State:
            recovery_email = "person@example.test"
            _reset_token = "ephemeral-token"
            recovery_error_message = "old error"
            recovery_resend_seconds = 12

        state = State()
        LoginState.use_another_recovery_email.fn(state)
        self.assertEqual(state.recovery_email, "")
        self.assertEqual(state._reset_token, "")
        self.assertEqual(state.recovery_error_message, "")
        self.assertEqual(state.recovery_resend_seconds, 0)

    def test_returning_to_login_clears_the_abandoned_recovery(self) -> None:
        class State:
            recovery_email = "person@example.test"
            _reset_token = "ephemeral-token"
            recovery_error_message = "old error"
            recovery_resend_seconds = 12
            recovery_password_visible = True
            recovery_confirmation_visible = True
            password_reset_notice_pending = False
            password_reset_notice_visible = False

        state = State()
        LoginState.return_to_login.fn(state)
        self.assertEqual(state.recovery_email, "")
        self.assertEqual(state._reset_token, "")
        self.assertEqual(state.recovery_resend_seconds, 0)
        self.assertFalse(state.recovery_password_visible)
        self.assertFalse(state.recovery_confirmation_visible)

    def test_resend_is_blocked_by_server_event_state_until_timer_reaches_zero(
        self,
    ) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            recovery_email = "person@example.test"
            recovery_resend_seconds = 10

        state = State()
        with patch("doafacil.login.request_password_reset_code") as request:
            async def run() -> list[object]:
                events = []
                async for event in LoginState.resend_recovery_code.fn(state):
                    events.append(event)
                return events

            self.assertEqual(asyncio.run(run()), [])
        request.assert_not_called()

    def test_resend_success_resets_timer_and_starts_background_event(self) -> None:
        class State:
            recovery_is_loading = False
            recovery_error_message = ""
            recovery_email = "person@example.test"
            recovery_resend_seconds = 0

        state = State()
        with (
            patch.dict(os.environ, {AUTH_API_ENV: "https://auth.example/api"}),
            patch(
                "doafacil.login.request_password_reset_code",
                new_callable=AsyncMock,
            ) as request,
        ):
            async def run() -> list[object]:
                events = []
                async for event in LoginState.resend_recovery_code.fn(state):
                    events.append(event)
                return events

            events = asyncio.run(run())

        request.assert_awaited_once()
        self.assertEqual(state.recovery_resend_seconds, 30)
        self.assertTrue(
            any("countdown_recovery_resend" in str(event) for event in events)
        )

    def test_countdown_background_event_reaches_zero(self) -> None:
        class State:
            recovery_countdown_running = False
            recovery_resend_seconds = 3

            async def __aenter__(self) -> "State":
                return self

            async def __aexit__(self, *args: object) -> None:
                return None

        state = State()
        with patch("doafacil.login.asyncio.sleep", new_callable=AsyncMock):
            asyncio.run(LoginState.countdown_recovery_resend.fn(state))
        self.assertEqual(state.recovery_resend_seconds, 0)
        self.assertFalse(state.recovery_countdown_running)

    def test_recovery_route_gates_redirect_without_prerequisites(self) -> None:
        class State:
            recovery_email = ""
            _reset_token = ""

        state = State()
        self.assertIn(
            "/recuperar-senha",
            str(LoginState.require_recovery_email.fn(state)),
        )
        self.assertIn(
            "/recuperar-senha",
            str(LoginState.require_reset_token.fn(state)),
        )

    def test_signup_navigation_clears_transient_notice(self) -> None:
        class State:
            password_reset_notice_pending = True
            password_reset_notice_visible = True

        state = State()
        event = LoginState.navigate_to_signup_from_login.fn(state)
        self.assertIn("/cadastro", str(event))
        self.assertFalse(state.password_reset_notice_pending)
        self.assertFalse(state.password_reset_notice_visible)


class RecoveryPageTests(unittest.TestCase):
    def test_recovery_routes_are_registered_with_state_gates(self) -> None:
        routes = {
            page.route: page
            for page in app._unevaluated_pages.values()
        }
        self.assertIn("recuperar-senha", routes)
        self.assertIn("verificar-email", routes)
        self.assertIn("nova-senha", routes)
        self.assertTrue(routes["verificar-email"].on_load)
        self.assertTrue(routes["nova-senha"].on_load)

    def test_screens_have_expected_content_and_auth_card_animation(self) -> None:
        cases = (
            (
                request_recovery_page(),
                ("Esqueceu a senha?", "E-mail", "Continuar", "← Voltar"),
                ("recovery-email",),
            ),
            (
                verify_recovery_page(),
                (
                    "Verifique seu e-mail",
                    "Código",
                    "Pode demorar um minutinho. Olha também no spam.",
                    "Reenviar código",
                    "Usar outro e-mail",
                ),
                ("recovery-code",),
            ),
            (
                new_password_page(),
                (
                    "Altere sua senha",
                    "Nova senha",
                    "Confirmar senha",
                    "Salvar nova senha",
                ),
                ("recovery-password", "recovery-password-confirmation"),
            ),
        )
        for page, expected_text, expected_ids in cases:
            with self.subTest(text=expected_text[0]):
                contents = f"{_component_text(page)} {page}"
                for text in expected_text:
                    self.assertIn(text, contents)
                nodes = _component_nodes(page)
                cards = [
                    node
                    for node in nodes
                    if getattr(node, "class_name", None) == "auth-card-enter"
                ]
                self.assertEqual(len(cards), 1)
                input_ids = {
                    getattr(node.id, "_var_value", node.id)
                    for node in nodes
                    if getattr(node, "id", None) is not None
                }
                for field_id in expected_ids:
                    self.assertIn(field_id, input_ids)
                forms = [
                    node for node in nodes if type(node).__name__ == "Form"
                ]
                self.assertEqual(len(forms), 1)
                self.assertIn("on_submit", forms[0].event_triggers)
                submit_buttons = [
                    node
                    for node in nodes
                    if getattr(getattr(node, "type", None), "_var_value", None)
                    == "submit"
                ]
                self.assertEqual(len(submit_buttons), 1)
                self.assertIn(
                    "recovery_is_loading",
                    str(submit_buttons[0].disabled),
                )

        for page in (request_recovery_page(), new_password_page()):
            back_link = next(
                node
                for node in _component_nodes(page)
                if type(node).__name__ == "Link"
                and _component_text(node) == "← Voltar"
            )
            self.assertIn("/login", str(back_link))

    def test_password_visibility_controls_are_independent_and_accessible(self) -> None:
        nodes = _component_nodes(new_password_page())
        buttons = [
            node
            for node in nodes
            if getattr(getattr(node, "type", None), "_var_value", None) == "button"
            and "aria-label" in getattr(node, "custom_attrs", {})
        ]
        self.assertEqual(len(buttons), 2)
        for button in buttons:
            accessible_label = str(button.custom_attrs["aria-label"])
            self.assertIn("Mostrar senha", accessible_label)
            self.assertIn("Ocultar senha", accessible_label)

    def test_login_has_accessible_success_notice_and_recovery_link(self) -> None:
        from doafacil.login import login_page

        nodes = _component_nodes(login_page())
        self.assertTrue(
            any(
                "status" in str(getattr(node, "role", ""))
                or "status" in str(
                    getattr(node, "custom_attrs", {}).get("role", "")
                )
                for node in nodes
            )
        )
        forgot = next(
            node
            for node in nodes
            if _component_text(node) == "Esqueci minha senha"
        )
        self.assertIn("/recuperar-senha", str(forgot))

    def test_recovery_autofill_styles_and_design_documentation(self) -> None:
        css_file = Path(__file__).parents[1] / "doafacil" / "doafacil.py"
        source = css_file.read_text(encoding="utf-8")
        for field_id in (
            "recovery-email",
            "recovery-code",
            "recovery-password",
            "recovery-password-confirmation",
        ):
            self.assertIn(f"#{field_id}:-webkit-autofill", source)
            self.assertIn(f"#{field_id}::placeholder", source)

        readme = (
            Path(__file__).parents[1] / "docs" / "design" / "README.md"
        ).read_text(encoding="utf-8")
        for heading in (
            "### 11-esqueci-senha.png",
            "### 12-verifique-email.png",
            "### 13-nova-senha.png",
        ):
            self.assertIn(heading, readme)
        self.assertIn("não estão no Figma", readme)

    def test_recovery_links_preserve_or_clear_the_email_as_required(self) -> None:
        nodes = _component_nodes(verify_recovery_page())
        links = {
            _component_text(node): node
            for node in nodes
            if type(node).__name__ == "Link"
        }
        self.assertIn("← Voltar", links)
        self.assertIn("/recuperar-senha", str(links["← Voltar"]))
        self.assertIn("Usar outro e-mail", links)
        self.assertIn("use_another_recovery_email", str(links["Usar outro e-mail"]))
