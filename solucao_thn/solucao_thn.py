import reflex as rx

from rxconfig import config

from .xano_api import XanoApiError, XanoClient


PRIMARY = {
    "dark": "#0F4D3A",
    "green": "#18A566",
    "light": "#E8F7EF",
    "yellow": "#F4B740",
    "cream": "#FFF9ED",
    "background": "#F8FAF8",
    "text": "#12352A",
    "muted": "#58786F",
}

CATEGORY_ITEMS = [
    {"name": "Roupas", "icon": "👕", "color": "#E8F7EF", "tag": "35 doações"},
    {"name": "Alimentos", "icon": "🥖", "color": "#FFF1D2", "tag": "24 doações"},
    {"name": "Móveis", "icon": "🪑", "color": "#EAF4FF", "tag": "18 doações"},
    {"name": "Livros", "icon": "📚", "color": "#FDE9D9", "tag": "22 doações"},
    {"name": "Eletrônicos", "icon": "💻", "color": "#E8F7EF", "tag": "16 doações"},
    {"name": "Outros", "icon": "🎁", "color": "#F4E9FF", "tag": "12 doações"},
]

DONATION_ITEMS = [
    {
        "title": "Kit de roupas",
        "category": "Roupas",
        "location": "São Paulo, SP",
        "description": "Conjunto de peças em bom estado para crianças e adolescentes.",
        "accent": "linear-gradient(135deg, #E8F7EF 0%, #86D5A8 100%)",
        "icon": "👕",
    },
    {
        "title": "Cesta de alimentos",
        "category": "Alimentos",
        "location": "São Paulo, SP",
        "description": "Itens essenciais para compor uma cesta de apoio familiar.",
        "accent": "linear-gradient(135deg, #FFF1D2 0%, #F4B740 100%)",
        "icon": "🥖",
    },
    {
        "title": "Livros para estudantes",
        "category": "Livros",
        "location": "São Paulo, SP",
        "description": "Material escolar e de leitura para apoiar estudos e aprendizagem.",
        "accent": "linear-gradient(135deg, #FDE9D9 0%, #FFB98E 100%)",
        "icon": "📚",
    },
    {
        "title": "Mesa de escritório",
        "category": "Móveis",
        "location": "São Paulo, SP",
        "description": "Peça funcional para transformar um espaço de estudo ou trabalho.",
        "accent": "linear-gradient(135deg, #EAF4FF 0%, #9BC3FF 100%)",
        "icon": "🪑",
    },
    {
        "title": "Brinquedos infantis",
        "category": "Outros",
        "location": "São Paulo, SP",
        "description": "Brinquedos em bom estado para alegrar pequenas histórias.",
        "accent": "linear-gradient(135deg, #F4E9FF 0%, #D7B7FF 100%)",
        "icon": "🎁",
    },
    {
        "title": "Computador para estudos",
        "category": "Eletrônicos",
        "location": "São Paulo, SP",
        "description": "Equipamento útil para continuar estudos, trabalho e acesso ao futuro.",
        "accent": "linear-gradient(135deg, #DEFAF4 0%, #68D1B0 100%)",
        "icon": "💻",
    },
]


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


class LandingPageState(rx.State):
    carousel_index: int = 0

    def next_donation(self) -> None:
        self.carousel_index = (self.carousel_index + 1) % len(DONATION_ITEMS)

    def prev_donation(self) -> None:
        self.carousel_index = (self.carousel_index - 1) % len(DONATION_ITEMS)

    @rx.var
    def featured_donations(self) -> list[dict[str, str]]:
        return [
            DONATION_ITEMS[(self.carousel_index + offset) % len(DONATION_ITEMS)]
            for offset in range(4)
        ]


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


def render_nav_link(label: str, href: str) -> rx.Component:
    return rx.link(
        rx.text(label, color=PRIMARY["text"], font_size="0.95rem", font_weight="500"),
        href=href,
        style={"text_decoration": "none"},
    )


