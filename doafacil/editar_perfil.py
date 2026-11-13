"""Editar perfil: cliente do GET/PATCH auth/profile, estado e página.

Rota /perfil/editar, só com login. A pessoa vem sempre do token (o Xano lê o
$auth.id); o frontend envia só o formulário inteiro. Layout segundo o frame
Group 7 do Figma, com as diferenças registradas em docs/design/README.md (que
prevalece). Todo dado vindo do Xano é renderizado com componentes de texto,
sem HTML.
"""

from __future__ import annotations

from typing import Any

import httpx
import reflex as rx

from doafacil.cadastro import BRAZILIAN_STATES
from doafacil.cadastro_doacao import AUTH_API_ENV, DonationServiceError, _api_endpoint
from doafacil.chat import PLATFORM_RATE_LIMIT_MESSAGE, avatar_initial, back_link_header
from doafacil.login import LoginState
from doafacil.minhas_doacoes import (
    MyDonationsState,
    SAVED_MESSAGE,
    _edit_select,
    _field_label,
    _state_message,
)
from doafacil.perfil_doador import location_label
from doafacil.sobre import ABOUT_MAX_LENGTH, about_text, parse_about


PROFILE_PATH = "/auth/profile"
PAGE_TITLE = "Editar perfil"
BACK_LABEL = "Voltar a Minhas doações"
LOADING_MESSAGE = "Carregando seu perfil..."
LOAD_ERROR_MESSAGE = "Não foi possível carregar seu perfil. Tente novamente mais tarde."
RATE_LIMIT_MESSAGE = PLATFORM_RATE_LIMIT_MESSAGE
SAVE_ERROR_MESSAGE = "Não foi possível salvar as alterações. Tente novamente."
SAVE_REJECTED_MESSAGE = "Não foi possível salvar. Confira os campos e tente novamente."
NAME_HELP = "Só o primeiro nome aparece para outras pessoas."
ABOUT_PLACEHOLDER = "Conte um pouco sobre você"
ABOUT_HINT = "Não coloque telefone, endereço ou e-mail: este texto é público."
EMAIL_HELP = "O e-mail é usado para entrar e não pode ser alterado."
EMAIL_ARIA_LABEL = "E-mail (não pode ser alterado)"
PREVIEW_CAPTION = "Prévia — é assim que seu perfil aparece para outras pessoas."
VISIBILITY_TITLE = "Quem vê estas informações"
VISIBILITY_TEXT = (
    "Seu primeiro nome, cidade, estado e o texto de Sobre aparecem no seu perfil "
    "público. Suas doações mostram o primeiro nome e a cidade e o estado do "
    "momento em que foram publicadas. Seu e-mail é usado para entrar e só é "
    "mostrado a pessoas logadas que pedirem contato numa doação sua com a "
    "preferência “E-mail”."
)


class ProfileError(Exception):
    pass


class ProfileUnauthorizedError(ProfileError):
    pass


class ProfileRejectedError(ProfileError):
    pass


class ProfileRateLimitError(ProfileError):
    pass


class ProfileServiceError(ProfileError):
    pass


def _endpoint() -> str:
    try:
        return _api_endpoint(AUTH_API_ENV, PROFILE_PATH)
    except DonationServiceError:
        raise ProfileServiceError from None


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code == 401:
        raise ProfileUnauthorizedError
    if response.status_code == 400:
        raise ProfileRejectedError
    if response.status_code == 429:
        raise ProfileRateLimitError
    if response.status_code != 200:
        raise ProfileServiceError


def _parse_profile(payload: object) -> dict[str, str]:
    """Só os campos usados; campos extras são ignorados."""
    if not isinstance(payload, dict):
        raise ProfileServiceError
    fields = {key: payload.get(key) for key in ("name", "email", "city", "state")}
    if any(not isinstance(value, str) for value in fields.values()):
        raise ProfileServiceError
    try:
        about = parse_about(payload.get("about"))
    except ValueError:
        raise ProfileServiceError from None
    return {
        "name": fields["name"].strip(),
        "email": fields["email"].strip(),
        "city": fields["city"].strip(),
        "state": fields["state"].strip(),
        "about": about,
    }


def _json(response: httpx.Response) -> object:
    try:
        return response.json()
    except ValueError:
        raise ProfileServiceError from None


async def fetch_profile(client: httpx.AsyncClient, auth_token: str) -> dict[str, str]:
    response = await client.get(
        _endpoint(), headers={"Authorization": f"Bearer {auth_token}"}
    )
    _raise_for_status(response)
    return _parse_profile(_json(response))


