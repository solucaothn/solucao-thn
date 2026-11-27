import json
import os
import re
from typing import Any
from urllib.parse import quote, urlsplit

import httpx
import reflex as rx

from doafacil.cabecalho import HEADER_MAX_WIDTH, HEADER_PADDING_X
from doafacil import cache_publico
from doafacil.rotas import login_redirect, path_segment_after
from doafacil.chat import (
    ChatError,
    ChatNotFoundError,
    ChatRateLimitError,
    ChatUnauthorizedError,
    avatar_initial,
    rate_limit_message,
    start_conversation,
)
from doafacil.login import LoginState
from doafacil.navegacao import back_home_header
from doafacil.perfil_publico import (
    ACTIVE_LABELS,
    COMPLETED_LABELS,
    COUNT_NUMBER_COLOR,
    avatar,
    parse_counts,
    parse_email_verified,
    parse_photo_url,
)


DONATION_DETAIL_PATH = "/catalog/donations/detail"
DONOR_CONTACT_EMAIL_PATH = "/catalog/donations/contact-email"
GENERIC_DETAIL_IMAGE = "/doacao-generica.svg"
DONATION_NOT_FOUND_MESSAGE = "Doação não encontrada"
DONATION_DETAIL_ERROR_MESSAGE = (
    "Não foi possível carregar os detalhes da doação. Tente novamente mais tarde."
)
DONOR_CONTACT_ERROR_MESSAGE = (
    "Não foi possível iniciar o contato. Tente novamente mais tarde."
)
DONOR_OWN_DONATION_MESSAGE = "Esta é a sua doação."
DONOR_CHAT_PREFERENCE_MESSAGE = "Quem doa prefere contato pelo chat."
# 404 do início de conversa: neutro, sem dizer o motivo (preferência por
# e-mail, doação da própria pessoa ou doação indisponível).
CHAT_NOT_AVAILABLE_FOR_DONATION_MESSAGE = (
    "Não é possível conversar sobre esta doação pelo chat."
)
CHAT_START_ERROR_MESSAGE = "Não foi possível abrir o chat. Tente novamente."


class DonationNotFoundError(Exception):
    pass


class DonorOwnDonationError(Exception):
    pass


def _positive_donation_id(value: object) -> int:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]+", value) is None:
        raise DonationNotFoundError

    try:
        donation_id = int(value)
    except ValueError as error:
        raise DonationNotFoundError from error
    if donation_id <= 0:
        raise DonationNotFoundError
    return donation_id


def _donation_detail_endpoint(base_url: str, donation_id: int) -> str:
    parsed_url = urlsplit(base_url.strip())
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("XANO_API_URL precisa conter uma URL HTTP(S) válida.")
    return f"{base_url.strip().rstrip('/')}{DONATION_DETAIL_PATH}?donation_id={donation_id}"


def _donor_contact_email_endpoint(base_url: str, donation_id: int) -> str:
    parsed_url = urlsplit(base_url.strip())
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("XANO_API_URL precisa conter uma URL HTTP(S) válida.")
    return (
        f"{base_url.strip().rstrip('/')}{DONOR_CONTACT_EMAIL_PATH}"
        f"?donation_id={donation_id}"
    )


def _mailto_url(email: str, title: str) -> str:
    recipient = quote(email, safe="@.-_")
    subject = quote(f"Sobre a doação: {title}", safe="")
    return f"mailto:{recipient}?subject={subject}"