def render_home_navbar() -> rx.Component:
    return rx.box(
        rx.container(
            rx.hstack(
                rx.link(
                    rx.text("DoaFácil", font_size="1.75rem", font_weight="700", color=PRIMARY["dark"]),
                    href="#top",
                    style={"text_decoration": "none"},
                ),
                rx.hstack(
                    render_nav_link("Explorar doações", "#explorar"),
                    render_nav_link("Como funciona", "#como-funciona"),
                    render_nav_link("Categorias", "#categorias"),
                    spacing="7",
                    display=["none", "none", "flex"],
                ),
                rx.hstack(
                    rx.link(
                        rx.button("Entrar", variant="ghost", color=PRIMARY["dark"], bg="transparent", border="1px solid rgba(18,53,42,0.12)", border_radius="999px", px="4", py="2"),
                        href="#entrar",
                    ),
                    rx.button(
                        "Quero doar",
                        bg=PRIMARY["green"],
                        color="white",
                        border_radius="999px",
                        px="5",
                        py="2.5",
                        box_shadow="0 10px 24px rgba(24,165,102,0.28)",
                    ),
                    spacing="3",
                ),
                justify="between",
                align="center",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="4",
        ),
        width="100%",
        background="rgba(255,255,255,0.85)",
        backdrop_filter="blur(10px)",
        border_bottom="1px solid rgba(18,53,42,0.06)",
        position="sticky",
        top="0",
        z_index="10",
    )


def render_home_hero() -> rx.Component:
    return rx.box(
        rx.container(
            rx.hstack(
                rx.vstack(
                    rx.box(
                        rx.text("DOAR PODE TRANSFORMAR UM DIA", color=PRIMARY["green"], font_size="0.76rem", font_weight="700", letter_spacing="0.13em"),
                        bg="rgba(24,165,102,0.08)",
                        border="1px solid rgba(24,165,102,0.14)",
                        border_radius="999px",
                        px="3",
                        py="2",
                    ),
                    rx.heading(
                        "Uma doação simples pode fazer toda a diferença.",
                        size="7",
                        color=PRIMARY["dark"],
                        line_height="1.06",
                        width="100%",
                    ),
                    rx.text(
                        "Conecte itens que não são usados mais com pessoas ou comunidades que podem dar um novo destino a eles.",
                        color=PRIMARY["muted"],
                        font_size="1.08rem",
                        line_height="1.7",
                        max_width="560px",
                    ),
                    rx.hstack(
                        rx.button(
                            "Quero doar",
                            bg=PRIMARY["green"],
                            color="white",
                            border_radius="999px",
                            px="6",
                            py="3",
                            box_shadow="0 16px 30px rgba(24,165,102,0.24)",
                        ),
                        rx.button(
                            "Encontrar uma doação",
                            bg="white",
                            color=PRIMARY["dark"],
                            border="1px solid rgba(18,53,42,0.1)",
                            border_radius="999px",
                            px="6",
                            py="3",
                        ),
                        spacing="4",
                        wrap="wrap",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text("1.240+", font_weight="800", font_size="1.3rem", color=PRIMARY["dark"]),
                            rx.text("doações em circulação", color=PRIMARY["muted"], font_size="0.82rem"),
                            spacing="0",
                        ),
                        rx.vstack(
                            rx.text("680+", font_weight="800", font_size="1.3rem", color=PRIMARY["dark"]),
                            rx.text("pessoas alcançadas", color=PRIMARY["muted"], font_size="0.82rem"),
                            spacing="0",
                        ),
                        spacing="8",
                        align="start",
                        wrap="wrap",
                    ),
                    spacing="5",
                    align="start",
                    width=["100%", "100%", "55%"],
                    min_width="0",
                ),
                rx.box(
                    rx.box(
                        rx.box(
                            rx.box(
                                rx.text("💚", font_size="1.6rem"),
                                bg="rgba(255,255,255,0.65)",
                                border_radius="50%",
                                width="52px",
                                height="52px",
                                display="flex",
                                align_items="center",
                                justify_content="center",
                                box_shadow="0 14px 30px rgba(17,61,49,0.12)",
                            ),
                            rx.box(
                                rx.text("Nova oportunidade", color=PRIMARY["dark"], font_size="0.8rem", font_weight="700"),
                                rx.text("3 pessoas próximas", color=PRIMARY["muted"], font_size="0.72rem"),
                                spacing="0",
                            ),
                            justify="between",
                            align="center",
                            width="100%",
                            padding="4",
                        ),
                        rx.box(
                            rx.text("Roupas", color=PRIMARY["dark"], font_size="0.75rem", font_weight="700", bg="rgba(255,255,255,0.8)", px="3", py="2", border_radius="999px"),
                            rx.text("🔔 8 pedidos recentes", color=PRIMARY["dark"], font_size="0.75rem", font_weight="600"),
                            justify="between",
                            align="center",
                            width="100%",
                            margin_top="4",
                        ),
                        rx.box(
                            rx.text("Cesta de alimentos", color=PRIMARY["dark"], font_size="1.6rem", font_weight="700"),
                            rx.text("Ajuda imediata para famílias do entorno.", color=PRIMARY["muted"], font_size="0.9rem"),
                            spacing="1",
                            margin_top="4",
                        ),
                        rx.box(
                            rx.hstack(
                                rx.box(
                                    rx.text("32%", font_weight="700", color=PRIMARY["dark"]),
                                    rx.text("de pessoas já responderam", color=PRIMARY["muted"], font_size="0.68rem"),
                                    spacing="0",
                                ),
                                rx.button("Ver doação", bg=PRIMARY["green"], color="white", border_radius="999px", px="4", py="2"),
                                justify="between",
                                align="center",
                                width="100%",
                            ),
                            margin_top="5",
                        ),
                        bg="rgba(255,255,255,0.8)",
                        border="1px solid rgba(17,61,49,0.08)",
                        border_radius="28px",
                        box_shadow="0 26px 60px rgba(17,61,49,0.13)",
                        padding="5",
                        width="100%",
                        position="relative",
                        z_index="2",
                    ),
                    rx.box(
                        rx.box(
                            rx.text("📚", font_size="1.4rem"),
                            rx.text("Livros", font_size="0.82rem", color=PRIMARY["dark"], font_weight="700"),
                            spacing="2",
                            align="center",
                            bg="white",
                            border_radius="18px",
                            box_shadow="0 16px 26px rgba(17,61,49,0.12)",
                            padding="3",
                        ),
                        position="absolute",
                        right="-16px",
                        top="50px",
                        z_index="3",
                    ),
                    rx.box(
                        rx.box(
                            rx.text("🧥", font_size="1.2rem"),
                            rx.text("Roupas", font_size="0.72rem", color=PRIMARY["dark"], font_weight="700"),
                            spacing="2",
                            align="center",
                            bg="white",
                            border_radius="15px",
                            box_shadow="0 16px 26px rgba(17,61,49,0.12)",
                            padding="3",
                        ),
                        position="absolute",
                        left="-18px",
                        bottom="62px",
                        z_index="3",
                    ),
                    rx.box(
                        rx.text("+680 pessoas alcançadas", color=PRIMARY["dark"], font_weight="700", bg="rgba(255,255,255,0.78)", border_radius="999px", px="4", py="2"),
                        position="absolute",
                        bottom="-18px",
                        right="52px",
                        z_index="4",
                    ),
                    bg="linear-gradient(135deg, #F7EED4 0%, #EAF7F0 100%)",
                    border_radius="32px",
                    width=["100%", "100%", "45%"],
                    min_height="540px",
                    position="relative",
                    border="1px solid rgba(18,53,42,0.04)",
                    padding="6",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                justify="between",
                align="center",
                width="100%",
                spacing="6",
                wrap="wrap",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y=["10", "12", "16"],
        ),
        width="100%",
        background=PRIMARY["cream"],
    )


def render_search_section() -> rx.Component:
    return rx.box(
        rx.container(
            rx.box(
                rx.vstack(
                    rx.text("Encontre algo que pode fazer a diferença", color=PRIMARY["dark"], font_size="1.4rem", font_weight="700"),
                    rx.hstack(
                        rx.input(
                            placeholder="O que você está procurando?",
                            bg="#F7F9F8",
                            border="1px solid rgba(18,53,42,0.08)",
                            border_radius="18px",
                            px="4",
                            py="4",
                            width="100%",
                        ),
                        rx.button(
                            "Buscar",
                            bg=PRIMARY["green"],
                            color="white",
                            border_radius="18px",
                            px="7",
                            py="4",
                            min_width="130px",
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                        wrap="wrap",
                    ),
                    rx.hstack(
                        rx.foreach(
                            ["Roupas", "Alimentos", "Livros", "Móveis", "Eletrônicos", "Outros"],
                            lambda tag: rx.button(
                                tag,
                                variant="soft",
                                color=PRIMARY["dark"],
                                bg="rgba(24,165,102,0.08)",
                                border_radius="999px",
                                px="4",
                                py="2",
                            ),
                        ),
                        spacing="3",
                        wrap="wrap",
                    ),
                    spacing="4",
                    width="100%",
                ),
                bg="white",
                border="1px solid rgba(18,53,42,0.06)",
                border_radius="28px",
                box_shadow="0 24px 44px rgba(17,61,49,0.06)",
                padding=["5", "5", "6"],
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="0",
        ),
        width="100%",
        background="white",
        margin_top="-26px",
        padding_bottom="8",
    )


def render_impact_stats() -> rx.Component:
    return rx.box(
        rx.container(
            rx.hstack(
                rx.vstack(
                    rx.text("1.240+", color=PRIMARY["dark"], font_size="2.1rem", font_weight="800"),
                    rx.text("Doações compartilhadas", color=PRIMARY["muted"], font_size="0.95rem"),
                    spacing="1",
                    align="center",
                ),
                rx.vstack(
                    rx.text("680+", color=PRIMARY["dark"], font_size="2.1rem", font_weight="800"),
                    rx.text("Pessoas alcançadas", color=PRIMARY["muted"], font_size="0.95rem"),
                    spacing="1",
                    align="center",
                ),
                rx.vstack(
                    rx.text("32", color=PRIMARY["dark"], font_size="2.1rem", font_weight="800"),
                    rx.text("Categorias", color=PRIMARY["muted"], font_size="0.95rem"),
                    spacing="1",
                    align="center",
                ),
                rx.vstack(
                    rx.text("100%", color=PRIMARY["dark"], font_size="2.1rem", font_weight="800"),
                    rx.text("Feito para conectar pessoas", color=PRIMARY["muted"], font_size="0.95rem"),
                    spacing="1",
                    align="center",
                ),
                justify="between",
                align="stretch",
                width="100%",
                spacing="0",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="7",
        ),
        width="100%",
        background=PRIMARY["light"],
        border_top="1px solid rgba(18,53,42,0.03)",
        border_bottom="1px solid rgba(18,53,42,0.03)",
    )


def render_category_section() -> rx.Component:
    cards = []
    for item in CATEGORY_ITEMS:
        cards.append(
            rx.box(
                rx.box(
                    rx.text(item["icon"], font_size="2.4rem"),
                    bg=item["color"],
                    border_radius="22px",
                    width="64px",
                    height="64px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.heading(item["name"], size="5", color=PRIMARY["dark"]),
                rx.text(
                    "Descubra itens que podem ajudar alguém com facilidade e propósito.",
                    color=PRIMARY["muted"],
                    font_size="0.94rem",
                    line_height="1.7",
                ),
                rx.hstack(
                    rx.text(item["tag"], color=PRIMARY["green"], font_size="0.78rem", font_weight="700"),
                    rx.text("→", color=PRIMARY["dark"], font_weight="700"),
                    justify="between",
                    width="100%",
                    margin_top="4",
                ),
                bg="white",
                border="1px solid rgba(18,53,42,0.06)",
                border_radius="24px",
                padding="5",
                width="100%",
                box_shadow="0 14px 30px rgba(17,61,49,0.04)",
                transition="transform 0.2s ease, box-shadow 0.2s ease",
                _hover={"transform": "translateY(-4px)", "box_shadow": "0 18px 34px rgba(17,61,49,0.08)"},
            )
        )
    return rx.box(
        rx.container(
            rx.vstack(
                rx.heading("Encontre uma forma de ajudar", size="7", color=PRIMARY["dark"]),
                rx.text(
                    "Explore as categorias e descubra onde sua doação pode fazer a diferença.",
                    color=PRIMARY["muted"],
                    font_size="1.05rem",
                    text_align="center",
                ),
                rx.grid(
                    *cards,
                    columns="3",
                    spacing="4",
                    width="100%",
                ),
                spacing="6",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background="white",
    )


class DonationCarouselState(rx.State):
    index: int = 0

    def next(self) -> None:
        self.index = (self.index + 1) % len(DONATION_ITEMS)

    def prev(self) -> None:
        self.index = (self.index - 1) % len(DONATION_ITEMS)

    @rx.var
    def visible_cards(self) -> list[dict[str, str]]:
        return [
            DONATION_ITEMS[(self.index + offset) % len(DONATION_ITEMS)]
            for offset in range(4)
        ]


def render_featured_donations_carousel() -> rx.Component:
    return rx.box(
        rx.container(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Doações em destaque", size="7", color=PRIMARY["dark"]),
                        rx.text(
                            "Talvez aquilo que você procura esteja esperando por você.",
                            color=PRIMARY["muted"],
                            font_size="1.04rem",
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.hstack(
                        rx.button(
                            "←",
                            on_click=DonationCarouselState.prev,
                            bg="white",
                            color=PRIMARY["dark"],
                            border="1px solid rgba(18,53,42,0.08)",
                            border_radius="999px",
                            width="48px",
                            height="48px",
                        ),
                        rx.button(
                            "→",
                            on_click=DonationCarouselState.next,
                            bg=PRIMARY["green"],
                            color="white",
                            border_radius="999px",
                            width="48px",
                            height="48px",
                        ),
                        spacing="3",
                    ),
                    justify="between",
                    width="100%",
                    align="end",
                ),
                rx.grid(
                    rx.foreach(
                        DonationCarouselState.visible_cards,
                        lambda item: rx.box(
                            rx.box(
                                rx.box(
                                    rx.text(item["icon"], font_size="2rem"),
                                    bg="rgba(255,255,255,0.72)",
                                    border_radius="18px",
                                    px="3",
                                    py="2",
                                ),
                                rx.text(item["category"], color=PRIMARY["dark"], font_weight="700", font_size="0.7rem", bg="rgba(255,255,255,0.78)", px="3", py="2", border_radius="999px"),
                                justify="between",
                                align="center",
                                width="100%",
                                padding="4",
                            ),
                            rx.vstack(
                                rx.text(item["title"], color=PRIMARY["dark"], font_size="1.4rem", font_weight="700"),
                                rx.text(item["location"], color=PRIMARY["muted"], font_size="0.82rem"),
                                rx.text(item["description"], color=PRIMARY["muted"], font_size="0.92rem", line_height="1.7"),
                                rx.button(
                                    "Ver doação",
                                    bg=PRIMARY["green"],
                                    color="white",
                                    border_radius="999px",
                                    px="4",
                                    py="2",
                                ),
                                spacing="3",
                                width="100%",
                                padding="4",
                            ),
                            bg="white",
                            border_radius="26px",
                            border="1px solid rgba(18,53,42,0.06)",
                            box_shadow="0 20px 36px rgba(17,61,49,0.06)",
                            overflow="hidden",
                            width="100%",
                        ),
                    ),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                rx.hstack(
                    rx.foreach(
                        range(len(DONATION_ITEMS)),
                        lambda idx: rx.box(
                            width="10px",
                            height="10px",
                            border_radius="999px",
                            bg=rx.cond(DonationCarouselState.index == idx, PRIMARY["green"], "rgba(18,53,42,0.18)"),
                            transition="all 0.2s ease",
                        ),
                    ),
                    spacing="2",
                    justify="center",
                    width="100%",
                ),
                spacing="6",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background=PRIMARY["light"],
    )


def render_how_it_works() -> rx.Component:
    return rx.box(
        rx.container(
            rx.vstack(
                rx.heading("Doar é mais simples do que parece", size="7", color=PRIMARY["dark"]),
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.text("01", color=PRIMARY["green"], font_weight="800", font_size="0.96rem"),
                            rx.text("ENCONTRE", color=PRIMARY["dark"], font_weight="700", font_size="1.1rem"),
                            rx.text("Encontre algo que você pode doar.", color=PRIMARY["muted"], font_size="0.95rem", line_height="1.7"),
                            spacing="3",
                            align="start",
                            width="100%",
                        ),
                        rx.box(
                            rx.text("02", color=PRIMARY["green"], font_weight="800", font_size="0.96rem"),
                            rx.text("CONECTE", color=PRIMARY["dark"], font_weight="700", font_size="1.1rem"),
                            rx.text("Converse com quem precisa.", color=PRIMARY["muted"], font_size="0.95rem", line_height="1.7"),
                            spacing="3",
                            align="start",
                            width="100%",
                        ),
                        rx.box(
                            rx.text("03", color=PRIMARY["green"], font_weight="800", font_size="0.96rem"),
                            rx.text("TRANSFORME", color=PRIMARY["dark"], font_weight="700", font_size="1.1rem"),
                            rx.text("Sua doação ganha um novo destino.", color=PRIMARY["muted"], font_size="0.95rem", line_height="1.7"),
                            spacing="3",
                            align="start",
                            width="100%",
                        ),
                        justify="between",
                        align="stretch",
                        width="100%",
                        spacing="5",
                    ),
                    width="100%",
                    position="relative",
                    padding_top="3",
                ),
                spacing="6",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background="white",
    )


def render_security_section() -> rx.Component:
    return rx.box(
        rx.container(
            rx.vstack(
                rx.heading("Doar deve ser simples. E seguro.", size="7", color="white"),
                rx.text(
                    "O DoaFácil foi pensado para aproximar pessoas de forma clara, responsável e transparente.",
                    color="rgba(255,255,255,0.82)",
                    font_size="1.05rem",
                    text_align="center",
                    max_width="760px",
                ),
                rx.grid(
                    rx.box(
                        rx.text("🔒", font_size="2rem"),
                        rx.heading("Dados protegidos", size="5", color="white"),
                        rx.text("Suas informações merecem cuidado.", color="rgba(255,255,255,0.8)", font_size="0.95rem"),
                        bg="rgba(255,255,255,0.12)",
                        border="1px solid rgba(255,255,255,0.12)",
                        border_radius="22px",
                        padding="5",
                    ),
                    rx.box(
                        rx.text("✓", font_size="2rem"),
                        rx.heading("Informações claras", size="5", color="white"),
                        rx.text("Saiba o que está sendo oferecido antes de entrar em contato.", color="rgba(255,255,255,0.8)", font_size="0.95rem"),
                        bg="rgba(255,255,255,0.12)",
                        border="1px solid rgba(255,255,255,0.12)",
                        border_radius="22px",
                        padding="5",
                    ),
                    rx.box(
                        rx.text("🛡", font_size="2rem"),
                        rx.heading("Experiência segura", size="5", color="white"),
                        rx.text("Recursos pensados para tornar a jornada mais confiável.", color="rgba(255,255,255,0.8)", font_size="0.95rem"),
                        bg="rgba(255,255,255,0.12)",
                        border="1px solid rgba(255,255,255,0.12)",
                        border_radius="22px",
                        padding="5",
                    ),
                    rx.box(
                        rx.text("💚", font_size="2rem"),
                        rx.heading("Comunidade", size="5", color="white"),
                        rx.text("Uma plataforma feita para aproximar quem pode ajudar de quem precisa.", color="rgba(255,255,255,0.8)", font_size="0.95rem"),
                        bg="rgba(255,255,255,0.12)",
                        border="1px solid rgba(255,255,255,0.12)",
                        border_radius="22px",
                        padding="5",
                    ),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                spacing="6",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background=PRIMARY["dark"],
    )


def render_impact_story() -> rx.Component:
    return rx.box(
        rx.container(
            rx.hstack(
                rx.vstack(
                    rx.heading("Pequenos gestos podem mudar grandes histórias.", size="7", color=PRIMARY["dark"]),
                    rx.text(
                        "Quando você doa aquilo que não usa mais, abre espaço para que outra pessoa encontre uma solução real, acolhedora e útil.",
                        color=PRIMARY["muted"],
                        font_size="1.05rem",
                        line_height="1.8",
                    ),
                    rx.hstack(
                        rx.box(
                            rx.text("+1.240", color=PRIMARY["dark"], font_weight="800", font_size="1.7rem"),
                            rx.text("doações", color=PRIMARY["muted"], font_size="0.88rem"),
                            spacing="1",
                            align="center",
                        ),
                        rx.box(
                            rx.text("+680", color=PRIMARY["dark"], font_weight="800", font_size="1.7rem"),
                            rx.text("pessoas", color=PRIMARY["muted"], font_size="0.88rem"),
                            spacing="1",
                            align="center",
                        ),
                        rx.box(
                            rx.text("+32", color=PRIMARY["dark"], font_weight="800", font_size="1.7rem"),
                            rx.text("categorias", color=PRIMARY["muted"], font_size="0.88rem"),
                            spacing="1",
                            align="center",
                        ),
                        spacing="6",
                        wrap="wrap",
                    ),
                    spacing="5",
                    align="start",
                    width=["100%", "100%", "52%"],
                ),
                rx.box(
                    rx.box(
                        rx.box(
                            rx.text("💛", font_size="2rem"),
                            rx.text("+1.240\ndoações", color=PRIMARY["dark"], font_weight="700", line_height="1.3"),
                            bg="white",
                            border_radius="22px",
                            box_shadow="0 18px 30px rgba(17,61,49,0.08)",
                            padding="4",
                            width="170px",
                        ),
                        rx.box(
                            rx.text("🧥", font_size="2rem"),
                            rx.text("+680\npessoas", color=PRIMARY["dark"], font_weight="700", line_height="1.3"),
                            bg="rgba(255,255,255,0.7)",
                            border_radius="22px",
                            box_shadow="0 18px 30px rgba(17,61,49,0.08)",
                            padding="4",
                            width="170px",
                        ),
                        rx.box(
                            rx.text("📚", font_size="2rem"),
                            rx.text("+32\ncategorias", color=PRIMARY["dark"], font_weight="700", line_height="1.3"),
                            bg="white",
                            border_radius="22px",
                            box_shadow="0 18px 30px rgba(17,61,49,0.08)",
                            padding="4",
                            width="170px",
                        ),
                        position="relative",
                        z_index="2",
                        spacing="4",
                    ),
                    rx.box(
                        rx.text("”,", color=PRIMARY["green"], font_size="4rem", font_weight="700"),
                        position="absolute",
                        top="-10px",
                        right="36px",
                    ),
                    bg="linear-gradient(135deg, rgba(24,165,102,0.08) 0%, rgba(244,183,64,0.14) 100%)",
                    border="1px solid rgba(24,165,102,0.08)",
                    border_radius="32px",
                    min_height="350px",
                    width=["100%", "100%", "48%"],
                    position="relative",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    padding="6",
                ),
                justify="between",
                align="center",
                width="100%",
                spacing="6",
                wrap="wrap",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background=PRIMARY["cream"],
    )


def render_emotional_cta() -> rx.Component:
    return rx.box(
        rx.container(
            rx.box(
                rx.vstack(
                    rx.text("O que não faz mais falta para você pode significar muito para alguém.", font_size="2.2rem", font_weight="700", color="white", line_height="1.15", max_width="820px"),
                    rx.text(
                        "Uma peça de roupa, um livro, um móvel ou uma cesta de alimentos pode começar uma nova história.",
                        color="rgba(255,255,255,0.82)",
                        font_size="1.08rem",
                        line_height="1.8",
                        max_width="780px",
                    ),
                    rx.button(
                        "Quero fazer uma doação",
                        bg=PRIMARY["yellow"],
                        color=PRIMARY["dark"],
                        border_radius="999px",
                        px="7",
                        py="3",
                        box_shadow="0 18px 32px rgba(244,183,64,0.3)",
                    ),
                    spacing="5",
                    align="start",
                ),
                bg=PRIMARY["green"],
                border_radius="30px",
                padding=["6", "6", "7"],
                width="100%",
                position="relative",
                overflow="hidden",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="6",
        ),
        width="100%",
        background="white",
    )


def render_final_cta() -> rx.Component:
    return rx.box(
        rx.container(
            rx.box(
                rx.vstack(
                    rx.text("Pronto para fazer a diferença?", color=PRIMARY["dark"], font_size="2.2rem", font_weight="700"),
                    rx.text(
                        "Comece com uma pequena doação e ajude algo que você não usa mais a encontrar um novo destino.",
                        color=PRIMARY["muted"],
                        font_size="1.05rem",
                        max_width="620px",
                        text_align="center",
                    ),
                    rx.button(
                        "Começar agora",
                        bg=PRIMARY["green"],
                        color="white",
                        border_radius="999px",
                        px="7",
                        py="3",
                        box_shadow="0 18px 30px rgba(24,165,102,0.2)",
                    ),
                    spacing="5",
                    align="center",
                ),
                bg="rgba(24,165,102,0.05)",
                border="1px solid rgba(24,165,102,0.08)",
                border_radius="28px",
                padding=["8", "6", "9"],
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="7",
        ),
        width="100%",
        background="white",
    )


def render_footer() -> rx.Component:
    return rx.box(
        rx.container(
            rx.grid(
                rx.vstack(
                    rx.text("DoaFácil", color="white", font_size="2rem", font_weight="700"),
                    rx.text(
                        "Uma plataforma para conectar doações com pessoas que precisam de ajuda de forma simples e acolhedora.",
                        color="rgba(255,255,255,0.72)",
                        line_height="1.8",
                    ),
                    rx.text("© 2026 DoaFácil. Todos os direitos reservados.", color="rgba(255,255,255,0.62)", font_size="0.88rem"),
                    spacing="4",
                    align="start",
                ),
                rx.vstack(
                    rx.text("Sobre nós", color="white", font_weight="700"),
                    rx.link("Como funciona", href="#como-funciona", style={"color": "rgba(255,255,255,0.7)", "text_decoration": "none"}),
                    rx.link("Categorias", href="#categorias", style={"color": "rgba(255,255,255,0.7)", "text_decoration": "none"}),
                    rx.link("Explorar doações", href="#explorar", style={"color": "rgba(255,255,255,0.7)", "text_decoration": "none"}),
                    spacing="3",
                    align="start",
                ),
                rx.vstack(
                    rx.text("Ajuda", color="white", font_weight="700"),
                    rx.text("Central de ajuda", color="rgba(255,255,255,0.7)"),
                    rx.text("Termos", color="rgba(255,255,255,0.7)"),
                    rx.text("Privacidade", color="rgba(255,255,255,0.7)"),
                    spacing="3",
                    align="start",
                ),
                rx.vstack(
                    rx.text("Comunidade", color="white", font_weight="700"),
                    rx.text("Explorar doações", color="rgba(255,255,255,0.7)"),
                    rx.text("Quero doar", color="rgba(255,255,255,0.7)"),
                    rx.text("Entrar", color="rgba(255,255,255,0.7)"),
                    spacing="3",
                    align="start",
                ),
                columns="4",
                spacing="8",
                width="100%",
            ),
            max_width="1200px",
            width="100%",
            padding_x=["4", "5", "6"],
            padding_y="10",
        ),
        width="100%",
        background=PRIMARY["dark"],
    )


def index() -> rx.Component:
    return rx.box(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            render_home_navbar(),
            render_home_hero(),
            render_search_section(),
            render_impact_stats(),
            render_category_section(),
            render_featured_donations_carousel(),
            render_how_it_works(),
            render_security_section(),
            render_impact_story(),
            render_emotional_cta(),
            render_final_cta(),
            render_footer(),
            width="100%",
            spacing="0",
            background=PRIMARY["background"],
            color=PRIMARY["text"],
        ),
        width="100%",
    )


app = rx.App()
app.add_page(index, on_load=AuthState.hydrate)
