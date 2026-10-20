import asyncio
import os
import re
from collections.abc import AsyncGenerator, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx
import reflex as rx


AUTH_API_ENV = "XANO_AUTH_API_URL"
AUTH_LOGIN_PATH = "/auth/login"
AUTH_SIGNUP_PATH = "/auth/signup"
AUTH_ME_PATH = "/auth/me"
PASSWORD_RESET_REQUEST_PATH = "/reset/request_code"
PASSWORD_RESET_VERIFY_PATH = "/reset/verify_code"
PASSWORD_RESET_CONFIRM_PATH = "/reset/confirm_password"
ACCOUNT_FALLBACK_NAME = "Minha conta"
DUPLICATE_SIGNUP_MESSAGE = "An account with this email already exists."
RECOVERY_CODE_ERROR = (
    "Código inválido ou vencido. Confira e tente de novo, ou peça um novo código."
)
RECOVERY_UNAVAILABLE_MESSAGE = (
    "Não foi possível conectar ao serviço de autenticação. Tente novamente."
)


class LoginError(Exception):
    pass


class LoginConfigurationError(LoginError):
    pass


class InvalidCredentialsError(LoginError):
    pass


class LoginUnavailableError(LoginError):
    pass


class SignupError(LoginError):
    pass


class EmailAlreadyRegisteredError(SignupError):
    pass


class SignupRejectedError(SignupError):
    pass


class SignupUnavailableError(SignupError):
    pass


class AuthTokenRejectedError(LoginError):
    pass


class AuthAccountUnavailableError(LoginError):
    pass


class PasswordRecoveryError(LoginError):
    pass


class PasswordRecoveryUnavailableError(PasswordRecoveryError):
    pass


class RecoveryCodeRejectedError(PasswordRecoveryError):
    pass


class RecoveryTokenRejectedError(PasswordRecoveryError):
    pass


@dataclass(frozen=True, repr=False)
class LoginResult:
    auth_token: str
    user_id: int


@dataclass(frozen=True, repr=False)
class SignupResult:
    auth_token: str
    user_id: int


@dataclass(frozen=True, repr=False)
class RecoveryTokenResult:
    reset_token: str


def login_error_message(error: LoginError) -> str:
    if isinstance(error, InvalidCredentialsError):
        return "E-mail ou senha incorretos."
    return (
        "Não foi possível conectar ao serviço de autenticação. "
        "Tente novamente."
    )


def signup_error_message(error: LoginError) -> str:
    if isinstance(error, EmailAlreadyRegisteredError):
        return "Este e-mail já está cadastrado."
    if isinstance(error, (SignupUnavailableError, LoginConfigurationError)):
        return (
            "Não foi possível conectar ao serviço de autenticação. "
            "Tente novamente."
        )
    return "Não foi possível criar sua conta. Confira os dados e tente novamente."


def _auth_api_endpoint(path: str) -> str:
    base_url = os.getenv(AUTH_API_ENV, "").strip()
    try:
        parsed_url = urlsplit(base_url)
        valid_port = parsed_url.port is None or 1 <= parsed_url.port <= 65535
    except ValueError:
        valid_port = False
        parsed_url = urlsplit("")

    if (
        parsed_url.scheme not in {"http", "https"}
        or not parsed_url.hostname
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.query
        or parsed_url.fragment
        or not valid_port
    ):
        raise LoginConfigurationError from None

    return f"{base_url.rstrip('/')}{path}"


def auth_login_endpoint() -> str:
    return _auth_api_endpoint(AUTH_LOGIN_PATH)


def auth_signup_endpoint() -> str:
    return _auth_api_endpoint(AUTH_SIGNUP_PATH)


def auth_me_endpoint() -> str:
    return _auth_api_endpoint(AUTH_ME_PATH)


def password_reset_request_endpoint() -> str:
    return _auth_api_endpoint(PASSWORD_RESET_REQUEST_PATH)


def password_reset_verify_endpoint() -> str:
    return _auth_api_endpoint(PASSWORD_RESET_VERIFY_PATH)