def _parse_donation_detail(
    payload: object, expected_id: int
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("A resposta do detalhe precisa ser um objeto.")

    donation_id = payload.get("id")
    title = payload.get("title")
    condition = payload.get("condition")
    description = payload.get("description")
    category = payload.get("category")
    city = payload.get("city")
    state = payload.get("state")
    delivery_method = payload.get("delivery_method")
    contact_preference = payload.get("contact_preference")
    donor_first_name = payload.get("donor_first_name")
    photos = payload.get("photos")

    if (
        isinstance(donation_id, bool)
        or not isinstance(donation_id, int)
        or donation_id != expected_id
        or not isinstance(title, str)
        or not title.strip()
        or not isinstance(condition, str)
        or condition not in {"Ótimo", "Bom", "Regular"}
        or not isinstance(description, str)
        or not isinstance(category, str)
        or not category.strip()
        or not isinstance(city, str)
        or not isinstance(state, str)
        or not isinstance(delivery_method, str)
        or not delivery_method.strip()
        or not isinstance(contact_preference, str)
        or not contact_preference.strip()
        or not isinstance(donor_first_name, str)
        or not isinstance(photos, list)
        or any(not isinstance(photo, str) or not photo.strip() for photo in photos)
    ):
        raise ValueError("A resposta do detalhe contém dados inválidos.")

    # Foto de perfil de quem doa: URL pública ou nula (sem foto → "").
    donor_photo = parse_photo_url(payload.get("donor_photo"))
    # Contadores e selo de quem doa (change perfil-credibilidade).
    donor_email_verified = parse_email_verified(payload.get("donor_email_verified"))
    donor_active, donor_completed = parse_counts(payload.get("donor_counts"))

    unique_photos = list(dict.fromkeys(photos))
    if not unique_photos:
        unique_photos = [GENERIC_DETAIL_IMAGE]

    return {
        "id": donation_id,
        "title": title,
        "condition": condition,
        "description": description,
        "category": category,
        "city": city,
        "state": state,
        "delivery_method": delivery_method,
        "contact_preference": contact_preference,
        "donor_first_name": donor_first_name,
        "donor_photo": donor_photo,
        "donor_email_verified": donor_email_verified,
        "donor_active": donor_active,
        "donor_completed": donor_completed,
        "photos": unique_photos,
    }


async def _fetch_donation_detail(
    client: httpx.AsyncClient,
    base_url: str,
    donation_id_value: object,
) -> dict[str, Any]:
    donation_id = _positive_donation_id(donation_id_value)
    endpoint = _donation_detail_endpoint(base_url, donation_id)

    async def load() -> dict[str, Any]:
        response = await client.get(endpoint)
        if response.status_code == 404:
            raise DonationNotFoundError
        response.raise_for_status()
        return _parse_donation_detail(response.json(), donation_id)

    # Detalhe público, guardado por 60 s para todos (cache_publico).
    return await cache_publico.cached(cache_publico.DETAIL, endpoint, load)


async def _fetch_donor_member_since(
    client: httpx.AsyncClient,
    base_url: str,
    donation_id: int,
) -> str:
    """“outubro de 2020”, a partir do perfil público de quem doa (página 1,
    a mesma entrada do cache público de 60 s que a página do perfil usa).

    Qualquer falha do perfil devolve "": a linha “desde” some e o resto do
    cartão aparece. Navegação cancelada (CancelledError) não é capturada.
    """
    # Import tardio: perfil_doador importa deste módulo.
    from doafacil.perfil_doador import (
        DonorProfileNotFoundError,
        DonorProfileRateLimitError,
        DonorProfileServiceError,
        fetch_donor_profile,
        member_since_label,
    )

    try:
        profile = await fetch_donor_profile(client, base_url, donation_id)
        return member_since_label(profile["member_since"])
    except (
        DonorProfileNotFoundError,
        DonorProfileRateLimitError,
        DonorProfileServiceError,
        httpx.HTTPError,
        ValueError,
    ):
        return ""


async def _fetch_donor_email(
    client: httpx.AsyncClient,
    base_url: str,
    donation_id: int,
    auth_token: str,
) -> str:
    endpoint = _donor_contact_email_endpoint(base_url, donation_id)
    response = await client.get(
        endpoint,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    if response.status_code == 403:
        raise DonorOwnDonationError
    if response.status_code != 200:
        response.raise_for_status()
        raise ValueError("A resposta do endpoint de contato é inválida.")

    payload = response.json()
    if not isinstance(payload, dict) or set(payload) != {"email"}:
        raise ValueError("A resposta do endpoint de contato é inválida.")
    email = payload.get("email")
    if (
        not isinstance(email, str)
        or re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is None
    ):
        raise ValueError("A resposta do endpoint de contato é inválida.")
    return email


class DonationDetailState(LoginState):
    donation_id: int = 0
    title: str = ""
    condition: str = ""
    description: str = ""
    category: str = ""
    city: str = ""
    state: str = ""
    delivery_method: str = ""
    contact_preference: str = ""
    donor_first_name: str = ""
    donor_photo: str = ""
    donor_email_verified: bool = False
    donor_active: int = 0
    donor_completed: int = 0
    # “No DoaFácil desde …” (change quem-doa-completo): texto pronto, como
    # “outubro de 2020”, lido do perfil público; vazio esconde a linha.
    donor_member_since: str = ""
    photos: list[str] = []
    view_state: str = "loading"
    contact_message: str = ""
    contact_message_is_error: bool = False
    is_starting_chat: bool = False
    # Visualizador de fotos (modal).
    viewer_open: bool = False
    viewer_index: int = 0
    viewer_zoomed: bool = False
    # Aviso “Doação publicada!” (change fotos-formulario-doacao): o cadastro
    # informa o id antes de redirecionar; o load_donation mostra o aviso só
    # para essa doação e consome o id (recarregar não mostra de novo).
    published_notice_id: int = 0
    show_published_notice: bool = False

    @rx.event
    def set_published_notice(self, donation_id: int) -> None:
        self.published_notice_id = int(donation_id)

    @rx.var
    def donor_initial(self) -> str:
        return avatar_initial(self.donor_first_name)

    @rx.var
    def gallery_size(self) -> int:
        """Quantas fotos a galeria mostra (de 1 a 5): escolhe o arranjo."""
        return min(len(self.photos), MAX_GALLERY_PHOTOS)

    @rx.event
    def open_viewer(self, index: int) -> None:
        if not self.photos:
            return
        self.viewer_index = min(max(int(index), 0), len(self.photos) - 1)
        self.viewer_zoomed = False
        self.viewer_open = True

    @rx.event
    def close_viewer(self) -> None:
        self.viewer_open = False
        self.viewer_zoomed = False

    @rx.event
    def set_viewer_open(self, is_open: bool) -> None:
        # on_open_change do diálogo: Esc e clique fora chegam aqui com False.
        if not is_open:
            DonationDetailState.close_viewer.fn(self)

    @rx.event
    def next_photo(self) -> None:
        if len(self.photos) <= 1:
            return
        self.viewer_index = (self.viewer_index + 1) % len(self.photos)
        self.viewer_zoomed = False

    @rx.event
    def prev_photo(self) -> None:
        if len(self.photos) <= 1:
            return
        self.viewer_index = (self.viewer_index - 1) % len(self.photos)
        self.viewer_zoomed = False

    @rx.event
    def toggle_zoom(self) -> None:
        self.viewer_zoomed = not self.viewer_zoomed

    @rx.event
    def viewer_key_down(self, key: str) -> None:
        # Esc fica com o diálogo (fecha e devolve o foco).
        if key == "ArrowRight":
            DonationDetailState.next_photo.fn(self)
        elif key == "ArrowLeft":
            DonationDetailState.prev_photo.fn(self)

    @rx.event
    async def load_donation(self) -> rx.event.EventSpec | None:
        self.donation_id = 0
        self.title = ""
        self.condition = ""
        self.description = ""
        self.category = ""
        self.city = ""
        self.state = ""
        self.delivery_method = ""
        self.contact_preference = ""
        self.donor_first_name = ""
        self.donor_photo = ""
        self.donor_email_verified = False
        self.donor_active = 0
        self.donor_completed = 0
        self.donor_member_since = ""
        self.photos = []
        self.view_state = "loading"
        self.contact_message = ""
        self.contact_message_is_error = False
        self.is_starting_chat = False
        self.viewer_open = False
        self.viewer_index = 0
        self.viewer_zoomed = False
        donation_id = path_segment_after(self.router, "doacao")
        # O aviso de publicação vale uma vez, só para a doação recém-publicada.
        notice_id = self.published_notice_id
        self.published_notice_id = 0
        try:
            self.show_published_notice = notice_id > 0 and int(donation_id) == notice_id
        except (TypeError, ValueError):
            self.show_published_notice = False

        try:
            _positive_donation_id(donation_id)
            base_url = os.getenv("XANO_API_URL", "").strip()
            async with httpx.AsyncClient(timeout=15.0) as client:
                donation = await _fetch_donation_detail(
                    client,
                    base_url,
                    donation_id,
                )
        except DonationNotFoundError:
            self.view_state = "not_found"
        except (httpx.HTTPError, ValueError):
            self.view_state = "error"
        else:
            self.donation_id = donation["id"]
            self.title = donation["title"]
            self.condition = donation["condition"]
            self.description = donation["description"]
            self.category = donation["category"]
            self.city = donation["city"]
            self.state = donation["state"]
            self.delivery_method = donation["delivery_method"]
            self.contact_preference = donation["contact_preference"]
            self.donor_first_name = donation["donor_first_name"]
            self.donor_photo = donation["donor_photo"]
            self.donor_email_verified = donation["donor_email_verified"]
            self.donor_active = donation["donor_active"]
            self.donor_completed = donation["donor_completed"]
            self.photos = donation["photos"]
            self.view_state = "loaded"
            # O “desde” vem depois, sem atrasar o detalhe.
            return DonationDetailState.load_donor_since
        return None

    @rx.event
    def retry_donation(self):
        """“Tentar de novo” da falha (change correcoes-revisao): mostra
        “Carregando doação...” na hora e busca a doação outra vez, com o mesmo
        pedido do load_donation (como o retry_profile do perfil)."""
        self.view_state = "loading"
        return DonationDetailState.load_donation

    @rx.event
    async def load_donor_since(self) -> None:
        donation_id = self.donation_id
        if donation_id <= 0:
            return
        base_url = os.getenv("XANO_API_URL", "").strip()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                label = await _fetch_donor_member_since(
                    client, base_url, donation_id
                )
        except httpx.HTTPError:
            label = ""
        # Outra doação foi aberta enquanto o perfil respondia.
        if self.donation_id == donation_id:
            self.donor_member_since = label

    @rx.event
    async def request_donor_contact(self) -> rx.event.EventSpec | None:
        self.contact_message = ""
        self.contact_message_is_error = False
        if not self.auth_token:
            return login_redirect(self)
        if self.contact_preference == "Chat do DoaFácil":
            self.contact_message = DONOR_CHAT_PREFERENCE_MESSAGE
            return None
        if self.contact_preference != "E-mail":
            self.contact_message = DONOR_CONTACT_ERROR_MESSAGE
            self.contact_message_is_error = True
            return None

        try:
            donation_id = _positive_donation_id(str(self.donation_id))
            base_url = os.getenv("XANO_API_URL", "").strip()
            async with httpx.AsyncClient(timeout=15.0) as client:
                email = await _fetch_donor_email(
                    client,
                    base_url,
                    donation_id,
                    self.auth_token,
                )
        except DonorOwnDonationError:
            self.contact_message = DONOR_OWN_DONATION_MESSAGE
            return None
        except (httpx.HTTPError, ValueError):
            self.contact_message = DONOR_CONTACT_ERROR_MESSAGE
            self.contact_message_is_error = True
            return None

        mailto = _mailto_url(email, self.title)
        return rx.call_script(
            f"window.location.href = {json.dumps(mailto)};"
        )

    @rx.event
    async def start_chat(self):
        """Abre a conversa da doação (change chat-carregamento): o `yield` logo
        depois de ligar `is_starting_chat` manda o estado ao navegador, e o
        botão “Chat” mostra o carregamento enquanto o POST roda (sem ele, o
        Reflex só atualizava a tela no fim do evento)."""
        self.contact_message = ""
        self.contact_message_is_error = False
        if not self.auth_token:
            yield login_redirect(self)
            return
        if self.is_starting_chat:
            return

        self.is_starting_chat = True
        yield
        outcome = None
        try:
            donation_id = _positive_donation_id(str(self.donation_id))
            async with httpx.AsyncClient(timeout=15.0) as client:
                conversation = await start_conversation(
                    client, self.auth_token, donation_id
                )
        except ChatUnauthorizedError:
            self.auth_token = ""
            self.account_name = ""
            outcome = login_redirect(self)
        except ChatNotFoundError:
            self.contact_message = CHAT_NOT_AVAILABLE_FOR_DONATION_MESSAGE
        except ChatRateLimitError as error:
            self.contact_message = rate_limit_message(error.kind)
            self.contact_message_is_error = True
        except (ChatError, ValueError):
            self.contact_message = CHAT_START_ERROR_MESSAGE
            self.contact_message_is_error = True
        else:
            outcome = rx.redirect(f"/chat?conversa={conversation['conversation_id']}")
        finally:
            self.is_starting_chat = False
        if outcome is not None:
            yield outcome


# Layout da página, segundo os frames detalhes-doacao-inteira e
# detalhes-doacao-1 do Figma (veja docs/design/README.md, que prevalece).
# Todo dado vindo do Xano é renderizado com componentes de texto, sem HTML.

TEXT_STRONG = "#2A2A2A"
TEXT_LABEL = "#555555"
TEXT_DONOR = "#001C3C"
BORDER_SOFT = "#D9D9D9"
PRIMARY_GREEN = "#007A42"
PRIMARY_GREEN_HOVER = "#006B39"
CREAM = "#FFF6E8"
PHOTO_PLACEHOLDER = "#EEEEEE"
DONOR_AVATAR_BACKGROUND = "#F2F2F2"
DETAIL_ICON = "/detalhe-atributo.svg"
LOCATION_ICON = "/detalhe-localizacao.svg"
MAX_THUMBNAILS = 4
MAX_GALLERY_PHOTOS = MAX_THUMBNAILS + 1
GALLERY_HEIGHT_WIDE = "470px"
GALLERY_COVER_HEIGHT_NARROW = "300px"
GALLERY_RADIUS = "8px"
GALLERY_GAP_WIDE = "16px"
GALLERY_GAP_NARROW = "8px"
# Área da grade de cada foto, pela posição (a = capa).
GALLERY_AREAS = ["a", "b", "c", "d", "e"]
# Computador (change galeria-detalhe): colunas e áreas por quantidade de
# fotos, todas dentro dos 470 px. Com 5, a capa fica com metade da largura.
GALLERY_WIDE_LAYOUTS = {
    1: ("minmax(0, 1fr)", "'a'"),
    2: ("minmax(0, 1fr) minmax(0, 1fr)", "'a b'"),
    3: ("minmax(0, 2fr) minmax(0, 1fr)", "'a b' 'a c'"),
    4: ("minmax(0, 1fr) minmax(0, 1fr)", "'a b' 'c d'"),
    5: ("repeat(4, minmax(0, 1fr))", "'a a b c' 'a a d e'"),
}
# Celular: capa em cima e uma fileira de 4 posições para as miniaturas.
GALLERY_NARROW_COLUMNS = "repeat(4, minmax(0, 1fr))"
GALLERY_NARROW_AREAS_SINGLE = "'a a a a'"
GALLERY_NARROW_AREAS = "'a a a a' 'b c d e'"


VIEWER_BACKDROP = "rgba(255, 246, 232, 0.85)"
VIEWER_BLUR = "blur(6px)"
# #1F1F1F sobre o creme (mesmo a 85%) passa de 15:1, acima do AA.
VIEWER_TEXT = "#1F1F1F"
VIEWER_CONTROL_BACKGROUND = "#FFFFFF"
VIEWER_CONTROL_HOVER = "#F2F2F2"
VIEWER_CONTROL_SHADOW = "0 2px 8px rgba(0, 0, 0, 0.18)"
VIEWER_CONTROL_SIZE = "48px"
# Margem dos botões e da foto até a borda da tela, em qualquer largura.
VIEWER_EDGE = "16px"
# Cabeçalho do modal: 16 px + botão de 48 px + 16 px.
VIEWER_HEADER_HEIGHT = "80px"
# Foto em 1x: cabe na altura que sobra abaixo do cabeçalho, com 16 px embaixo.
VIEWER_IMAGE_MAX_HEIGHT = "calc(100dvh - 80px - 16px)"
# Largura: 16 px de cada lado no celular (as setas ficam sobre a foto); no
# computador, espaço das setas (16 + 48 + 16) dos dois lados.
VIEWER_IMAGE_MAX_WIDTH_MOBILE = "calc(100vw - 32px)"
VIEWER_IMAGE_MAX_WIDTH_DESKTOP = "calc(100vw - 160px)"
# 2x: o dobro dessas larguras, com rolagem para mover a foto.
VIEWER_IMAGE_ZOOM_WIDTH_MOBILE = "calc(200vw - 64px)"
VIEWER_IMAGE_ZOOM_WIDTH_DESKTOP = "calc(200vw - 320px)"
# O Radix pinta um véu escuro (::before do overlay) atrás de todo diálogo;
# só no visualizador ele fica transparente, para valer o creme com desfoque.
VIEWER_OVERLAY_CSS = (
    ".rt-BaseDialogOverlay:has(.detail-viewer)::before"
    "{background-color:transparent}"
)


def _photo_open_button(
    child: rx.Component, index: rx.Var | int, label: rx.Var | str
) -> rx.Component:
    """Botão sem estilo próprio em volta da foto: clique, Enter ou Espaço
    abrem o visualizador nessa foto."""
    return rx.el.button(
        child,
        type="button",
        on_click=DonationDetailState.open_viewer(index),
        aria_label=label,
        class_name="detail-photo-button",
        display="block",
        width="100%",
        height="100%",
        padding="0",
        border="none",
        background="transparent",
        border_radius="8px",
        cursor="zoom-in",
    )


def _photo_label(position: rx.Var | int) -> rx.Var:
    return (
        rx.Var.create("Ampliar foto ")
        + rx.Var.create(position).to_string()
        + " de "
        + DonationDetailState.photos.length().to_string()
    )


def _viewer_control(
    icon: str, label: str, on_click: rx.EventHandler, **props: Any
) -> rx.Component:
    """Botão branco com sombra leve e ícone escuro, com área de toque de 48 px."""
    return rx.el.button(
        rx.icon(icon, size=28, aria_hidden="true"),
        type="button",
        # stop_propagation: o clique no botão não chega ao fundo (que fecha).
        on_click=on_click.stop_propagation,
        aria_label=label,
        title=label,
        class_name="detail-viewer-control",
        display="inline-flex",
        align_items="center",
        justify_content="center",
        flex_shrink="0",
        width=VIEWER_CONTROL_SIZE,
        height=VIEWER_CONTROL_SIZE,
        min_width=VIEWER_CONTROL_SIZE,
        min_height=VIEWER_CONTROL_SIZE,
        padding="0",
        color=VIEWER_TEXT,
        background=VIEWER_CONTROL_BACKGROUND,
        box_shadow=VIEWER_CONTROL_SHADOW,
        border="none",
        border_radius="999px",
        cursor="pointer",
        _hover={"background": VIEWER_CONTROL_HOVER},
        _focus_visible={
            "outline": f"2px solid {VIEWER_TEXT}",
            "outlineOffset": "2px",
        },
        **props,
    )


def _photo_viewer() -> rx.Component:
    """Visualizador modal: foto inteira, ‹ ›, setas, “N de M”, zoom 1x/2x e
    fechar por X, Esc ou clique fora. O rx.dialog (Radix) prende o foco,
    fecha com Esc e devolve o foco ao fechar.

    Fundo creme semitransparente com desfoque; textos e ícones escuros. O
    conteúdo ocupa a tela com position fixed + inset 0, então o X e as setas
    ficam sempre a 16 px das bordas visíveis, em qualquer largura."""
    zoomed = DonationDetailState.viewer_zoomed
    has_many = DonationDetailState.photos.length() > 1
    return rx.dialog.root(
        rx.dialog.content(
            rx.el.style(VIEWER_OVERLAY_CSS),
            # ← e →: ouvinte da janela, que só existe com o modal aberto (o
            # Radix desmonta o conteúdo fechado), então nenhuma tecla vai ao
            # servidor fora do visualizador. Esc fica com o próprio diálogo.
            rx.window_event_listener(
                on_key_down=DonationDetailState.viewer_key_down,
            ),
            # Fundo: clicar nele (fora da foto e dos botões) fecha.
            rx.box(
                # Cabeçalho de altura fixa: contador, dica e o X.
                rx.hstack(
                    rx.box(
                        rx.dialog.title(
                            DonationDetailState.viewer_index + 1,
                            " de ",
                            DonationDetailState.photos.length(),
                            class_name="detail-viewer-counter",
                            color=VIEWER_TEXT,
                            font_size="1rem",
                            font_weight="600",
                            line_height="1.4",
                            margin="0",
                        ),
                        rx.dialog.description(
                            "Use as setas para trocar de foto. Clique na foto "
                            "para ampliar ou reduzir.",
                            color=VIEWER_TEXT,
                            font_size="0.8rem",
                            line_height="1.3",
                            margin="0",
                            display=rx.breakpoints(initial="none", md="block"),
                        ),
                        on_click=rx.stop_propagation,
                        min_width="0",
                    ),
                    rx.spacer(),
                    _viewer_control("x", "Fechar", DonationDetailState.close_viewer),
                    class_name="detail-viewer-header",
                    align="center",
                    width="100%",
                    height=VIEWER_HEADER_HEIGHT,
                    padding=f"0 {VIEWER_EDGE}",
                    box_sizing="border-box",
                    flex_shrink="0",
                ),
                rx.box(
                    # Área da foto: em 2x, a rolagem move a imagem; no
                    # celular vale a pinça do navegador (touch-action).
                    rx.el.button(
                        rx.image(
                            src=DonationDetailState.photos[
                                DonationDetailState.viewer_index
                            ],
                            alt=DonationDetailState.title,
                            class_name="detail-viewer-image",
                            object_fit="contain",
                            display="block",
                            margin="auto",
                            # 1x: a foto inteira cabe abaixo do cabeçalho.
                            max_width=rx.cond(
                                zoomed,
                                "none",
                                rx.breakpoints(
                                    initial=VIEWER_IMAGE_MAX_WIDTH_MOBILE,
                                    md=VIEWER_IMAGE_MAX_WIDTH_DESKTOP,
                                ),
                            ),
                            max_height=rx.cond(zoomed, "none", VIEWER_IMAGE_MAX_HEIGHT),
                            # 2x: o dobro da largura disponível, com rolagem.
                            width=rx.cond(
                                zoomed,
                                rx.breakpoints(
                                    initial=VIEWER_IMAGE_ZOOM_WIDTH_MOBILE,
                                    md=VIEWER_IMAGE_ZOOM_WIDTH_DESKTOP,
                                ),
                                "auto",
                            ),
                            height="auto",
                        ),
                        type="button",
                        on_click=DonationDetailState.toggle_zoom.stop_propagation,
                        aria_label=rx.cond(zoomed, "Reduzir foto", "Ampliar foto"),
                        class_name="detail-viewer-zoom",
                        display="block",
                        margin="auto",
                        padding="0",
                        border="none",
                        background="transparent",
                        min_width=VIEWER_CONTROL_SIZE,
                        min_height=VIEWER_CONTROL_SIZE,
                        cursor=rx.cond(zoomed, "zoom-out", "zoom-in"),
                    ),
                    class_name="detail-viewer-stage",
                    display="flex",
                    align_items=rx.cond(zoomed, "flex-start", "center"),
                    justify_content=rx.cond(zoomed, "flex-start", "center"),
                    overflow="auto",
                    flex="1",
                    width="100%",
                    min_height="0",
                    box_sizing="border-box",
                    padding=rx.breakpoints(
                        initial=f"0 {VIEWER_EDGE} {VIEWER_EDGE}",
                        md=f"0 80px {VIEWER_EDGE}",
                    ),
                    style={"touchAction": "pan-x pan-y pinch-zoom"},
                ),
                rx.cond(
                    has_many,
                    rx.fragment(
                        # Centro vertical da área da foto (abaixo dos 80 px do
                        # cabeçalho), a 16 px das bordas laterais.
                        _viewer_control(
                            "chevron-left",
                            "Foto anterior",
                            DonationDetailState.prev_photo,
                            position="absolute",
                            left=VIEWER_EDGE,
                            top="calc(50% + 40px)",
                            transform="translateY(-50%)",
                            z_index="1",
                        ),
                        _viewer_control(
                            "chevron-right",
                            "Próxima foto",
                            DonationDetailState.next_photo,
                            position="absolute",
                            right=VIEWER_EDGE,
                            top="calc(50% + 40px)",
                            transform="translateY(-50%)",
                            z_index="1",
                        ),
                    ),
                    rx.fragment(),
                ),
                on_click=DonationDetailState.close_viewer,
                class_name="detail-viewer-backdrop",
                position="relative",
                display="flex",
                flex_direction="column",
                width="100%",
                height="100%",
                overflow="hidden",
            ),
            class_name="detail-viewer",
            # Tela cheia presa às bordas visíveis, sem o cartão do Radix.
            position="fixed",
            inset="0",
            top="0",
            left="0",
            # 100% do viewport sem a barra de rolagem: nada passa da borda.
            width="100%",
            height="100%",
            max_width="none",
            max_height="none",
            padding="0",
            margin="0",
            border_radius="0",
            overflow="hidden",
            box_sizing="border-box",
            color=VIEWER_TEXT,
            background=VIEWER_BACKDROP,
            box_shadow="none",
            style={
                "backdropFilter": VIEWER_BLUR,
                "WebkitBackdropFilter": VIEWER_BLUR,
            },
        ),
        open=DonationDetailState.viewer_open,
        on_open_change=DonationDetailState.set_viewer_open,
    )


def _gallery_photo(photo: rx.Var[str], index: rx.Var[int]) -> rx.Component:
    """Uma foto da galeria, em qualquer posição: botão que abre o visualizador
    nela, com a área da grade (a…e) dada pela posição."""
    is_cover = index == 0
    return rx.box(
        _photo_open_button(
            rx.image(
                src=photo,
                alt=rx.cond(is_cover, DonationDetailState.title, "Foto da doação"),
                display="block",
                width="100%",
                height="100%",
                min_height="0",
                # Uma foto só: inteira (contain), com fundo neutro nas sobras.
                object_fit=rx.cond(
                    DonationDetailState.gallery_size > 1, "cover", "contain"
                ),
                object_position="center",
                border_radius=GALLERY_RADIUS,
                background=PHOTO_PLACEHOLDER,
            ),
            index,
            _photo_label(index + 1),
        ),
        class_name="detail-gallery-photo",
        grid_area=rx.Var.create(GALLERY_AREAS)[index],
        min_width="0",
        min_height="0",
        # No celular, as miniaturas são quadradas; a capa segue a linha de 300 px.
        aspect_ratio=rx.breakpoints(
            initial=rx.cond(is_cover, "auto", "1 / 1"), md="auto"
        ),
    )


def _wide_layout(part: int) -> rx.Var:
    """Colunas (part=0) ou áreas (part=1) do computador para a quantidade."""
    return rx.match(
        DonationDetailState.gallery_size,
        *[
            (size, layout[part])
            for size, layout in GALLERY_WIDE_LAYOUTS.items()
            if size != MAX_GALLERY_PHOTOS
        ],
        GALLERY_WIDE_LAYOUTS[MAX_GALLERY_PHOTOS][part],
    )


def _gallery() -> rx.Component:
    """Galeria que se adapta à quantidade de fotos (change galeria-detalhe).

    Uma grade só, com todas as fotos (até 5) como filhas diretas: o espaço e
    os cantos são iguais entre todas. No computador, o arranjo depende da
    quantidade (1 grande; 2 lado a lado; 3 com a capa em 2/3 e duas
    empilhadas; 2x2; capa + 2x2). No celular, a capa vem em cima e as demais
    numa fileira de miniaturas quadradas. Com 2 a 5 fotos, todas usam
    ``object-fit: cover``; a foto única aparece inteira (``contain``).
    """
    has_thumbnails = DonationDetailState.gallery_size > 1
    return rx.box(
        rx.foreach(
            DonationDetailState.photos[0:MAX_GALLERY_PHOTOS],
            _gallery_photo,
        ),
        class_name="detail-gallery",
        style={
            "display": "grid",
            "gridTemplateColumns": rx.breakpoints(
                initial=GALLERY_NARROW_COLUMNS, md=_wide_layout(0)
            ),
            "gridTemplateAreas": rx.breakpoints(
                initial=rx.cond(
                    has_thumbnails,
                    GALLERY_NARROW_AREAS,
                    GALLERY_NARROW_AREAS_SINGLE,
                ),
                md=_wide_layout(1),
            ),
            "gridTemplateRows": rx.breakpoints(
                initial=rx.cond(
                    has_thumbnails,
                    f"{GALLERY_COVER_HEIGHT_NARROW} auto",
                    GALLERY_COVER_HEIGHT_NARROW,
                ),
                md=rx.cond(
                    DonationDetailState.gallery_size > 2,
                    "minmax(0, 1fr) minmax(0, 1fr)",
                    "minmax(0, 1fr)",
                ),
            ),
        },
        gap=rx.breakpoints(initial=GALLERY_GAP_NARROW, md=GALLERY_GAP_WIDE),
        width="100%",
        height=rx.breakpoints(initial="auto", md=GALLERY_HEIGHT_WIDE),
    )


def _summary_card() -> rx.Component:
    """Cartão de resumo à direita: título, condição e contato (Figma)."""
    return rx.vstack(
        rx.heading(
            DonationDetailState.title,
            as_="h1",
            font_size=rx.breakpoints(initial="1.8rem", md="2.4rem"),
            font_weight="500",
            color=TEXT_STRONG,
            line_height="1.2",
            overflow_wrap="anywhere",
        ),
        rx.text(
            "Condição: ",
            DonationDetailState.condition,
            color=TEXT_STRONG,
            font_size="0.95rem",
        ),
        rx.vstack(
            rx.button(
                "Outros meios de comunicação",
                on_click=DonationDetailState.request_donor_contact,
                class_name="detail-primary-button",
                width="100%",
                min_height="56px",
                background=PRIMARY_GREEN,
                color="white",
                font_weight="700",
                font_size="1rem",
                border_radius="999px",
                white_space="normal",
                _hover={"background": PRIMARY_GREEN_HOVER},
            ),
            rx.button(
                rx.hstack(
                    rx.icon("message-circle", size=20),
                    rx.text("Chat"),
                    spacing="2",
                    align="center",
                ),
                on_click=DonationDetailState.start_chat,
                disabled=DonationDetailState.is_starting_chat,
                loading=DonationDetailState.is_starting_chat,
                width="100%",
                min_height="52px",
                background="white",
                color=TEXT_STRONG,
                font_weight="500",
                font_size="1rem",
                border="1px solid #85858D",
                border_radius="999px",
                _hover={"background": "#F7F8F7"},
            ),
            rx.cond(
                DonationDetailState.contact_message != "",
                rx.text(
                    DonationDetailState.contact_message,
                    role="status",
                    color=rx.cond(
                        DonationDetailState.contact_message_is_error,
                        "#9B2C2C",
                        "#166B3B",
                    ),
                    font_size="0.9rem",
                    width="100%",
                ),
                rx.fragment(),
            ),
            align="stretch",
            spacing="4",
            width="100%",
            padding_top="24px",
        ),
        class_name="detail-summary-card",
        align="stretch",
        spacing="2",
        width="100%",
        padding="40px 20px 32px",
        background="white",
        border=f"1px solid {BORDER_SOFT}",
        border_radius="8px",
        box_shadow="0 8px 13px rgba(0, 0, 0, 0.15)",
    )


def _title_and_description() -> rx.Component:
    """Título (caixa alta só no visual) e descrição logo abaixo da galeria."""
    return rx.vstack(
        rx.heading(
            DonationDetailState.title,
            as_="h2",
            class_name="detail-title",
            font_size="1.5rem",
            font_weight="700",
            color="#000000",
            text_transform="uppercase",
            line_height="1.25",
            overflow_wrap="anywhere",
        ),
        rx.text(
            DonationDetailState.description,
            class_name="detail-description",
            color="#222222",
            font_size=rx.breakpoints(initial="1rem", md="1.1rem"),
            line_height="1.5",
            white_space="pre-wrap",
            overflow_wrap="anywhere",
        ),
        align="stretch",
        spacing="3",
        width="100%",
    )


def _decorative_icon(src: str, size: str) -> rx.Component:
    return rx.image(
        src=src,
        alt="",
        width=size,
        height=size,
        min_width=size,
        aria_hidden="true",
    )


def _detail_item(label: str, value: rx.Var) -> rx.Component:
    """Ícone verde, rótulo pequeno e o valor logo abaixo (Figma)."""
    return rx.hstack(
        _decorative_icon(DETAIL_ICON, "18px"),
        rx.vstack(
            rx.text(
                label,
                class_name="detail-item-label",
                color=TEXT_LABEL,
                font_size="0.75rem",
                line_height="1.2",
            ),
            rx.text(
                value,
                class_name="detail-item-value",
                color=TEXT_STRONG,
                font_size="0.95rem",
                font_weight="600",
                line_height="1.3",
                overflow_wrap="anywhere",
            ),
            spacing="1",
            align="start",
            min_width="0",
        ),
        class_name="detail-item",
        spacing="3",
        align="start",
        min_width="0",
    )


def _details_section() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Detalhes",
            as_="h2",
            font_size="1.5rem",
            font_weight="500",
            color=TEXT_STRONG,
            class_name="page-fade-enter",
        ),
        rx.box(
            _detail_item("Categoria", DonationDetailState.category),
            _detail_item("Condição", DonationDetailState.condition),
            _detail_item("Forma de entrega", DonationDetailState.delivery_method),
            _detail_item(
                "Preferência de contato", DonationDetailState.contact_preference
            ),
            class_name="detail-grid",
            style={
                "display": "grid",
                "gridTemplateColumns": rx.breakpoints(
                    initial="minmax(0, 1fr)",
                    sm="repeat(2, minmax(0, 1fr))",
                    lg="repeat(4, minmax(0, 1fr))",
                ),
            },
            column_gap="24px",
            row_gap="24px",
            width="100%",
        ),
        align="stretch",
        spacing="3",
        width="100%",
    )


