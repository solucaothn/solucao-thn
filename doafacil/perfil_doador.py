"""Perfil público de quem doa: cliente do Xano, estado e página.

A rota é /doacao/<id>/quem-doa: o perfil é aberto a partir de uma doação, e o
frontend nunca recebe o id de usuário de quem doa. Layout segundo os frames
perfil-doador-01 e perfil-doador-02 do Figma, com as diferenças registradas em
docs/design/README.md (que prevalece). Todo dado vindo do Xano é renderizado
com componentes de texto, sem HTML.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

import httpx
import reflex as rx

from doafacil.cartoes_doacao import _parse_donations, donation_grid_card
from doafacil.chat import PLATFORM_RATE_LIMIT_MESSAGE, avatar_initial, back_link_header
from doafacil.sobre import about_text, parse_about
from doafacil.detalhe_doacao import (
    DONATION_NOT_FOUND_MESSAGE,
    DonationNotFoundError,
    _positive_donation_id,
)


DONOR_PROFILE_PATH = "/catalog/donations/donor"
PROFILE_PER_PAGE = 12
BACK_TO_DONATION_LABEL = "Voltar à doação"
PROFILE_LOADING_MESSAGE = "Carregando perfil..."
PROFILE_ERROR_MESSAGE = (
    "Não foi possível carregar o perfil de quem doa. Tente novamente mais tarde."
)
PROFILE_PAGE_ERROR_MESSAGE = (
    "Não foi possível carregar esta página de doações. Tente novamente."
)
PROFILE_RATE_LIMIT_MESSAGE = PLATFORM_RATE_LIMIT_MESSAGE
DONATIONS_TITLE = "Doações disponíveis"
EMPTY_TITLE = "Nenhuma doação disponível no momento"
EXPLORE_LINK_LABEL = "Explorar outras doações"
MONTHS_PT_BR = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)
_MEMBER_SINCE_PATTERN = re.compile(r"([0-9]{4})-(0[1-9]|1[0-2])")


class DonorProfileNotFoundError(Exception):
    pass


class DonorProfileRateLimitError(Exception):
    pass


class DonorProfileServiceError(Exception):
    pass


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _donor_profile_endpoint(base_url: str, donation_id: int, page: int) -> str:
    parsed_url = urlsplit(base_url.strip())
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("XANO_API_URL precisa conter uma URL HTTP(S) válida.")
    return (
        f"{base_url.strip().rstrip('/')}{DONOR_PROFILE_PATH}"
        f"?donation_id={donation_id}&page={page}"
    )


def member_since_label(value: str) -> str:
    """'2020-10' → 'outubro de 2020'."""
    match = _MEMBER_SINCE_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError("member_since precisa estar no formato AAAA-MM.")
    return f"{MONTHS_PT_BR[int(match.group(2)) - 1]} de {match.group(1)}"


def items_count_label(total: int) -> str:
    return "1 item" if total == 1 else f"{total} itens"


def location_label(city: str, state: str) -> str:
    return ", ".join(part for part in (city.strip(), state.strip()) if part)


def _parse_donor_profile(
    payload: object, now: datetime | None = None
) -> dict[str, Any]:
    """Valida a resposta e devolve só os campos permitidos.

    Campos extras (como e-mail ou owner_id, se aparecessem) são ignorados e
    nunca chegam ao estado.
    """
    if not isinstance(payload, dict):
        raise ValueError("A resposta do perfil precisa ser um objeto.")

    donor = payload.get("donor")
    if not isinstance(donor, dict):
        raise ValueError("A resposta do perfil não tem os dados de quem doa.")
    first_name = donor.get("first_name")
    city = donor.get("city")
    state = donor.get("state")
    member_since = donor.get("member_since")
    if (
        not isinstance(first_name, str)
        or not first_name.strip()
        or not isinstance(city, str)
        or not isinstance(state, str)
        or not isinstance(member_since, str)
        or _MEMBER_SINCE_PATTERN.fullmatch(member_since) is None
    ):
        raise ValueError("A resposta do perfil contém dados inválidos.")
    about = parse_about(donor.get("about"))

    page = payload.get("page")
    total = payload.get("total")
    page_total = payload.get("page_total")
    if (
        not _is_int(page)
        or not _is_int(total)
        or not _is_int(page_total)
        or page < 1
        or total < 0
        or page_total < 0
    ):
        raise ValueError("A paginação do perfil é inválida.")

    return {
        "first_name": first_name.strip(),
        "city": city,
        "state": state,
        "member_since": member_since,
        "about": about,
        "items": _parse_donations(payload.get("items"), now),
        "page": page,
        "total": total,
        "page_total": page_total,
    }


async def fetch_donor_profile(
    client: httpx.AsyncClient,
    base_url: str,
    donation_id: int,
    page: int = 1,
) -> dict[str, Any]:
    endpoint = _donor_profile_endpoint(base_url, donation_id, page)
    response = await client.get(endpoint)
    if response.status_code == 404:
        raise DonorProfileNotFoundError
    if response.status_code == 429:
        raise DonorProfileRateLimitError
    if response.status_code != 200:
        raise DonorProfileServiceError
    try:
        payload = response.json()
    except ValueError as error:
        raise ValueError("A resposta do perfil não é JSON.") from error
    return _parse_donor_profile(payload)


class DonorProfileState(rx.State):
    view_state: str = "loading"
    error_message: str = ""
    donation_id: int = 0
    back_href: str = "/"
    first_name: str = ""
    initial: str = ""
    location: str = ""
    member_since_label: str = ""
    about: str = ""
    items: list[dict[str, Any]] = []
    total: int = 0
    count_label: str = ""
    page: int = 1
    page_total: int = 0
    page_loading: bool = False
    page_error: str = ""

    def _apply_profile(self, profile: dict[str, Any]) -> None:
        self.first_name = profile["first_name"]
        self.initial = avatar_initial(profile["first_name"])
        self.location = location_label(profile["city"], profile["state"])
        self.member_since_label = member_since_label(profile["member_since"])
        self.about = profile["about"]
        self.items = profile["items"]
        self.total = profile["total"]
        self.count_label = items_count_label(profile["total"])
        self.page = profile["page"]
        self.page_total = profile["page_total"]

    def _clear_profile(self) -> None:
        self.first_name = ""
        self.initial = ""
        self.location = ""
        self.member_since_label = ""
        self.about = ""
        self.items = []
        self.total = 0
        self.count_label = ""
        self.page = 1
        self.page_total = 0

    @rx.event
    async def load_profile(self) -> None:
        DonorProfileState._clear_profile(self)
        self.view_state = "loading"
        self.error_message = ""
        self.donation_id = 0
        self.back_href = "/"
        self.page_loading = False
        self.page_error = ""

        try:
            donation_id = _positive_donation_id(
                self.router.page.params.get("id", "")
            )
        except DonationNotFoundError:
            # Id inválido: nenhuma requisição, e o voltar leva ao início.
            self.view_state = "not_found"
            return

        self.donation_id = donation_id
        self.back_href = f"/doacao/{donation_id}"
        try:
            base_url = os.getenv("XANO_API_URL", "").strip()
            async with httpx.AsyncClient(timeout=15.0) as client:
                profile = await fetch_donor_profile(client, base_url, donation_id, 1)
        except DonorProfileNotFoundError:
            self.view_state = "not_found"
        except DonorProfileRateLimitError:
            self.error_message = PROFILE_RATE_LIMIT_MESSAGE
            self.view_state = "error"
        except (DonorProfileServiceError, httpx.HTTPError, ValueError):
            self.error_message = PROFILE_ERROR_MESSAGE
            self.view_state = "error"
        else:
            DonorProfileState._apply_profile(self, profile)
            self.view_state = "ready"

    @rx.event
    async def go_to_page(self, page: int):
        """Uma requisição só para a página pedida.

        Ignora cliques durante o carregamento e fora do intervalo. Com erro, a
        página anterior continua visível e a mensagem aparece junto da
        paginação.
        """
        if self.view_state != "ready" or self.page_loading:
            return
        try:
            target = int(page)
        except (TypeError, ValueError):
            return
        if target < 1 or target > self.page_total or target == self.page:
            return

        self.page_loading = True
        self.page_error = ""
        yield
        try:
            base_url = os.getenv("XANO_API_URL", "").strip()
            async with httpx.AsyncClient(timeout=15.0) as client:
                profile = await fetch_donor_profile(
                    client, base_url, self.donation_id, target
                )
        except DonorProfileNotFoundError:
            # A doação de origem deixou de estar disponível.
            DonorProfileState._clear_profile(self)
            self.view_state = "not_found"
        except DonorProfileRateLimitError:
            self.page_error = PROFILE_RATE_LIMIT_MESSAGE
        except (DonorProfileServiceError, httpx.HTTPError, ValueError):
            self.page_error = PROFILE_PAGE_ERROR_MESSAGE
        else:
            DonorProfileState._apply_profile(self, profile)
        finally:
            self.page_loading = False


# Página ---------------------------------------------------------------------

CREAM = "#FFF6E8"
WHITE = "#FFFFFF"
BORDER_SOFT = "#D9D9D9"
TITLE_GREEN = "#166B3B"
LINK_GREEN = "#007A42"
LINK_GREEN_HOVER = "#006B39"
TEXT_STRONG = "#2A2A2A"
TEXT_MUTED = "#555555"
TEXT_ERROR = "#9B2C2C"
AVATAR_BACKGROUND = "#F2F2F2"
CONTENT_MAX_WIDTH = "1396px"
CARDS_GRID_COLUMNS = "repeat(auto-fill, minmax(220px, 1fr))"


def _state_message(message: rx.Var | str, color: str) -> rx.Component:
    return rx.box(
        rx.text(message, color=color, text_align="center"),
        display="flex",
        align_items="center",
        justify_content="center",
        width="100%",
        min_height="calc(100vh - 88px)",
        padding="24px 16px",
        background=CREAM,
        class_name="page-fade-enter",
    )


def _identity_card() -> rx.Component:
    """Círculo com a inicial, primeiro nome, “Cidade, UF” e “membro desde”.

    Sem foto de perfil e sem selo de e-mail verificado (fora do escopo).
    """
    avatar_size = rx.breakpoints(initial="72px", md="120px")
    return rx.flex(
        rx.box(
            rx.text(
                DonorProfileState.initial,
                color=TEXT_MUTED,
                font_weight="700",
                font_size=rx.breakpoints(initial="2rem", md="3rem"),
                line_height="1",
            ),
            aria_hidden="true",
            class_name="donor-profile-avatar",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
            width=avatar_size,
            height=avatar_size,
            border_radius="999px",
            background=AVATAR_BACKGROUND,
        ),
        rx.vstack(
            rx.heading(
                DonorProfileState.first_name,
                as_="h1",
                color=TITLE_GREEN,
                font_size=rx.breakpoints(initial="1.6rem", md="2rem"),
                font_weight="700",
                line_height="1.2",
                overflow_wrap="anywhere",
            ),
            rx.text(
                DonorProfileState.location,
                color=TEXT_STRONG,
                font_size="1rem",
                overflow_wrap="anywhere",
            ),
            rx.text(
                "No DoaFácil desde ",
                DonorProfileState.member_since_label,
                color=TEXT_MUTED,
                font_size="0.95rem",
            ),
            # Sobre de quem doa: texto simples; vazio, nada.
            about_text(DonorProfileState.about, padding_top="4px"),
            spacing="2",
            align=rx.breakpoints(initial="center", md="start"),
            text_align=rx.breakpoints(initial="center", md="left"),
            min_width="0",
        ),
        class_name="donor-profile-identity",
        # No celular, o círculo fica acima do texto.
        direction=rx.breakpoints(initial="column", md="row"),
        align="center",
        gap=rx.breakpoints(initial="16px", md="32px"),
        width="100%",
        padding=rx.breakpoints(initial="24px 16px", md="32px 40px"),
        background=WHITE,
        border=f"1px solid {BORDER_SOFT}",
        border_radius="8px",
    )


def _page_button(label: str, target: rx.Var, disabled: rx.Var) -> rx.Component:
    return rx.button(
        label,
        on_click=DonorProfileState.go_to_page(target),
        disabled=disabled,
        min_height="44px",
        padding="0 20px",
        background=WHITE,
        color=LINK_GREEN,
        border=f"1px solid {LINK_GREEN}",
        border_radius="999px",
        font_weight="600",
        cursor="pointer",
        _hover={"background": "#F1F8F3"},
        _focus_visible={
            "outline": f"2px solid {LINK_GREEN}",
            "outlineOffset": "2px",
        },
    )


def _pagination() -> rx.Component:
    """Só com mais de uma página: “Anterior”, “Página N de M” e “Próxima”."""
    return rx.cond(
        DonorProfileState.page_total > 1,
        rx.vstack(
            rx.hstack(
                _page_button(
                    "Anterior",
                    DonorProfileState.page - 1,
                    (DonorProfileState.page <= 1) | DonorProfileState.page_loading,
                ),
                rx.text(
                    "Página ",
                    DonorProfileState.page,
                    " de ",
                    DonorProfileState.page_total,
                    aria_live="polite",
                    color=TEXT_STRONG,
                    font_size="0.95rem",
                    white_space="nowrap",
                ),
                _page_button(
                    "Próxima",
                    DonorProfileState.page + 1,
                    (DonorProfileState.page >= DonorProfileState.page_total)
                    | DonorProfileState.page_loading,
                ),
                class_name="donor-profile-pagination",
                spacing="4",
                align="center",
                justify="center",
                wrap="wrap",
                width="100%",
            ),
            rx.cond(
                DonorProfileState.page_error != "",
                rx.text(
                    DonorProfileState.page_error,
                    role="alert",
                    color=TEXT_ERROR,
                    font_size="0.9rem",
                    text_align="center",
                    width="100%",
                ),
                rx.fragment(),
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        rx.fragment(),
    )


def _donations_list() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading(
                DONATIONS_TITLE,
                as_="h2",
                color=TITLE_GREEN,
                font_size="1.5rem",
                font_weight="700",
                class_name="page-fade-enter",
            ),
            rx.text(
                DonorProfileState.count_label,
                class_name="donor-profile-count",
                color=TEXT_MUTED,
                font_size="1rem",
            ),
            spacing="3",
            align="baseline",
            wrap="wrap",
        ),
        rx.box(
            rx.foreach(DonorProfileState.items, donation_grid_card),
            class_name="donor-profile-grid",
            style={
                "display": "grid",
                "gridTemplateColumns": CARDS_GRID_COLUMNS,
            },
            gap="24px",
            width="100%",
        ),
        _pagination(),
        align="stretch",
        spacing="5",
        width="100%",
    )


def _empty_state() -> rx.Component:
    return rx.vstack(
        rx.heading(
            EMPTY_TITLE,
            as_="h2",
            color=TITLE_GREEN,
            font_size="1.25rem",
            font_weight="700",
            text_align="center",
            class_name="page-fade-enter",
        ),
        rx.text(
            "Quando ",
            DonorProfileState.first_name,
            " publicar uma nova doação, ela aparece aqui.",
            color=TEXT_MUTED,
            text_align="center",
            overflow_wrap="anywhere",
        ),
        rx.link(
            EXPLORE_LINK_LABEL,
            href="/",
            color=LINK_GREEN,
            font_weight="700",
            display="inline-flex",
            align_items="center",
            min_height="44px",
            _hover={"color": LINK_GREEN_HOVER},
        ),
        class_name="donor-profile-empty",
        align="center",
        spacing="3",
        width="100%",
        max_width="560px",
        margin="0 auto",
        padding=rx.breakpoints(initial="32px 16px", md="48px 40px"),
        background=WHITE,
        border=f"1px solid {BORDER_SOFT}",
        border_radius="8px",
    )


def _profile_content() -> rx.Component:
    return rx.box(
        rx.vstack(
            _identity_card(),
            rx.cond(
                DonorProfileState.items.length() == 0,
                _empty_state(),
                _donations_list(),
            ),
            align="stretch",
            spacing="7",
            width="100%",
            max_width=CONTENT_MAX_WIDTH,
            margin="0 auto",
        ),
        width="100%",
        min_height="calc(100vh - 88px)",
        padding=rx.breakpoints(initial="24px 16px 48px", md="32px 24px 56px"),
        background=CREAM,
    )


def donor_profile_page() -> rx.Component:
    return rx.box(
        # “Voltar à doação” na linha do logotipo, em #007A42.
        back_link_header(DonorProfileState.back_href, BACK_TO_DONATION_LABEL, LINK_GREEN),
        rx.cond(
            DonorProfileState.view_state == "loading",
            _state_message(PROFILE_LOADING_MESSAGE, TEXT_MUTED),
            rx.cond(
                DonorProfileState.view_state == "not_found",
                _state_message(DONATION_NOT_FOUND_MESSAGE, TEXT_MUTED),
                rx.cond(
                    DonorProfileState.view_state == "error",
                    _state_message(DonorProfileState.error_message, TEXT_ERROR),
                    _profile_content(),
                ),
            ),
        ),
        display="flex",
        flex_direction="column",
        width="100%",
        min_height="100vh",
        background=CREAM,
        font_family="'LINE Seed JP', Arial, sans-serif",
    )
