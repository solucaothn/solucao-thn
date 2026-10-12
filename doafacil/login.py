import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx
import reflex as rx


AUTH_API_ENV = "XANO_AUTH_API_URL"
AUTH_LOGIN_PATH = "/auth/login"


class LoginError(Exception):
    pass


class LoginConfigurationError(LoginError):
    pass


class InvalidCredentialsError(LoginError):
    pass


class LoginUnavailableError(LoginError):
    pass


@dataclass(frozen=True, repr=False)
class LoginResult:
    auth_token: str
    user_id: int


def login_error_message(error: LoginError) -> str:
    if isinstance(error, InvalidCredentialsError):
        return "E-mail ou senha incorretos."
    return (
        "Não foi possível conectar ao serviço de autenticação. "
        "Tente novamente."
    )


def auth_login_endpoint() -> str:
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

    return f"{base_url.rstrip('/')}{AUTH_LOGIN_PATH}"


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


class LoginState(rx.State):
    is_loading: bool = False
    error_message: str = ""
    auth_token: str = ""
    password_visible: bool = False

    @rx.event
    def toggle_password_visibility(self) -> None:
        self.password_visible = not self.password_visible

    @rx.event
    async def login(
        self, form_data: dict[str, Any]
    ) -> AsyncGenerator[rx.event.EventSpec, None]:
        if self.is_loading:
            return

        self.is_loading = True
        self.error_message = ""
        self.auth_token = ""

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
                                rx.text(
                                    "Esqueci minha senha",
                                    color="#168447",
                                    font_size="0.85rem",
                                    text_align="right",
                                    width="100%",
                                    cursor="default",
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
                ),
                rx.button(
                    "Criar conta",
                    type="button",
                    variant="outline",
                    color="#168447",
                    border="1px solid #168447",
                    border_radius="999px",
                    cursor="default",
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