def _location_card() -> rx.Component:
    """Só “Cidade, UF”: bairro, zona e CEP não aparecem (privacidade)."""
    return rx.vstack(
        rx.heading(
            "Localização",
            as_="h2",
            font_size="1.5rem",
            font_weight="500",
            color=TEXT_STRONG,
            class_name="page-fade-enter",
        ),
        rx.hstack(
            _decorative_icon(LOCATION_ICON, "56px"),
            rx.text(
                DonationDetailState.city,
                ", ",
                DonationDetailState.state,
                class_name="detail-location-text",
                color=TEXT_STRONG,
                font_size="1rem",
                font_weight="600",
            ),
            class_name="detail-location-card",
            spacing="5",
            align="center",
            width="100%",
            padding="20px",
            background="white",
            border=f"1px solid {BORDER_SOFT}",
            border_radius="8px",
        ),
        align="stretch",
        spacing="3",
        width="100%",
    )


DONOR_PROFILE_BUTTON_LABEL = "Ver perfil de quem doa"
DONOR_SINCE_PREFIX = "No DoaFácil desde "
DONOR_DONATIONS_TITLE = "Doações"
DONOR_VERIFIED_TITLE = "Informações verificadas"
DONOR_VERIFIED_EMAIL_LABEL = "E-mail"
DONOR_BUTTON_HOVER_BACKGROUND = "#E8F5EC"