async def update_profile(
    client: httpx.AsyncClient, auth_token: str, fields: dict[str, str]
) -> dict[str, str]:
    response = await client.patch(
        _endpoint(),
        json=fields,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    _raise_for_status(response)
    return _parse_profile(_json(response))


def first_name_of(name: str) -> str:
    parts = name.strip().split(maxsplit=1)
    return parts[0] if parts else ""


def validate_profile(name: str, city: str, uf: str, about: str) -> str:
    """Mesmas regras e mensagens do cadastro de conta, e o Sobre até 300."""
    if not name.strip():
        return "Informe seu nome."
    if not city.strip():
        return "Informe sua cidade."
    if uf not in BRAZILIAN_STATES:
        return "Selecione seu estado."
    if len(about.strip()) > ABOUT_MAX_LENGTH:
        return f"O Sobre pode ter no máximo {ABOUT_MAX_LENGTH} caracteres."
    return ""


def _new_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=15.0)


def _clear_session(state: Any) -> None:
    state.auth_token = ""
    state.account_name = ""


def _clear_form(state: Any) -> None:
    state.name = ""
    state.email = ""
    state.city = ""
    state.uf = ""
    state.about = ""
    state.form_error = ""
    state.is_saving = False


class EditProfileState(LoginState):
    view_state: str = "loading"
    load_error: str = ""
    name: str = ""
    email: str = ""
    city: str = ""
    # “uf”, e não “state”, para não confundir com o estado do Reflex.
    uf: str = ""
    about: str = ""
    form_error: str = ""
    is_saving: bool = False

    @rx.var
    def preview_first_name(self) -> str:
        return first_name_of(self.name)

    @rx.var
    def preview_initial(self) -> str:
        return avatar_initial(first_name_of(self.name))

    @rx.var
    def preview_location(self) -> str:
        return location_label(self.city, self.uf)

    @rx.var
    def preview_about(self) -> str:
        return self.about.strip()

    @rx.var
    def about_count(self) -> str:
        return f"{len(self.about)}/{ABOUT_MAX_LENGTH}"

    @rx.event
    async def load_profile(self):
        _clear_form(self)
        self.view_state = "loading"
        self.load_error = ""
        if not self.auth_token:
            yield rx.redirect("/login")
            return
        try:
            async with _new_client() as client:
                profile = await fetch_profile(client, self.auth_token)
        except ProfileUnauthorizedError:
            _clear_session(self)
            yield rx.redirect("/login")
            return
        except ProfileRateLimitError:
            self.load_error = RATE_LIMIT_MESSAGE
            self.view_state = "error"
            return
        except (ProfileError, httpx.HTTPError, ValueError):
            self.load_error = LOAD_ERROR_MESSAGE
            self.view_state = "error"
            return
        self.name = profile["name"]
        self.email = profile["email"]
        self.city = profile["city"]
        # Uma UF fora das 27 siglas deixa o campo vazio, para ser escolhida.
        self.uf = profile["state"] if profile["state"] in BRAZILIAN_STATES else ""
        self.about = profile["about"]
        self.view_state = "ready"

    @rx.event
    def set_name(self, value: str) -> None:
        self.name = value

    @rx.event
    def set_city(self, value: str) -> None:
        self.city = value

    @rx.event
    def set_uf(self, value: str) -> None:
        self.uf = value

    @rx.event
    def set_about(self, value: str) -> None:
        self.about = value[:ABOUT_MAX_LENGTH]

    @rx.event
    async def save(self):
        if self.is_saving or self.view_state != "ready":
            return
        error = validate_profile(self.name, self.city, self.uf, self.about)
        if error:
            self.form_error = error
            return

        self.form_error = ""
        self.is_saving = True
        yield
        # Sempre o formulário inteiro: o Xano grava o Sobre em toda
        # atualização (vazio apaga).
        fields = {
            "name": self.name.strip(),
            "city": self.city.strip(),
            "state": self.uf,
            "about": self.about.strip(),
        }
        try:
            async with _new_client() as client:
                profile = await update_profile(client, self.auth_token, fields)
        except ProfileUnauthorizedError:
            _clear_session(self)
            self.is_saving = False
            yield rx.redirect("/login")
            return
        except ProfileRejectedError:
            self.form_error = SAVE_REJECTED_MESSAGE
        except ProfileRateLimitError:
            self.form_error = RATE_LIMIT_MESSAGE
        except (ProfileError, httpx.HTTPError, ValueError):
            self.form_error = SAVE_ERROR_MESSAGE
        else:
            # O cabeçalho da home passa a mostrar o primeiro nome novo.
            self.account_name = first_name_of(profile["name"]) or self.account_name
            self.is_saving = False
            yield MyDonationsState.set_flash(SAVED_MESSAGE)
            yield rx.redirect("/minhas-doacoes")
            return
        self.is_saving = False


# Página -----------------------------------------------------------------------