def password_reset_confirm_endpoint() -> str:
    return _auth_api_endpoint(PASSWORD_RESET_CONFIRM_PATH)


async def request_password_reset_code(
    client: httpx.AsyncClient, endpoint: str, email: str
) -> None:
    try:
        response = await client.post(endpoint, json={"email": email})
    except httpx.RequestError:
        raise PasswordRecoveryUnavailableError from None

    if response.is_error:
        raise PasswordRecoveryUnavailableError from None
    try:
        payload = response.json()
    except ValueError:
        raise PasswordRecoveryUnavailableError from None
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise PasswordRecoveryUnavailableError from None


async def request_password_reset_verification(
    client: httpx.AsyncClient,
    endpoint: str,
    email: str,
    code: str,
) -> RecoveryTokenResult:
    try:
        response = await client.post(
            endpoint, json={"email": email, "code": code}
        )
    except httpx.RequestError:
        raise PasswordRecoveryUnavailableError from None

    if response.is_error:
        raise PasswordRecoveryUnavailableError from None
    try:
        payload = response.json()
    except ValueError:
        raise PasswordRecoveryUnavailableError from None
    if not isinstance(payload, dict):
        raise PasswordRecoveryUnavailableError from None
    if payload.get("success") is False:
        raise RecoveryCodeRejectedError from None

    reset_token = payload.get("reset_token")
    if (
        payload.get("success") is not True
        or not isinstance(reset_token, str)
        or not reset_token
    ):
        raise PasswordRecoveryUnavailableError from None
    return RecoveryTokenResult(reset_token=reset_token)


async def request_password_reset_confirmation(
    client: httpx.AsyncClient,
    endpoint: str,
    reset_token: str,
    password: str,
    password_confirmation: str,
) -> None:
    try:
        response = await client.post(
            endpoint,
            json={
                "reset_token": reset_token,
                "password": password,
                "password_confirmation": password_confirmation,
            },
        )
    except httpx.RequestError:
        raise PasswordRecoveryUnavailableError from None

    if response.is_error:
        raise PasswordRecoveryUnavailableError from None
    try:
        payload = response.json()
    except ValueError:
        raise PasswordRecoveryUnavailableError from None
    if not isinstance(payload, dict):
        raise PasswordRecoveryUnavailableError from None
    if payload.get("success") is False:
        raise RecoveryTokenRejectedError from None
    if payload.get("success") is not True:
        raise PasswordRecoveryUnavailableError from None