def _donor_card() -> rx.Component:
    """Cartão de quem doa em seções (change quem-doa-completo).

    Topo com foto, primeiro nome, “No DoaFácil desde …” e “Cidade, UF”; o
    botão “Ver perfil de quem doa”; “Doações” (os contadores, com os rótulos
    do perfil público e de Minhas doações); e
    “Informações verificadas” só com o e-mail verificado. Nunca o e-mail.

    O cartão não é link: o link é o botão, para /doacao/<id>/quem-doa. O
    frontend só usa o id da doação, nunca o id de quem doa.
    """
    return rx.box(
        _donor_card_content(),
        class_name="detail-donor-card",
        width="100%",
        padding="32px 28px",
        background="white",
        border=f"1px solid {BORDER_SOFT}",
        border_radius="8px",
        color=TEXT_DONOR,
    )


def _donor_divider() -> rx.Component:
    """Linha de 1 px entre as seções (decorativa)."""
    return rx.box(
        class_name="detail-donor-divider",
        role="presentation",
        width="100%",
        height="0",
        border_top=f"1px solid {BORDER_SOFT}",
    )


def _donor_section_title(text: str) -> rx.Component:
    return rx.heading(
        text,
        as_="h3",
        font_size="1rem",
        font_weight="600",
        color=TEXT_DONOR,
    )


