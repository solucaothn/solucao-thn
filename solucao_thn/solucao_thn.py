import reflex as rx

from rxconfig import config

from .xano_api import XanoApiError, XanoClient


class AuthState(rx.State):
    """UI state for a session authenticated by Xano."""

    auth_token: str = rx.Cookie(
        "",
        name="xano_auth_token",
        path="/",
        max_age=86400,
        secure=True,
        same_site="lax",
    )
    session_user_id: str = ""
    api_error: str = ""
    api_success: str = ""
    profile: dict[str, str] = {}

    register_name: str = ""
    register_email: str = ""
    register_password: str = ""
    register_city: str = ""
    register_state: str = ""
    login_email: str = ""
    login_password: str = ""
    profile_name: str = ""
    profile_city: str = ""
    profile_state: str = ""

    def set_register_name(self, value: str) -> None:
        self.register_name = value

    def set_register_email(self, value: str) -> None:
        self.register_email = value

    def set_register_password(self, value: str) -> None:
        self.register_password = value

    def set_register_city(self, value: str) -> None:
        self.register_city = value

    def set_register_state(self, value: str) -> None:
        self.register_state = value

    def set_login_email(self, value: str) -> None:
        self.login_email = value

    def set_login_password(self, value: str) -> None:
        self.login_password = value

    def set_profile_name(self, value: str) -> None:
        self.profile_name = value

    def set_profile_city(self, value: str) -> None:
        self.profile_city = value

    def set_profile_state(self, value: str) -> None:
        self.profile_state = value

    def _sync_profile_form(self) -> None:
        self.profile_name = self.profile.get("name", "")
        self.profile_city = self.profile.get("city", "")
        self.profile_state = self.profile.get("state", "")

    def register_user(self) -> None:
        self.api_error = ""
        self.api_success = ""
        try:
            result = XanoClient().signup(
                name=self.register_name,
                email=self.register_email,
                password=self.register_password,
                city=self.register_city,
                state=self.register_state,
            )
            self.auth_token = result["authToken"]
            self.load_profile()
            if not self.api_error:
                self.api_success = "Cadastro realizado com sucesso."
            self.register_name = ""
            self.register_email = ""
            self.register_password = ""
            self.register_city = ""
            self.register_state = ""
        except (XanoApiError, KeyError) as exc:
            self.api_error = str(exc)

    def login_user(self) -> None:
        self.api_error = ""
        self.api_success = ""
        try:
            result = XanoClient().login(
                email=self.login_email,
                password=self.login_password,
            )
            self.auth_token = result["authToken"]
            self.load_profile()
            if not self.api_error:
                self.api_success = "Login realizado com sucesso."
            self.login_email = ""
            self.login_password = ""
        except (XanoApiError, KeyError) as exc:
            self.api_error = str(exc)

    def logout(self) -> None:
        self.api_error = ""
        self.api_success = ""
        self.auth_token = ""
        self.session_user_id = ""
        self.profile = {}
        self.profile_name = ""
        self.profile_city = ""
        self.profile_state = ""

    def load_profile(self) -> None:
        if not self.auth_token:
            return
        try:
            self.profile = XanoClient().profile(self.auth_token)
            self.session_user_id = str(self.profile.get("id", ""))
            self._sync_profile_form()
        except XanoApiError as exc:
            self.auth_token = ""
            self.session_user_id = ""
            self.profile = {}
            self.api_error = str(exc)

    def update_profile(self) -> None:
        self.api_error = ""
        self.api_success = ""
        if not self.auth_token:
            self.api_error = "Faça login para atualizar o perfil."
            return
        try:
            self.profile = XanoClient().update_profile(
                token=self.auth_token,
                name=self.profile_name,
                city=self.profile_city,
                state=self.profile_state,
            )
            self.session_user_id = str(self.profile.get("id", ""))
            self._sync_profile_form()
            self.api_success = "Perfil atualizado com sucesso."
        except XanoApiError as exc:
            self.api_error = str(exc)


def render_status_box() -> rx.Component:
    return rx.box(
        rx.cond(
            AuthState.api_error != "",
            rx.callout(AuthState.api_error, icon="warning", color_scheme="red", role="alert"),
            rx.cond(
                AuthState.api_success != "",
                rx.callout(AuthState.api_success, icon="check", color_scheme="green"),
                rx.text(""),
            ),
        ),
        width="100%",
    )


def render_register_form() -> rx.Component:
    return rx.box(
        rx.heading("Cadastro", size="5"),
        rx.form(
            rx.vstack(
                rx.input(placeholder="Nome completo", value=AuthState.register_name, on_change=AuthState.set_register_name),
                rx.input(placeholder="E-mail", value=AuthState.register_email, on_change=AuthState.set_register_email),
                rx.input(placeholder="Senha", type_="password", value=AuthState.register_password, on_change=AuthState.set_register_password),
                rx.input(placeholder="Cidade", value=AuthState.register_city, on_change=AuthState.set_register_city),
                rx.input(placeholder="Estado", value=AuthState.register_state, on_change=AuthState.set_register_state),
                rx.button("Criar conta", type_="submit"),
                spacing="3",
            ),
            on_submit=AuthState.register_user,
        ),
        padding="4",
        border="1px solid #e5e7eb",
        border_radius="md",
    )


def render_login_form() -> rx.Component:
    return rx.box(
        rx.heading("Login", size="5"),
        rx.form(
            rx.vstack(
                rx.input(placeholder="E-mail", value=AuthState.login_email, on_change=AuthState.set_login_email),
                rx.input(placeholder="Senha", type_="password", value=AuthState.login_password, on_change=AuthState.set_login_password),
                rx.button("Entrar", type_="submit"),
                spacing="3",
            ),
            on_submit=AuthState.login_user,
        ),
        padding="4",
        border="1px solid #e5e7eb",
        border_radius="md",
    )


def render_profile_form() -> rx.Component:
    return rx.box(
        rx.heading("Meu perfil", size="5"),
        rx.form(
            rx.vstack(
                rx.input(placeholder="Nome completo", value=AuthState.profile_name, on_change=AuthState.set_profile_name),
                rx.input(placeholder="Cidade", value=AuthState.profile_city, on_change=AuthState.set_profile_city),
                rx.input(placeholder="Estado", value=AuthState.profile_state, on_change=AuthState.set_profile_state),
                rx.hstack(
                    rx.button("Salvar alterações", type_="submit"),
                    rx.button("Sair", on_click=AuthState.logout, variant="soft"),
                ),
                spacing="3",
            ),
            on_submit=AuthState.update_profile,
        ),
        padding="4",
        border="1px solid #e5e7eb",
        border_radius="md",
    )


def index() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("DoaFácil", size="9"),
            rx.text("Fundação de identidade e autorização", size="5"),
            render_status_box(),
            rx.cond(
                AuthState.session_user_id == "",
                rx.hstack(render_register_form(), render_login_form(), spacing="5", align="start", wrap="wrap"),
                rx.vstack(
                    render_profile_form(),
                    rx.text("Acesso restrito ao próprio perfil. O backend valida a propriedade do recurso."),
                    spacing="4",
                ),
            ),
            spacing="5",
            justify="center",
            min_height="85vh",
            width="100%",
        ),
        padding_y="8",
    )


app = rx.App()
app.add_page(index, on_load=AuthState.load_profile)