CREAM = "#FFF6E8"
WHITE = "#FFFFFF"
BORDER_SOFT = "#D9D9D9"
FIELD_BORDER = "1px solid #C8C8C8"
TITLE_GREEN = "#166B3B"
LINK_GREEN = "#007A42"
LINK_GREEN_HOVER = "#006B39"
TEXT_STRONG = "#2A2A2A"
TEXT_FIELD = "#1F1F1F"
TEXT_MUTED = "#555555"
TEXT_ERROR = "#9B2C2C"
AVATAR_BACKGROUND = "#F2F2F2"
READ_ONLY_BACKGROUND = "#F1F1F1"
LOCK_ICON_COLOR = "#6B6B6B"
NOTICE_BACKGROUND = "#FFF3D6"


def _input(value: rx.Var, on_change: Any, field_id: str, **props: Any) -> rx.Component:
    return rx.input(
        value=value,
        on_change=on_change,
        id=field_id,
        width="100%",
        height="40px",
        background=WHITE,
        color=TEXT_FIELD,
        border=FIELD_BORDER,
        border_radius="8px",
        **props,
    )


def _help(text: str | rx.Var, help_id: str | None = None, **props: Any) -> rx.Component:
    extra = {"id": help_id} if help_id else {}
    return rx.text(
        text,
        color=TEXT_MUTED,
        font_size="0.8rem",
        line_height="1.4",
        width="100%",
        **extra,
        **props,
    )


def _section_title(text: str) -> rx.Component:
    return rx.heading(
        text,
        as_="h2",
        color=TITLE_GREEN,
        font_size="1.2rem",
        font_weight="700",
        width="100%",
        padding_top="8px",
    )


def _preview() -> rx.Component:
    """Prévia: inicial, primeiro nome, “Cidade, UF” e Sobre. Sem e-mail,
    contadores, foto, “Editar perfil” ou “Compartilhar”."""
    return rx.vstack(
        rx.vstack(
            rx.box(
                rx.text(
                    EditProfileState.preview_initial,
                    color=TEXT_MUTED,
                    font_weight="700",
                    font_size="2rem",
                    line_height="1",
                ),
                aria_hidden="true",
                display="flex",
                align_items="center",
                justify_content="center",
                width="80px",
                height="80px",
                border_radius="999px",
                background=AVATAR_BACKGROUND,
            ),
            rx.text(
                EditProfileState.preview_first_name,
                color=TEXT_STRONG,
                font_size="1.15rem",
                font_weight="700",
                text_align="center",
                overflow_wrap="anywhere",
            ),
            rx.text(
                EditProfileState.preview_location,
                color=TEXT_STRONG,
                font_size="0.95rem",
                text_align="center",
                overflow_wrap="anywhere",
            ),
            about_text(EditProfileState.preview_about, text_align="center"),
            class_name="edit-profile-preview",
            align="center",
            spacing="2",
            width="100%",
            padding="24px 16px",
            background=WHITE,
            border=f"1px solid {BORDER_SOFT}",
            border_radius="8px",
        ),
        _help(PREVIEW_CAPTION),
        align="stretch",
        spacing="2",
        width="100%",
    )


def _visibility_notice() -> rx.Component:
    return rx.box(
        rx.text(VISIBILITY_TITLE, color=TITLE_GREEN, font_weight="700", font_size="0.95rem"),
        rx.text(VISIBILITY_TEXT, color=TEXT_STRONG, font_size="0.85rem", line_height="1.5", padding_top="4px"),
        class_name="edit-profile-visibility",
        width="100%",
        padding="16px",
        background=NOTICE_BACKGROUND,
        border=f"1px solid {TEXT_STRONG}",
        border_radius="8px",
    )