def _donor_info_line(icon: str, *children: Any) -> rx.Component:
    """Ícone decorativo e texto, como “No DoaFácil desde …” e “Cidade, UF”."""
    return rx.hstack(
        rx.icon(icon, size=18, color=TEXT_DONOR, aria_hidden="true", flex_shrink="0"),
        rx.text(*children, color=TEXT_DONOR, font_size="0.9rem"),
        spacing="2",
        align="center",
    )


def _donor_stat(icon: str, value: rx.Var, labels: tuple[str, str]) -> rx.Component:
    """Um número com ícone (decorativo) e o rótulo abaixo, no singular com 1,
    como no perfil público e em Minhas doações."""
    singular, plural = labels
    return rx.hstack(
        rx.icon(icon, size=22, color=TEXT_DONOR, aria_hidden="true", flex_shrink="0"),
        rx.vstack(
            rx.text(
                value,
                color=COUNT_NUMBER_COLOR,
                font_size="1.3rem",
                font_weight="700",
                line_height="1.1",
            ),
            rx.text(
                rx.cond(value == 1, singular, plural),
                color=TEXT_LABEL,
                font_size="0.85rem",
                line_height="1.2",
            ),
            spacing="0",
            align="start",
        ),
        class_name="detail-donor-stat",
        spacing="2",
        align="center",
        flex="1",
        min_width="0",
    )


