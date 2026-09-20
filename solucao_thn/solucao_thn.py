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
    profile: dict[str, object] = {}

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
    donations: list[dict[str, object]] = []
    categories: list[dict[str, object]] = []
    donation_id: int = 0
    donation_title: str = ""
    donation_description: str = ""
    donation_category_id: str = ""
    donation_status: str = "disponível"
    pending_delete_id: int = 0

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

    def set_donation_title(self, value: str) -> None:
        self.donation_title = value

    def set_donation_description(self, value: str) -> None:
        self.donation_description = value

    def set_donation_category_id(self, value: str) -> None:
        self.donation_category_id = value

    def set_donation_status(self, value: str) -> None:
        self.donation_status = value

    @rx.var
    def category_names(self) -> list[str]:
        return [str(category.get("name", "")) for category in self.categories]

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
        self.pending_delete_id = 0

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

    def hydrate(self) -> None:
        self.load_profile()
        self.load_catalog()

    def load_catalog(self) -> None:
        self.api_error = ""
        try:
            self.categories = XanoClient().categories()
            self.donations = XanoClient().donations()
        except XanoApiError as exc:
            self.api_error = str(exc)

    def clear_donation_form(self) -> None:
        self.donation_id = 0
        self.donation_title = ""
        self.donation_description = ""
        self.donation_category_id = ""
        self.donation_status = "disponível"

    def cancel_delete_confirmation(self) -> None:
        self.pending_delete_id = 0

    def edit_donation(self, donation: dict[str, object]) -> None:
        self.donation_id = int(donation.get("id", 0))
        self.donation_title = str(donation.get("title", ""))
        self.donation_description = str(donation.get("description", ""))
        category_id = str(donation.get("category_id", ""))
        self.donation_category_id = next(
            (
                str(category.get("name", ""))
                for category in self.categories
                if str(category.get("id", "")) == category_id
            ),
            "",
        )
        self.donation_status = str(donation.get("status", "disponível"))

    def save_donation(self) -> None:
        self.api_error = ""
        self.api_success = ""
        if not self.auth_token:
            self.api_error = "Faça login para cadastrar uma doação."
            return
        try:
            category_id = next(
                int(category["id"])
                for category in self.categories
                if str(category.get("name", "")) == self.donation_category_id
            )
            if self.donation_id:
                XanoClient().update_donation(
                    token=self.auth_token,
                    donation_id=self.donation_id,
                    category_id=category_id,
                    title=self.donation_title,
                    description=self.donation_description,
                )
                self.api_success = "Doação atualizada com sucesso."
            else:
                XanoClient().create_donation(
                    token=self.auth_token,
                    category_id=category_id,
                    title=self.donation_title,
                    description=self.donation_description,
                )
                self.api_success = "Doação cadastrada com sucesso."
            self.clear_donation_form()
            self.load_catalog()
        except (XanoApiError, ValueError) as exc:
            self.api_error = str(exc)

    def delete_donation(self, donation_id: int) -> None:
        self.api_error = ""
        self.api_success = ""
        if not self.auth_token:
            self.api_error = "Faça login para excluir uma doação."
            return
        if self.pending_delete_id != donation_id:
            self.pending_delete_id = donation_id
            self.api_success = "Clique novamente para confirmar a exclusão."
            return
        try:
            XanoClient().delete_donation(
                token=self.auth_token, donation_id=donation_id
            )
            self.pending_delete_id = 0
            self.api_success = "Doação excluída com sucesso."
            self.load_catalog()
        except XanoApiError as exc:
            self.api_error = str(exc)

    def change_donation_status(self, donation_id: int, status: str) -> None:
        self.api_error = ""
        self.api_success = ""
        if not self.auth_token:
            self.api_error = "Faça login para alterar o status."
            return
        try:
            XanoClient().update_donation_status(
                token=self.auth_token, donation_id=donation_id, status=status
            )
            self.api_success = "Status atualizado com sucesso."
            self.load_catalog()
        except XanoApiError as exc:
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


def render_donation_card(donation: dict[str, object]) -> rx.Component:
    return rx.box(
        rx.heading(donation["title"], size="4"),
        rx.text(donation["description"]),
        rx.text("Categoria: ", donation["category_id"]),
        rx.text("Status: ", donation["status"]),
        rx.hstack(
            rx.button(
                "Editar",
                on_click=AuthState.edit_donation(donation),
                variant="soft",
            ),
            rx.button(
                "Excluir / confirmar",
                on_click=AuthState.delete_donation(donation["id"]),
                color_scheme="red",
                variant="soft",
            ),
            rx.button(
                "Marcar reservada",
                on_click=AuthState.change_donation_status(
                    donation["id"], "reservada"
                ),
                variant="soft",
            ),
            rx.button(
                "Marcar concluída",
                on_click=AuthState.change_donation_status(
                    donation["id"], "concluída"
                ),
                variant="soft",
            ),
            spacing="2",
        ),
        padding="4",
        border="1px solid #e5e7eb",
        border_radius="md",
        width="100%",
    )


def render_donation_form() -> rx.Component:
    return rx.box(
        rx.heading(
            rx.cond(AuthState.donation_id == 0, "Nova doação", "Editar doação"),
            size="5",
        ),
        rx.form(
            rx.vstack(
                rx.input(
                    placeholder="Título do item",
                    value=AuthState.donation_title,
                    on_change=AuthState.set_donation_title,
                    required=True,
                ),
                rx.text_area(
                    placeholder="Descrição",
                    value=AuthState.donation_description,
                    on_change=AuthState.set_donation_description,
                ),
                rx.select(
                    AuthState.category_names,
                    value=AuthState.donation_category_id,
                    on_change=AuthState.set_donation_category_id,
                    placeholder="Selecione uma categoria",
                    required=True,
                ),
                rx.hstack(
                    rx.button("Salvar", type_="submit"),
                    rx.button(
                        "Cancelar",
                        type_="button",
                        on_click=AuthState.clear_donation_form,
                        variant="soft",
                    ),
                ),
                spacing="3",
            ),
            on_submit=AuthState.save_donation,
        ),
        padding="4",
        border="1px solid #e5e7eb",
        border_radius="md",
        width="100%",
    )


def render_catalog() -> rx.Component:
    return rx.vstack(
        rx.heading("Catálogo de doações", size="6"),
        rx.cond(
            AuthState.session_user_id != "",
            render_donation_form(),
            rx.text("Faça login para cadastrar e manter suas doações."),
        ),
        rx.cond(
            AuthState.donations.length() > 0,
            rx.foreach(AuthState.donations, render_donation_card),
            rx.text("Nenhuma doação disponível."),
        ),
        spacing="4",
        width="100%",
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
                    spacing="4",
                ),
            ),
            render_catalog(),
            spacing="5",
            justify="center",
            min_height="85vh",
            width="100%",
        ),
        padding_y="8",
    )


app = rx.App()
app.add_page(index, on_load=AuthState.hydrate)