async def request_authenticated_name(
    client: httpx.AsyncClient, endpoint: str, auth_token: str
) -> str:
    try:
        response = await client.get(
            endpoint,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
    except httpx.RequestError:
        raise AuthAccountUnavailableError from None

    if response.status_code in {401, 403}:
        raise AuthTokenRejectedError from None
    if response.is_error:
        raise AuthAccountUnavailableError from None

    try:
        payload = response.json()
    except ValueError:
        raise AuthAccountUnavailableError from None

    if not isinstance(payload, dict):
        raise AuthAccountUnavailableError from None

    name = payload.get("name")
    if not isinstance(name, str):
        raise AuthAccountUnavailableError from None
    first_name = name.strip().split(maxsplit=1)
    return first_name[0] if first_name else ACCOUNT_FALLBACK_NAME


async def request_login(
    client: httpx.AsyncClient,
    endpoint: str,
    email: str,
    password: str,
) -> LoginResult:
    try:
        response = await client.post(
            endpoint,
            json={"email": email, "password": password},
        )
    except httpx.RequestError:
        raise LoginUnavailableError from None

    if response.status_code in {401, 403}:
        raise InvalidCredentialsError from None
    if response.is_error:
        raise LoginUnavailableError from None

    try:
        payload = response.json()
    except ValueError:
        raise LoginUnavailableError from None

    if not isinstance(payload, dict):
        raise LoginUnavailableError from None

    auth_token = payload.get("authToken")
    user_id = payload.get("user_id")
    if (
        not isinstance(auth_token, str)
        or not auth_token
        or isinstance(user_id, bool)
        or not isinstance(user_id, int)
    ):
        raise LoginUnavailableError from None

    return LoginResult(auth_token=auth_token, user_id=user_id)


def _contains_duplicate_signup_message(value: object) -> bool:
    if isinstance(value, str):
        return value.strip() == DUPLICATE_SIGNUP_MESSAGE
    if isinstance(value, Mapping):
        return any(
            _contains_duplicate_signup_message(item)
            for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_duplicate_signup_message(item) for item in value)
    return False


async def request_signup(
    client: httpx.AsyncClient,
    endpoint: str,
    name: str,
    email: str,
    password: str,
    city: str,
    state: str,
) -> SignupResult:
    try:
        response = await client.post(
            endpoint,
            json={
                "name": name.strip(),
                "email": email.strip(),
                "password": password,
                "city": city.strip(),
                "state": state.strip(),
            },
        )
    except httpx.RequestError:
        raise SignupUnavailableError from None

    try:
        payload = response.json()
    except ValueError:
        payload = None

    if response.is_error:
        if _contains_duplicate_signup_message(payload):
            raise EmailAlreadyRegisteredError from None
        raise SignupRejectedError from None

    if not isinstance(payload, dict):
        raise SignupUnavailableError from None

    auth_token = payload.get("authToken")
    user_id = payload.get("user_id")
    if (
        not isinstance(auth_token, str)
        or not auth_token
        or isinstance(user_id, bool)
        or not isinstance(user_id, int)
    ):
        raise SignupUnavailableError from None

    return SignupResult(auth_token=auth_token, user_id=user_id)


def validate_signup_data(form_data: Mapping[str, object]) -> str:
    required_fields = (
        ("name", "Informe seu nome."),
        ("email", "Informe seu e-mail."),
        ("city", "Informe sua cidade."),
        ("state", "Selecione seu estado."),
        ("password", "Informe sua senha."),
        ("confirm_password", "Confirme sua senha."),
    )
    values: dict[str, str] = {}
    for name, _ in required_fields:
        value = form_data.get(name)
        if isinstance(value, str):
            values[name] = value.strip()

    for name, message in required_fields:
        if not values.get(name):
            return message

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", values["email"]):
        return "Informe um e-mail válido."

    password = form_data.get("password")
    confirm_password = form_data.get("confirm_password")
    if not isinstance(password, str) or len(password) < 8:
        return "A senha deve ter pelo menos 8 caracteres."
    if not any(character.isalpha() for character in password):
        return "A senha deve conter pelo menos uma letra."
    if not any(character.isdigit() for character in password):
        return "A senha deve conter pelo menos um número."
    if password != confirm_password:
        return "As senhas não coincidem."
    return ""


def validate_recovery_password(
    password: object, password_confirmation: object
) -> str:
    if not isinstance(password, str) or not password:
        return "Informe sua senha."
    if not isinstance(password_confirmation, str) or not password_confirmation:
        return "Confirme sua senha."
    if len(password) < 8:
        return "A senha deve ter pelo menos 8 caracteres."
    if not any(character.isalpha() for character in password):
        return "A senha deve conter pelo menos uma letra."
    if not any(character.isdigit() for character in password):
        return "A senha deve conter pelo menos um número."
    if password != password_confirmation:
        return "As senhas não coincidem."
    return ""


class LoginState(rx.State):
    is_loading: bool = False
    error_message: str = ""
    auth_token: str = ""
    account_name: str = ""
    password_visible: bool = False
    signup_password_visible: bool = False
    signup_confirmation_visible: bool = False
    recovery_email: str = ""
    _reset_token: str = ""
    recovery_error_message: str = ""
    recovery_is_loading: bool = False
    recovery_resend_seconds: int = 0
    recovery_countdown_running: bool = False
    recovery_password_visible: bool = False
    recovery_confirmation_visible: bool = False
    password_reset_notice_pending: bool = False
    password_reset_notice_visible: bool = False

    @rx.var
    def masked_recovery_email(self) -> str:
        if "@" not in self.recovery_email:
            return ""
        local_part, domain = self.recovery_email.split("@", maxsplit=1)
        if not local_part or not domain:
            return ""
        return f"{local_part[0]}***@{domain}"

    @rx.var
    def recovery_resend_label(self) -> str:
        return f"Reenviar código em 0:{self.recovery_resend_seconds:02d}"

    @rx.event
    def consume_password_reset_notice(self) -> None:
        self.password_reset_notice_visible = self.password_reset_notice_pending
        self.password_reset_notice_pending = False
        self.recovery_email = ""
        self._reset_token = ""
        self.recovery_error_message = ""
        self.recovery_resend_seconds = 0

    @rx.event
    def clear_password_reset_notice(self) -> None:
        self.password_reset_notice_pending = False
        self.password_reset_notice_visible = False

    @rx.event
    def dismiss_password_reset_notice_on_input(self, value: str) -> None:
        self.password_reset_notice_pending = False
        self.password_reset_notice_visible = False

    @rx.event
    def navigate_to_signup_from_login(self) -> rx.event.EventSpec:
        self.password_reset_notice_pending = False
        self.password_reset_notice_visible = False
        return rx.redirect("/cadastro")

    @rx.event
    def set_recovery_email(self, value: str) -> None:
        self.recovery_email = value
        self.recovery_error_message = ""

    @rx.event
    def require_recovery_email(self) -> rx.event.EventSpec | None:
        if not self.recovery_email:
            return rx.redirect("/recuperar-senha")
        return None

    @rx.event
    def require_reset_token(self) -> rx.event.EventSpec | None:
        if not self._reset_token:
            return rx.redirect("/recuperar-senha")
        return None

    @rx.event
    def use_another_recovery_email(self) -> None:
        self.recovery_email = ""
        self._reset_token = ""
        self.recovery_error_message = ""
        self.recovery_resend_seconds = 0

    @rx.event
    def return_to_login(self) -> None:
        self.recovery_email = ""
        self._reset_token = ""
        self.recovery_error_message = ""
        self.recovery_resend_seconds = 0
        self.recovery_password_visible = False
        self.recovery_confirmation_visible = False
        self.password_reset_notice_pending = False
        self.password_reset_notice_visible = False

    @rx.event
    def toggle_recovery_password_visibility(self) -> None:
        self.recovery_password_visible = not self.recovery_password_visible

    @rx.event
    def toggle_recovery_confirmation_visibility(self) -> None:
        self.recovery_confirmation_visible = (
            not self.recovery_confirmation_visible
        )

    @rx.event
    async def request_recovery_code(
        self, form_data: dict[str, Any]
    ) -> AsyncGenerator[rx.event.EventSpec, None]:
        if self.recovery_is_loading:
            return

        email_value = form_data.get("email")
        email = email_value.strip() if isinstance(email_value, str) else ""
        if not email:
            self.recovery_error_message = "Informe seu e-mail."
            return
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            self.recovery_error_message = "Informe um e-mail válido."
            return

        self.recovery_is_loading = True
        self.recovery_error_message = ""
        try:
            endpoint = password_reset_request_endpoint()
            async with httpx.AsyncClient(timeout=10.0) as client:
                await request_password_reset_code(client, endpoint, email)
        except LoginError:
            self.recovery_error_message = RECOVERY_UNAVAILABLE_MESSAGE
            self.recovery_is_loading = False
            return

        self.recovery_email = email
        self.recovery_resend_seconds = 30
        self.recovery_is_loading = False
        yield rx.redirect("/verificar-email")
        yield LoginState.countdown_recovery_resend

    @rx.event
    async def resend_recovery_code(
        self,
    ) -> AsyncGenerator[rx.event.EventSpec, None]:
        if self.recovery_is_loading or self.recovery_resend_seconds > 0:
            return
        if not self.recovery_email:
            yield rx.redirect("/recuperar-senha")
            return

        self.recovery_is_loading = True
        self.recovery_error_message = ""
        try:
            endpoint = password_reset_request_endpoint()
            async with httpx.AsyncClient(timeout=10.0) as client:
                await request_password_reset_code(
                    client, endpoint, self.recovery_email
                )
        except LoginError:
            self.recovery_error_message = RECOVERY_UNAVAILABLE_MESSAGE
            self.recovery_is_loading = False
            return

        self.recovery_resend_seconds = 30
        self.recovery_is_loading = False
        yield LoginState.countdown_recovery_resend

    @rx.event(background=True)
    async def countdown_recovery_resend(self) -> None:
        async with self:
            if self.recovery_countdown_running:
                return
            self.recovery_countdown_running = True

        while True:
            await asyncio.sleep(1)
            async with self:
                if self.recovery_resend_seconds <= 0:
                    self.recovery_countdown_running = False
                    return
                self.recovery_resend_seconds -= 1

    @rx.event
    async def verify_recovery_code(
        self, form_data: dict[str, Any]
    ) -> AsyncGenerator[rx.event.EventSpec, None]:
        if self.recovery_is_loading:
            return

        code_value = form_data.get("code")
        code = code_value.strip() if isinstance(code_value, str) else ""
        if not re.fullmatch(r"\d{6}", code):
            self.recovery_error_message = RECOVERY_CODE_ERROR
            return
        if not self.recovery_email:
            yield rx.redirect("/recuperar-senha")
            return

        self.recovery_is_loading = True
        self.recovery_error_message = ""
        try:
            endpoint = password_reset_verify_endpoint()
            async with httpx.AsyncClient(timeout=10.0) as client:
                result = await request_password_reset_verification(
                    client, endpoint, self.recovery_email, code
                )
        except RecoveryCodeRejectedError:
            self.recovery_error_message = RECOVERY_CODE_ERROR
        except LoginError:
            self.recovery_error_message = RECOVERY_UNAVAILABLE_MESSAGE
        else:
            self._reset_token = result.reset_token
            self.recovery_is_loading = False
            yield rx.redirect("/nova-senha")
            return
        self.recovery_is_loading = False

    @rx.event
    async def confirm_recovery_password(
        self, form_data: dict[str, Any]
    ) -> AsyncGenerator[rx.event.EventSpec, None]:
        if self.recovery_is_loading:
            return
        if not self._reset_token:
            yield rx.redirect("/recuperar-senha")
            return

        password = form_data.get("password")
        password_confirmation = form_data.get("password_confirmation")
        validation_message = validate_recovery_password(
            password, password_confirmation
        )
        if validation_message:
            self.recovery_error_message = validation_message
            return

        self.recovery_is_loading = True
        self.recovery_error_message = ""
        try:
            endpoint = password_reset_confirm_endpoint()
            async with httpx.AsyncClient(timeout=10.0) as client:
                await request_password_reset_confirmation(
                    client,
                    endpoint,
                    self._reset_token,
                    password,
                    password_confirmation,
                )
        except RecoveryTokenRejectedError:
            self.recovery_error_message = (
                "O tempo para trocar a senha acabou. Peça um novo código."
            )
            self._reset_token = ""
            self.recovery_email = ""
        except LoginError:
            self.recovery_error_message = RECOVERY_UNAVAILABLE_MESSAGE
        else:
            self._reset_token = ""
            self.recovery_email = ""
            self.recovery_resend_seconds = 0
            self.password_reset_notice_pending = True
            self.password_reset_notice_visible = False
            self.recovery_is_loading = False
            yield rx.redirect("/login")
            return
        self.recovery_is_loading = False

    @rx.event
    async def load_account(self) -> None:
        if not self.auth_token:
            self.account_name = ""
            return

        self.account_name = ACCOUNT_FALLBACK_NAME
        try:
            endpoint = auth_me_endpoint()
            async with httpx.AsyncClient(timeout=10.0) as client:
                self.account_name = await request_authenticated_name(
                    client, endpoint, self.auth_token
                )
        except AuthTokenRejectedError:
            self.auth_token = ""
            self.account_name = ""
        except LoginError:
            self.account_name = ACCOUNT_FALLBACK_NAME

    @rx.event
    def logout(self) -> None:
        self.auth_token = ""
        self.account_name = ""
        self.password_reset_notice_pending = False
        self.password_reset_notice_visible = False

    @rx.event
    def toggle_password_visibility(self) -> None:
        self.password_visible = not self.password_visible

    @rx.event
    def toggle_signup_password_visibility(self) -> None:
        self.signup_password_visible = not self.signup_password_visible

    @rx.event
    def toggle_signup_confirmation_visibility(self) -> None:
        self.signup_confirmation_visible = not self.signup_confirmation_visible

    @rx.event
    async def login(
        self, form_data: dict[str, Any]
    ) -> AsyncGenerator[rx.event.EventSpec, None]:
        if self.is_loading:
            return

        self.is_loading = True
        self.error_message = ""
        self.auth_token = ""
        self.account_name = ""
        self.password_reset_notice_pending = False
        self.password_reset_notice_visible = False

        email = form_data.get("email", "").strip()
        password = form_data.get("password", "")
        if not email or not password:
            self.error_message = "Informe seu e-mail e senha."
            self.is_loading = False
            return

        try:
            endpoint = auth_login_endpoint()
            async with httpx.AsyncClient(timeout=10.0) as client:
                result = await request_login(
                    client, endpoint, email, password
                )
        except InvalidCredentialsError as error:
            self.error_message = login_error_message(error)
        except LoginError as error:
            self.error_message = login_error_message(error)
        else:
            self.auth_token = result.auth_token
            self.is_loading = False
            yield rx.redirect("/")
            return

        self.is_loading = False

    @rx.event
    async def signup(
        self, form_data: dict[str, Any]
    ) -> AsyncGenerator[rx.event.EventSpec, None]:
        if self.is_loading:
            return

        self.is_loading = True
        self.error_message = ""
        self.auth_token = ""
        self.account_name = ""

        validation_message = validate_signup_data(form_data)
        if validation_message:
            self.error_message = validation_message
            self.is_loading = False
            return

        try:
            endpoint = auth_signup_endpoint()
            async with httpx.AsyncClient(timeout=10.0) as client:
                result = await request_signup(
                    client,
                    endpoint,
                    str(form_data["name"]),
                    str(form_data["email"]),
                    str(form_data["password"]),
                    str(form_data["city"]),
                    str(form_data["state"]),
                )
        except LoginError as error:
            self.error_message = signup_error_message(error)
        else:
            self.auth_token = result.auth_token
            self.is_loading = False
            yield rx.redirect("/")
            return

        self.is_loading = False


def login_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.box(
                rx.image(
                    src="/logo.svg",
                    alt="DoaFácil",
                    width="190px",
                    height="72px",
                    object_fit="contain",
                    margin="0 auto",
                ),
                width="100%",
                background="white",
                padding="12px 24px",
            ),
            rx.vstack(
                rx.link(
                    "← Voltar",
                    href="/",
                    on_click=LoginState.clear_password_reset_notice,
                    color="#168447",
                    align_self="start",
                    cursor="pointer",
                ),
                rx.box(
                    rx.form(
                        rx.vstack(
                            rx.heading(
                                "Bem-vindo",
                                color="#333333",
                                font_size="2rem",
                                font_weight="700",
                                text_align="center",
                                width="100%",
                            ),
                            rx.text(
                                "Entre com seu e-mail e senha",
                                color="#555555",
                                text_align="center",
                                width="100%",
                            ),
                            rx.cond(
                                LoginState.password_reset_notice_visible,
                                rx.hstack(
                                    rx.icon(
                                        "circle-check",
                                        size=20,
                                        color="#166534",
                                    ),
                                    rx.text(
                                        "Senha alterada com sucesso! Entre "
                                        "com a sua nova senha.",
                                        color="#166534",
                                        width="100%",
                                    ),
                                    role="status",
                                    align="center",
                                    width="100%",
                                    padding="12px",
                                    background="#DCFCE7",
                                    border_radius="8px",
                                ),
                                rx.fragment(),
                            ),
                            rx.vstack(
                                rx.text(
                                    "E-mail",
                                    color="#333333",
                                    font_weight="700",
                                    width="100%",
                                ),
                                rx.input(
                                    name="email",
                                    id="login-email",
                                    type="email",
                                    placeholder="Insira seu e-mail",
                                    required=True,
                                    on_change=(
                                        LoginState
                                        .dismiss_password_reset_notice_on_input
                                    ),
                                    width="100%",
                                    height="48px",
                                    background="white",
                                    color="#333333",
                                    border="1px solid #C8C8C8",
                                    border_radius="8px",
                                ),
                                align="start",
                                spacing="2",
                                width="100%",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Senha",
                                    color="#333333",
                                    font_weight="700",
                                    width="100%",
                                ),
                                rx.input(
                                    name="password",
                                    id="login-password",
                                    type=rx.cond(
                                        LoginState.password_visible,
                                        "text",
                                        "password",
                                    ),
                                    placeholder="Insira sua senha",
                                    required=True,
                                    on_change=(
                                        LoginState
                                        .dismiss_password_reset_notice_on_input
                                    ),
                                    width="100%",
                                    height="48px",
                                    background="white",
                                    color="#333333",
                                    border="1px solid #C8C8C8",
                                    border_radius="8px",
                                    padding_right="44px",
                                ),
                                rx.button(
                                    rx.cond(
                                        LoginState.password_visible,
                                        rx.icon("eye-off", size=18),
                                        rx.icon("eye", size=18),
                                    ),
                                    type="button",
                                    aria_label=rx.cond(
                                        LoginState.password_visible,
                                        "Ocultar senha",
                                        "Mostrar senha",
                                    ),
                                    on_click=LoginState.toggle_password_visibility,
                                    position="absolute",
                                    right="8px",
                                    top="36px",
                                    width="36px",
                                    height="36px",
                                    padding="0",
                                    color="#168447",
                                    background="transparent",
                                    border="none",
                                    box_shadow="none",
                                    cursor="pointer",
                                ),
                                rx.link(
                                    "Esqueci minha senha",
                                    href="/recuperar-senha",
                                    on_click=(
                                        LoginState.clear_password_reset_notice
                                    ),
                                    color="#168447",
                                    font_size="0.85rem",
                                    text_align="right",
                                    width="100%",
                                    cursor="pointer",
                                ),
                                align="start",
                                spacing="2",
                                width="100%",
                                position="relative",
                            ),
                            rx.cond(
                                LoginState.error_message != "",
                                rx.text(
                                    LoginState.error_message,
                                    color="#B42318",
                                    role="alert",
                                    width="100%",
                                ),
                                rx.fragment(),
                            ),
                            rx.button(
                                rx.cond(
                                    LoginState.is_loading,
                                    "Entrando...",
                                    "Entrar",
                                ),
                                type="submit",
                                disabled=LoginState.is_loading,
                                background="#168447",
                                color="white",
                                width="100%",
                                height="50px",
                                border_radius="8px",
                                cursor="pointer",
                            ),
                            align="start",
                            spacing="5",
                            width="100%",
                        ),
                        on_submit=LoginState.login,
                        width="100%",
                    ),
                    background="white",
                    border_radius="16px",
                    box_shadow="0 8px 24px rgba(0, 0, 0, 0.08)",
                    padding=rx.breakpoints(
                        initial="24px",
                        md="40px",
                    ),
                    width="100%",
                    class_name="auth-card-enter",
                ),
                rx.button(
                    "Criar conta",
                    type="button",
                    on_click=LoginState.navigate_to_signup_from_login,
                    variant="outline",
                    color="#168447",
                    border="1px solid #168447",
                    border_radius="999px",
                    cursor="pointer",
                ),
                align="center",
                spacing="5",
                width="100%",
                max_width="440px",
                padding="32px 24px",
            ),
            align="center",
            width="100%",
            spacing="0",
        ),
        min_height="100vh",
        width="100%",
        background="#FFF6E8",
        font_family="'LINE Seed JP', Arial, sans-serif",
    )