def _donor_profile_button() -> rx.Component:
    """Botão contornado, na largura toda, que leva ao perfil público."""
    return rx.link(
        DONOR_PROFILE_BUTTON_LABEL,
        href=f"/doacao/{DonationDetailState.donation_id}/quem-doa",
        # Começa pelo texto visível (WCAG 2.5.3) e diz de quem é o perfil.
        aria_label=(
            rx.Var.create(f"{DONOR_PROFILE_BUTTON_LABEL}, ")
            + DonationDetailState.donor_first_name
        ),
        class_name="detail-donor-profile-button",
        display="flex",
        align_items="center",
        justify_content="center",
        width="100%",
        min_height="44px",
        padding="10px 16px",
        box_sizing="border-box",
        color=PRIMARY_GREEN,
        font_weight="700",
        text_align="center",
        text_decoration="none",
        background="white",
        border=f"1px solid {PRIMARY_GREEN}",
        border_radius="8px",
        _hover={
            "background": DONOR_BUTTON_HOVER_BACKGROUND,
            "color": PRIMARY_GREEN_HOVER,
            "textDecoration": "none",
        },
        _focus_visible={
            "outline": f"2px solid {PRIMARY_GREEN}",
            "outlineOffset": "2px",
        },
    )


def _donor_card_content() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Quem doa",
            as_="h2",
            font_size="1.1rem",
            font_weight="500",
            color=TEXT_DONOR,
            class_name="page-fade-enter",
        ),
        # Topo: foto (ou inicial) de 48 px, nome, “desde” e cidade.
        rx.hstack(
            avatar(
                DonationDetailState.donor_photo,
                DonationDetailState.donor_initial,
                DonationDetailState.donor_first_name,
                "48px",
                background=DONOR_AVATAR_BACKGROUND,
                color=TEXT_LABEL,
                font_size="1.3rem",
            ),
            rx.vstack(
                rx.text(
                    DonationDetailState.donor_first_name,
                    color=TEXT_DONOR,
                    font_size="1.2rem",
                    font_weight="600",
                    overflow_wrap="anywhere",
                ),
                # Só com a data lida do perfil público; sem ela, a linha some.
                rx.cond(
                    DonationDetailState.donor_member_since != "",
                    _donor_info_line(
                        "calendar",
                        DONOR_SINCE_PREFIX,
                        DonationDetailState.donor_member_since,
                    ),
                    rx.fragment(),
                ),
                _donor_info_line(
                    "map-pin",
                    DonationDetailState.city,
                    ", ",
                    DonationDetailState.state,
                ),
                spacing="1",
                align="start",
                min_width="0",
            ),
            spacing="3",
            align="start",
        ),
        _donor_profile_button(),
        _donor_divider(),
        _donor_section_title(DONOR_DONATIONS_TITLE),
        rx.hstack(
            # Ativas (disponíveis e reservadas) e concluídas.
            _donor_stat("package", DonationDetailState.donor_active, ACTIVE_LABELS),
            _donor_stat(
                "package-check",
                DonationDetailState.donor_completed,
                COMPLETED_LABELS,
            ),
            spacing="4",
            width="100%",
            wrap="wrap",
        ),
        # Sem e-mail verificado, a seção e o divisor não aparecem.
        rx.cond(
            DonationDetailState.donor_email_verified,
            rx.fragment(
                _donor_divider(),
                _donor_section_title(DONOR_VERIFIED_TITLE),
                rx.hstack(
                    rx.icon(
                        "circle-check",
                        size=18,
                        color=COUNT_NUMBER_COLOR,
                        aria_hidden="true",
                        flex_shrink="0",
                    ),
                    rx.text(
                        DONOR_VERIFIED_EMAIL_LABEL,
                        color=TEXT_DONOR,
                        font_size="0.9rem",
                    ),
                    class_name="detail-donor-verified-email",
                    spacing="2",
                    align="center",
                ),
            ),
            rx.fragment(),
        ),
        align="stretch",
        spacing="4",
        width="100%",
    )