def _form() -> rx.Component:
    return rx.vstack(
        _section_title("Dados públicos"),
        _field_label("Nome", "profile-name"),
        _input(
            EditProfileState.name,
            EditProfileState.set_name,
            "profile-name",
            aria_describedby="profile-name-help",
        ),
        _help(NAME_HELP, "profile-name-help"),
        _field_label("Sobre", "profile-about"),
        rx.text_area(
            value=EditProfileState.about,
            on_change=EditProfileState.set_about,
            id="profile-about",
            placeholder=ABOUT_PLACEHOLDER,
            max_length=ABOUT_MAX_LENGTH,
            aria_describedby="profile-about-count profile-about-hint",
            min_height="120px",
            width="100%",
            background=WHITE,
            color=TEXT_FIELD,
            border=FIELD_BORDER,
            border_radius="8px",
        ),
        _help(
            EditProfileState.about_count,
            "profile-about-count",
            aria_live="polite",
        ),
        _help(ABOUT_HINT, "profile-about-hint"),
        _section_title("Localização"),
        rx.box(
            rx.vstack(
                _field_label("Cidade", "profile-city"),
                _input(EditProfileState.city, EditProfileState.set_city, "profile-city"),
                align="start",
                spacing="2",
                width="100%",
            ),
            _edit_select(
                "Estado",
                BRAZILIAN_STATES,
                EditProfileState.uf,
                EditProfileState.set_uf,
                "Selecione o estado",
                "profile-state",
            ),
            class_name="edit-profile-location",
            style={
                "display": "grid",
                "gridTemplateColumns": rx.breakpoints(
                    initial="minmax(0, 1fr)",
                    md="repeat(2, minmax(0, 1fr))",
                ),
            },
            gap="16px",
            width="100%",
        ),
        _section_title("Conta"),
        _field_label("E-mail", "profile-email"),
        # Só de leitura (readOnly, não disabled): dá para selecionar e copiar.
        # Texto #1F1F1F sobre #F1F1F1 (15:1) e cadeado à direita.
        rx.input(
            rx.input.slot(
                rx.icon("lock", size=16, color=LOCK_ICON_COLOR, aria_hidden="true"),
                side="right",
            ),
            value=EditProfileState.email,
            id="profile-email",
            read_only=True,
            aria_label=EMAIL_ARIA_LABEL,
            aria_describedby="profile-email-help",
            class_name="edit-profile-email",
            width="100%",
            height="40px",
            background=READ_ONLY_BACKGROUND,
            color=TEXT_FIELD,
            border=FIELD_BORDER,
            border_radius="8px",
            cursor="default",
            style={"& input": {"cursor": "default"}},
        ),
        _help(EMAIL_HELP, "profile-email-help"),
        _visibility_notice(),
        rx.cond(
            EditProfileState.form_error != "",
            rx.text(
                EditProfileState.form_error,
                role="alert",
                color=TEXT_ERROR,
                font_size="0.9rem",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.link(
                "Cancelar",
                href="/minhas-doacoes",
                display="inline-flex",
                align_items="center",
                min_height="44px",
                padding="0 20px",
                border="1px solid #85858D",
                border_radius="999px",
                color=TEXT_STRONG,
                font_weight="600",
                _hover={"textDecoration": "none", "background": "#F7F8F7"},
            ),
            rx.button(
                rx.cond(EditProfileState.is_saving, "Salvando...", "Salvar alterações"),
                on_click=EditProfileState.save,
                disabled=EditProfileState.is_saving,
                min_height="44px",
                padding="0 24px",
                border_radius="999px",
                background=LINK_GREEN,
                color="white",
                font_weight="700",
                cursor="pointer",
                _hover={"background": LINK_GREEN_HOVER},
            ),
            spacing="3",
            wrap="wrap",
            width="100%",
            padding_top="8px",
        ),
        class_name="auth-card-enter",
        align="start",
        spacing="3",
        width="100%",
        padding=rx.breakpoints(initial="24px 16px", md="32px 40px"),
        background=WHITE,
        border=f"1px solid {BORDER_SOFT}",
        border_radius="8px",
    )


def _content() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                PAGE_TITLE,
                as_="h1",
                color=TITLE_GREEN,
                font_size=rx.breakpoints(initial="1.75rem", md="2.25rem"),
                font_weight="700",
                text_align="left",
                width="100%",
                class_name="page-fade-enter",
            ),
            rx.box(
                rx.box(_preview(), min_width="0"),
                rx.box(_form(), min_width="0"),
                class_name="edit-profile-layout",
                style={
                    "display": "grid",
                    "gridTemplateColumns": rx.breakpoints(
                        initial="minmax(0, 1fr)",
                        md="minmax(220px, 280px) minmax(0, 1fr)",
                    ),
                    "alignItems": "start",
                },
                gap="32px",
                width="100%",
            ),
            align="stretch",
            spacing="5",
            width="100%",
            max_width="1236px",
            margin="0 auto",
        ),
        width="100%",
        min_height="calc(100vh - 88px)",
        padding=rx.breakpoints(initial="24px 16px 48px", md="32px 24px 56px"),
        background=CREAM,
    )


def edit_profile_page() -> rx.Component:
    return rx.box(
        back_link_header("/minhas-doacoes", BACK_LABEL, LINK_GREEN),
        rx.match(
            EditProfileState.view_state,
            ("loading", _state_message(LOADING_MESSAGE, TEXT_MUTED)),
            ("error", _state_message(EditProfileState.load_error, TEXT_ERROR)),
            _content(),
        ),
        display="flex",
        flex_direction="column",
        width="100%",
        min_height="100vh",
        background=CREAM,
        font_family="'LINE Seed JP', Arial, sans-serif",
    )