PUBLISHED_NOTICE_TEXT = "Doação publicada!"
PUBLISHED_NOTICE_LINK = "Minhas doações"
TITLE_GREEN_NOTICE = "#166B3B"
NOTICE_GREEN_BACKGROUND = "#E8F5EC"


def _published_notice() -> rx.Component:
    """Aviso depois de publicar pelo cadastro: “Doação publicada!” e o link
    “Minhas doações”. Fica até sair da página, sem botão de fechar. Sem o
    aviso, não ocupa espaço."""
    notice = rx.flex(
        rx.text(
            PUBLISHED_NOTICE_TEXT,
            color=TITLE_GREEN_NOTICE,
            font_weight="700",
        ),
        rx.link(
            PUBLISHED_NOTICE_LINK,
            href="/minhas-doacoes",
            display="inline-flex",
            align_items="center",
            min_height="44px",
            color=PRIMARY_GREEN,
            font_weight="700",
            text_decoration="underline",
            _focus_visible={
                "outline": f"2px solid {PRIMARY_GREEN}",
                "outlineOffset": "2px",
            },
        ),
        role="status",
        class_name="detail-published-notice",
        align="center",
        justify="between",
        wrap="wrap",
        column_gap="16px",
        width="100%",
        max_width=HEADER_MAX_WIDTH,
        margin="0 auto",
        padding="4px 16px",
        box_sizing="border-box",
        background=NOTICE_GREEN_BACKGROUND,
        border_radius="8px",
    )
    return rx.cond(
        DonationDetailState.show_published_notice,
        rx.box(
            notice,
            padding=rx.breakpoints(initial="16px 16px 0", md="20px 24px 0"),
            width="100%",
        ),
        rx.fragment(),
    )


# Ritmo vertical da página: entre seções (coluna esquerda e celular) e entre
# os cartões da coluna direita.
DETAIL_SECTION_GAP = "32px"
DETAIL_CARD_GAP = "24px"


def _donation_content() -> rx.Component:
    """Duas colunas no computador (como no Figma) e uma no celular.

    Ordem no celular: galeria, resumo, título e descrição, detalhes,
    localização e quem doa. As áreas da grade fazem a troca de posição.
    """
    return rx.box(
        _published_notice(),
        rx.box(
            # Cada coluna é uma pilha própria no computador, para a altura de
            # uma não abrir vãos na outra. No celular a coluna vira
            # "display: contents" e os filhos entram direto na grade de uma
            # coluna, na mesma ordem de antes.
            rx.box(
                rx.box(_gallery(), grid_area="gallery", min_width="0"),
                rx.box(_title_and_description(), grid_area="title", min_width="0"),
                rx.box(_details_section(), grid_area="details", min_width="0"),
                rx.box(_location_card(), grid_area="location", min_width="0"),
                class_name="detail-column-main",
                grid_area="main",
                display=rx.breakpoints(initial="contents", md="flex"),
                flex_direction="column",
                gap=DETAIL_SECTION_GAP,
                min_width="0",
            ),
            rx.box(
                rx.box(_summary_card(), grid_area="summary", min_width="0"),
                rx.box(_donor_card(), grid_area="donor", min_width="0"),
                class_name="detail-column-side",
                grid_area="side",
                display=rx.breakpoints(initial="contents", md="flex"),
                flex_direction="column",
                gap=DETAIL_CARD_GAP,
                min_width="0",
            ),
            # Visualizador modal (fora do fluxo da grade).
            _photo_viewer(),
            class_name="detail-layout",
            style={
                "display": "grid",
                "gridTemplateColumns": rx.breakpoints(
                    initial="minmax(0, 1fr)",
                    md="minmax(0, 2.6fr) minmax(280px, 1fr)",
                ),
                # Aspas simples: o CSS aceita, e o Reflex não escapa as
                # duplas dentro do valor (geraria JavaScript inválido).
                "gridTemplateAreas": rx.breakpoints(
                    initial=(
                        "'gallery' 'summary' 'title' 'details' 'location' 'donor'"
                    ),
                    md="'main side'",
                ),
                "alignItems": "start",
            },
            column_gap="24px",
            row_gap=DETAIL_SECTION_GAP,
            width="100%",
            # Mesmo contêiner de Minhas doações (change acabamento); a grade
            # (áreas e colunas) não muda.
            max_width=HEADER_MAX_WIDTH,
            margin="0 auto",
            padding_x=HEADER_PADDING_X,
            padding_top=rx.breakpoints(initial="24px", md="28px"),
            padding_bottom=rx.breakpoints(initial="48px", md="56px"),
            box_sizing="border-box",
        ),
        width="100%",
        min_height="calc(100vh - 88px)",
        background=CREAM,
    )


DONATION_UNAVAILABLE_TEXT = "Ela pode ter sido reservada, concluída ou removida por quem doou."


def _state_link(label: str, href: str, class_name: str, solid: bool) -> rx.Component:
    """Link de 44 px para os estados do detalhe: verde cheio ou contorno."""
    colors = (
        {"background": PRIMARY_GREEN, "color": "white", "_hover": {"background": "#006B39", "color": "white"}}
        if solid
        else {"background": "white", "color": PRIMARY_GREEN, "border": f"1px solid {PRIMARY_GREEN}", "_hover": {"background": "#F2F7F3", "color": PRIMARY_GREEN}}
    )
    return rx.link(
        label,
        href=href,
        class_name=class_name,
        display="inline-flex",
        align_items="center",
        justify_content="center",
        min_height="44px",
        padding="0 20px",
        border_radius="8px",
        font_weight="700",
        underline="none",
        _focus_visible={"outline": f"2px solid {PRIMARY_GREEN}", "outlineOffset": "2px"},
        **colors,
    )


def _detail_state_message(message: str, color: str, *actions: rx.Component) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(message, color=color, text_align="center"),
            *actions,
            align="center",
            spacing="3",
        ),
        display="flex",
        align_items="center",
        justify_content="center",
        width="100%",
        min_height="calc(100vh - 88px)",
        padding="24px",
        background=CREAM,
        class_name="page-fade-enter",
    )


def donation_detail_page() -> rx.Component:
    return rx.box(
        # “Voltar ao início” na linha do logotipo, igual ao chat e ao Figma.
        back_home_header(),
        rx.cond(
            DonationDetailState.view_state == "loading",
            _detail_state_message("Carregando doação...", "#555555"),
            rx.cond(
                DonationDetailState.view_state == "not_found",
                _detail_state_message(
                    DONATION_NOT_FOUND_MESSAGE,
                    "#555555",
                    # Caminhos a partir de uma doação indisponível (change
                    # acabamento), sem dizer qual foi o caso.
                    rx.text(DONATION_UNAVAILABLE_TEXT, color="#555555", text_align="center"),
                    rx.flex(
                        _state_link("Ver outras doações", "/explorar", "detail-unavailable-explore", solid=True),
                        _state_link("Voltar ao início", "/", "detail-unavailable-home", solid=False),
                        gap="12px",
                        wrap="wrap",
                        justify="center",
                    ),
                ),
                rx.cond(
                    DonationDetailState.view_state == "error",
                    _detail_state_message(
                        DONATION_DETAIL_ERROR_MESSAGE,
                        "#9B2C2C",
                        # Busca a doação de novo (change navegacao-celular).
                        rx.button(
                            rx.icon("rotate-cw", size=16, aria_hidden="true"),
                            # Mesmo texto das outras páginas (change
                            # correcoes-revisao).
                            "Tentar de novo",
                            on_click=DonationDetailState.retry_donation,
                            class_name="detail-retry",
                            variant="outline",
                            color=PRIMARY_GREEN,
                            border_color=PRIMARY_GREEN,
                            min_height="44px",
                            cursor="pointer",
                            _focus_visible={"outline": f"2px solid {PRIMARY_GREEN}", "outlineOffset": "2px"},
                        ),
                    ),
                    _donation_content(),
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
