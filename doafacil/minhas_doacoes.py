"""Minhas doações: cliente dos endpoints autenticados, estados e páginas.

Rotas /minhas-doacoes e /minhas-doacoes/<id>/editar, só com login. Toda a
autorização é do Xano (a pessoa vem do token); o frontend só envia o token e
o id da doação. Layout segundo o frame Group 6 do Figma, com as diferenças
registradas em docs/design/README.md (que prevalece). Todo dado vindo do Xano
é renderizado com componentes de texto, sem HTML.
"""

from __future__ import annotations

from typing import Any

import httpx
import reflex as rx

from doafacil.cadastro_doacao import (
    CATALOG_API_ENV,
    CONDITIONS,
    CONTACT_PREFERENCES,
    DELIVERY_METHODS,
    DonationServiceError,
    _api_endpoint,
    _fetch_categories,
)
from doafacil.cartoes_doacao import GENERIC_DONATION_IMAGE
from doafacil.chat import PLATFORM_RATE_LIMIT_MESSAGE, avatar_initial, back_link_header
from doafacil.detalhe_doacao import (
    DONATION_NOT_FOUND_MESSAGE,
    DonationNotFoundError,
    _positive_donation_id,
)
from doafacil.login import LoginState
from doafacil.sobre import about_text, parse_about


MY_DONATIONS_PATH = "/catalog/donations/mine"
MY_DONATION_PATH = "/catalog/donations/mine/item"
DONATION_PATH = "/catalog/donations"
DONATION_STATUS_PATH = "/catalog/donations/status"
CATEGORIES_PATH = "/catalog/categories"
MY_DONATIONS_PER_PAGE = 6
TITLE_MAX_LENGTH = 100
DESCRIPTION_MAX_LENGTH = 2000

STATUS_AVAILABLE = "disponível"
STATUS_RESERVED = "reservada"
STATUS_COMPLETED = "concluída"
STATUSES = (STATUS_AVAILABLE, STATUS_RESERVED, STATUS_COMPLETED)
STATUS_LABELS = {
    STATUS_AVAILABLE: "Disponível",
    STATUS_RESERVED: "Reservada",
    STATUS_COMPLETED: "Concluída",
}

# Ações do menu: (tipo, rótulo, status de destino ou None).
ACTION_RESERVE = "reserve"
ACTION_MAKE_AVAILABLE = "make_available"
ACTION_COMPLETE = "complete"
ACTION_DELETE = "delete"
ACTION_TARGET_STATUS = {
    ACTION_RESERVE: STATUS_RESERVED,
    ACTION_MAKE_AVAILABLE: STATUS_AVAILABLE,
    ACTION_COMPLETE: STATUS_COMPLETED,
}
# Ações sem volta ou que apagam dados pedem confirmação.
CONFIRMED_ACTIONS = frozenset({ACTION_COMPLETE, ACTION_DELETE})
ACTION_SUCCESS_MESSAGES = {
    ACTION_RESERVE: "Doação marcada como reservada.",
    ACTION_MAKE_AVAILABLE: "Doação marcada como disponível.",
    ACTION_COMPLETE: "Doação marcada como concluída.",
    ACTION_DELETE: "Doação apagada.",
}

PAGE_TITLE = "Minhas doações"
LOADING_MESSAGE = "Carregando suas doações..."
LIST_ERROR_MESSAGE = "Não foi possível carregar suas doações. Tente novamente mais tarde."
PAGE_ERROR_MESSAGE = "Não foi possível carregar esta página de doações. Tente novamente."
RATE_LIMIT_MESSAGE = PLATFORM_RATE_LIMIT_MESSAGE
EMPTY_TITLE = "Você ainda não tem doações"
EMPTY_TEXT = "Quando você publicar uma doação, ela aparece aqui."
ACTION_ERROR_MESSAGE = "Não foi possível concluir a ação. Tente novamente."
ACTION_REJECTED_MESSAGE = (
    "Não foi possível fazer esta mudança. Atualize a página e confira o status da doação."
)
ACTION_NOT_FOUND_MESSAGE = "Esta doação não foi encontrada. Atualize a página."
SAVED_MESSAGE = "Alterações salvas."
EDIT_LOADING_MESSAGE = "Carregando doação..."
EDIT_ERROR_MESSAGE = "Não foi possível carregar a doação. Tente novamente mais tarde."
EDIT_COMPLETED_MESSAGE = "Esta doação foi concluída e não pode mais ser editada."
SAVE_ERROR_MESSAGE = "Não foi possível salvar as alterações. Tente novamente."
SAVE_REJECTED_MESSAGE = "Não foi possível salvar. Confira os campos e tente novamente."
SAVE_NOT_FOUND_MESSAGE = (
    "Não foi possível salvar: a doação não foi encontrada ou não pode mais ser editada."
)


class MyDonationsError(Exception):
    pass


class MyDonationsUnauthorizedError(MyDonationsError):
    pass


class MyDonationNotFoundError(MyDonationsError):
    pass


class MyDonationRejectedError(MyDonationsError):
    pass


class MyDonationsRateLimitError(MyDonationsError):
    pass


class MyDonationsServiceError(MyDonationsError):
    pass


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _endpoint(path: str) -> str:
    try:
        return _api_endpoint(CATALOG_API_ENV, path)
    except DonationServiceError:
        raise MyDonationsServiceError from None


def _bearer(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code == 401:
        raise MyDonationsUnauthorizedError
    # 403 (status e exclusão de doação alheia) e 404 têm o mesmo tratamento.
    if response.status_code in {403, 404}:
        raise MyDonationNotFoundError
    if response.status_code == 400:
        raise MyDonationRejectedError
    if response.status_code == 429:
        raise MyDonationsRateLimitError
    if response.status_code != 200:
        raise MyDonationsServiceError


def _json(response: httpx.Response) -> object:
    try:
        return response.json()
    except ValueError:
        raise MyDonationsServiceError from None


def _condition_label(condition: object) -> str:
    return f"Condição: {condition}" if condition else "Condição não informada"


def _parse_my_donation_item(item: object) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    donation_id = item.get("id")
    created_at = item.get("created_at")
    title = item.get("title")
    photo = item.get("photo")
    condition = item.get("condition")
    status = item.get("status")
    if (
        not _is_int(donation_id)
        or not _is_int(created_at)
        or not isinstance(title, str)
        or not title.strip()
        or (photo is not None and not isinstance(photo, str))
        or (condition is not None and condition not in CONDITIONS)
        or status not in STATUSES
    ):
        return None
    return {
        "id": donation_id,
        "title": title,
        "photo": photo or GENERIC_DONATION_IMAGE,
        "condition_label": _condition_label(condition),
        "status": status,
        "status_label": STATUS_LABELS[status],
    }


def _parse_my_donations(payload: object) -> dict[str, Any]:
    """Valida a lista e devolve só os campos usados. Campos extras são ignorados."""
    if not isinstance(payload, dict):
        raise MyDonationsServiceError
    owner = payload.get("owner")
    counts = payload.get("counts")
    raw_items = payload.get("items")
    first_name = owner.get("first_name") if isinstance(owner, dict) else None
    active = counts.get("active") if isinstance(counts, dict) else None
    completed = counts.get("completed") if isinstance(counts, dict) else None
    page = payload.get("page")
    total = payload.get("total")
    page_total = payload.get("page_total")
    if (
        not isinstance(first_name, str)
        or not first_name.strip()
        or not _is_int(active)
        or not _is_int(completed)
        or active < 0
        or completed < 0
        or not _is_int(page)
        or not _is_int(total)
        or not _is_int(page_total)
        or page < 1
        or total < 0
        or page_total < 0
        or not isinstance(raw_items, list)
    ):
        raise MyDonationsServiceError

    try:
        about = parse_about(owner.get("about"))
    except ValueError:
        raise MyDonationsServiceError from None

    items = [parsed for item in raw_items if (parsed := _parse_my_donation_item(item))]
    if raw_items and not items:
        raise MyDonationsServiceError
    return {
        "first_name": first_name.strip(),
        "about": about,
        "active": active,
        "completed": completed,
        "items": items,
        "page": page,
        "total": total,
        "page_total": page_total,
    }


def _parse_my_donation(payload: object, expected_id: int) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise MyDonationsServiceError
    title = payload.get("title")
    description = payload.get("description")
    category_id = payload.get("category_id")
    fields = {
        name: payload.get(name)
        for name in ("condition", "delivery_method", "contact_preference")
    }
    status = payload.get("status")
    if (
        payload.get("id") != expected_id
        or not isinstance(title, str)
        or (description is not None and not isinstance(description, str))
        or not _is_int(category_id)
        or any(value is not None and not isinstance(value, str) for value in fields.values())
        or status not in STATUSES
    ):
        raise MyDonationsServiceError
    return {
        "id": expected_id,
        "title": title,
        "description": description or "",
        "category_id": category_id,
        "condition": fields["condition"] or "",
        "delivery_method": fields["delivery_method"] or "",
        "contact_preference": fields["contact_preference"] or "",
        "status": status,
    }


async def fetch_my_donations(
    client: httpx.AsyncClient, auth_token: str, page: int = 1
) -> dict[str, Any]:
    response = await client.get(
        _endpoint(MY_DONATIONS_PATH),
        params={"page": page},
        headers=_bearer(auth_token),
    )
    _raise_for_status(response)
    return _parse_my_donations(_json(response))


async def fetch_my_donation(
    client: httpx.AsyncClient, auth_token: str, donation_id: int
) -> dict[str, Any]:
    response = await client.get(
        _endpoint(MY_DONATION_PATH),
        params={"donation_id": donation_id},
        headers=_bearer(auth_token),
    )
    _raise_for_status(response)
    return _parse_my_donation(_json(response), donation_id)


async def change_status(
    client: httpx.AsyncClient, auth_token: str, donation_id: int, status: str
) -> str:
    if status not in STATUSES:
        raise ValueError("Status inválido.")
    response = await client.patch(
        _endpoint(DONATION_STATUS_PATH),
        json={"donation_id": donation_id, "status": status},
        headers=_bearer(auth_token),
    )
    _raise_for_status(response)
    payload = _json(response)
    if not isinstance(payload, dict) or payload.get("status") != status:
        raise MyDonationsServiceError
    return status


async def update_donation(
    client: httpx.AsyncClient, auth_token: str, donation_id: int, fields: dict[str, Any]
) -> None:
    response = await client.patch(
        _endpoint(DONATION_PATH),
        json={"donation_id": donation_id, **fields},
        headers=_bearer(auth_token),
    )
    _raise_for_status(response)
    payload = _json(response)
    if not isinstance(payload, dict) or payload.get("id") != donation_id:
        raise MyDonationsServiceError


async def delete_donation(
    client: httpx.AsyncClient, auth_token: str, donation_id: int
) -> None:
    response = await client.delete(
        _endpoint(DONATION_PATH),
        params={"donation_id": donation_id},
        headers=_bearer(auth_token),
    )
    _raise_for_status(response)
    payload = _json(response)
    if not isinstance(payload, dict) or payload.get("deleted") is not True:
        raise MyDonationsServiceError


def count_label(count: int, singular: str, plural: str) -> str:
    return singular if count == 1 else plural


def _new_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=15.0)


def _clear_session(state: Any) -> None:
    state.auth_token = ""
    state.account_name = ""


def _clear_list(state: Any) -> None:
    state.first_name = ""
    state.about = ""
    state.initial = ""
    state.active_count = 0
    state.completed_count = 0
    state.items = []
    state.total = 0
    state.page = 1
    state.page_total = 0


def _apply_list(state: Any, data: dict[str, Any]) -> None:
    state.first_name = data["first_name"]
    state.about = data["about"]
    state.initial = avatar_initial(data["first_name"])
    state.active_count = data["active"]
    state.completed_count = data["completed"]
    state.items = data["items"]
    state.total = data["total"]
    state.page = data["page"]
    state.page_total = data["page_total"]


async def _reload_after_action(state: Any) -> None:
    """Recarrega a página atual; se ela ficou além da última, a última."""
    async with _new_client() as client:
        data = await fetch_my_donations(client, state.auth_token, state.page)
        if not data["items"] and data["page"] > 1 and data["page_total"] >= 1:
            data = await fetch_my_donations(
                client, state.auth_token, min(data["page"] - 1, data["page_total"])
            )
    _apply_list(state, data)


async def _perform_action(state: Any, kind: str, donation_id: int):
    """Faz a requisição da ação e recarrega a página (2 requisições)."""
    state.action_busy = True
    state.notice = ""
    state.notice_is_error = False
    yield
    try:
        async with _new_client() as client:
            if kind == ACTION_DELETE:
                await delete_donation(client, state.auth_token, donation_id)
            else:
                await change_status(
                    client, state.auth_token, donation_id, ACTION_TARGET_STATUS[kind]
                )
        await _reload_after_action(state)
    except MyDonationsUnauthorizedError:
        _clear_session(state)
        state.action_busy = False
        yield rx.redirect("/login")
        return
    except MyDonationNotFoundError:
        state.notice = ACTION_NOT_FOUND_MESSAGE
        state.notice_is_error = True
    except MyDonationRejectedError:
        state.notice = ACTION_REJECTED_MESSAGE
        state.notice_is_error = True
    except MyDonationsRateLimitError:
        state.notice = RATE_LIMIT_MESSAGE
        state.notice_is_error = True
    except (MyDonationsServiceError, httpx.HTTPError, ValueError):
        state.notice = ACTION_ERROR_MESSAGE
        state.notice_is_error = True
    else:
        state.notice = ACTION_SUCCESS_MESSAGES[kind]
    state.action_busy = False


def _clear_pending(state: Any) -> None:
    state.confirm_open = False
    state.pending_kind = ""
    state.pending_id = 0
    state.pending_title = ""


class MyDonationsState(LoginState):
    view_state: str = "loading"
    load_error: str = ""
    first_name: str = ""
    about: str = ""
    initial: str = ""
    active_count: int = 0
    completed_count: int = 0
    items: list[dict[str, Any]] = []
    total: int = 0
    page: int = 1
    page_total: int = 0
    page_loading: bool = False
    page_error: str = ""
    notice: str = ""
    notice_is_error: bool = False
    # Aviso deixado pela página de edição, mostrado uma vez na próxima entrada.
    flash: str = ""
    action_busy: bool = False
    confirm_open: bool = False
    pending_kind: str = ""
    pending_id: int = 0
    pending_title: str = ""

    @rx.var
    def confirm_heading(self) -> str:
        if self.pending_kind == ACTION_DELETE:
            return "Apagar esta doação?"
        return "Marcar como concluída?"

    @rx.var
    def confirm_text(self) -> str:
        title = f"“{self.pending_title}”"
        if self.pending_kind == ACTION_DELETE:
            return (
                f"{title}, as fotos e todas as conversas e mensagens sobre ela "
                "serão apagadas. Isso não tem volta."
            )
        return (
            f"{title} vai ficar como concluída e não poderá voltar a outro status. "
            "As conversas sobre ela ficam somente para leitura."
        )

    @rx.var
    def confirm_button_label(self) -> str:
        if self.pending_kind == ACTION_DELETE:
            return "Apagar doação"
        return "Marcar como concluída"

    @rx.var
    def active_label(self) -> str:
        return count_label(self.active_count, "Doação", "Doações")

    @rx.var
    def completed_label(self) -> str:
        return count_label(
            self.completed_count, "Doação realizada", "Doações realizadas"
        )

    @rx.event
    def set_flash(self, message: str) -> None:
        self.flash = message

    @rx.event
    async def load_page(self):
        _clear_list(self)
        _clear_pending(self)
        self.view_state = "loading"
        self.load_error = ""
        self.page_loading = False
        self.page_error = ""
        self.action_busy = False
        self.notice = self.flash
        self.notice_is_error = False
        self.flash = ""

        if not self.auth_token:
            yield rx.redirect("/login")
            return
        try:
            async with _new_client() as client:
                data = await fetch_my_donations(client, self.auth_token, 1)
        except MyDonationsUnauthorizedError:
            _clear_session(self)
            yield rx.redirect("/login")
            return
        except MyDonationsRateLimitError:
            self.load_error = RATE_LIMIT_MESSAGE
            self.view_state = "error"
        except (MyDonationsError, httpx.HTTPError, ValueError):
            self.load_error = LIST_ERROR_MESSAGE
            self.view_state = "error"
        else:
            _apply_list(self, data)
            self.view_state = "ready"

    @rx.event
    async def go_to_page(self, page: int):
        if self.view_state != "ready" or self.page_loading or self.action_busy:
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
            async with _new_client() as client:
                data = await fetch_my_donations(client, self.auth_token, target)
        except MyDonationsUnauthorizedError:
            _clear_session(self)
            self.page_loading = False
            yield rx.redirect("/login")
            return
        except MyDonationsRateLimitError:
            self.page_error = RATE_LIMIT_MESSAGE
        except (MyDonationsError, httpx.HTTPError, ValueError):
            self.page_error = PAGE_ERROR_MESSAGE
        else:
            _apply_list(self, data)
        self.page_loading = False

    @rx.event
    async def request_action(self, kind: str, donation_id: int, title: str):
        """Reservar e voltar a disponível rodam direto; concluir e apagar
        abrem a confirmação."""
        if self.action_busy or self.view_state != "ready":
            return
        if kind not in ACTION_SUCCESS_MESSAGES or not _is_int(donation_id):
            return
        if kind in CONFIRMED_ACTIONS:
            self.pending_kind = kind
            self.pending_id = donation_id
            self.pending_title = title
            self.confirm_open = True
            return
        async for event in _perform_action(self, kind, donation_id):
            yield event

    @rx.event
    def cancel_action(self) -> None:
        _clear_pending(self)

    @rx.event
    def set_confirm_open(self, is_open: bool) -> None:
        # Esc e o botão “Cancelar” do diálogo chegam aqui com False.
        if not is_open:
            _clear_pending(self)

    @rx.event
    async def confirm_action(self):
        kind = self.pending_kind
        donation_id = self.pending_id
        _clear_pending(self)
        if self.action_busy or kind not in CONFIRMED_ACTIONS or not donation_id:
            return
        async for event in _perform_action(self, kind, donation_id):
            yield event


# Edição ---------------------------------------------------------------------


def _validate_edit(
    title: str,
    description: str,
    category_id: str,
    condition: str,
    delivery_method: str,
    contact_preference: str,
    category_ids: set[int],
) -> str:
    """Mesmas regras do cadastro (título, descrição, categoria, condição,
    entrega e contato), com mensagens próprias da edição."""
    if not title.strip():
        return "Informe o nome do item."
    if len(title.strip()) > TITLE_MAX_LENGTH:
        return f"O nome do item pode ter no máximo {TITLE_MAX_LENGTH} caracteres."
    if not description.strip():
        return "Descreva o item."
    if len(description.strip()) > DESCRIPTION_MAX_LENGTH:
        return f"A descrição pode ter no máximo {DESCRIPTION_MAX_LENGTH} caracteres."
    try:
        selected_category = int(category_id)
    except ValueError:
        return "Selecione uma categoria."
    if selected_category not in category_ids:
        return "Selecione uma categoria válida."
    if condition not in CONDITIONS:
        return "Selecione a condição do item."
    if delivery_method not in DELIVERY_METHODS:
        return "Selecione uma forma de entrega."
    if contact_preference not in CONTACT_PREFERENCES:
        return "Selecione uma forma de contato."
    return ""


def _clear_form(state: Any) -> None:
    state.donation_id = 0
    state.title = ""
    state.description = ""
    state.category_id = ""
    state.category_name = ""
    state.condition = ""
    state.delivery_method = ""
    state.contact_preference = ""
    state.categories = []
    state.form_error = ""
    state.is_saving = False


class EditDonationState(LoginState):
    view_state: str = "loading"
    load_error: str = ""
    donation_id: int = 0
    title: str = ""
    description: str = ""
    category_id: str = ""
    category_name: str = ""
    condition: str = ""
    delivery_method: str = ""
    contact_preference: str = ""
    categories: list[dict[str, Any]] = []
    form_error: str = ""
    is_saving: bool = False

    @rx.var
    def category_options(self) -> list[str]:
        return [category["name"] for category in self.categories]

    @rx.event
    async def load_edit(self):
        _clear_form(self)
        self.view_state = "loading"
        self.load_error = ""

        if not self.auth_token:
            yield rx.redirect("/login")
            return
        try:
            donation_id = _positive_donation_id(self.router.page.params.get("id", ""))
        except DonationNotFoundError:
            self.view_state = "not_found"
            return

        try:
            async with _new_client() as client:
                categories = await _fetch_categories(client, _endpoint(CATEGORIES_PATH))
                donation = await fetch_my_donation(client, self.auth_token, donation_id)
        except MyDonationsUnauthorizedError:
            _clear_session(self)
            yield rx.redirect("/login")
            return
        except MyDonationNotFoundError:
            self.view_state = "not_found"
            return
        except MyDonationsRateLimitError:
            self.load_error = RATE_LIMIT_MESSAGE
            self.view_state = "error"
            return
        except (MyDonationsError, DonationServiceError, httpx.HTTPError, ValueError):
            self.load_error = EDIT_ERROR_MESSAGE
            self.view_state = "error"
            return

        if donation["status"] == STATUS_COMPLETED:
            self.view_state = "completed"
            return

        self.donation_id = donation_id
        self.categories = categories
        self.title = donation["title"]
        self.description = donation["description"]
        # Um valor fora das opções do cadastro deixa o campo vazio.
        category = next(
            (item for item in categories if item["id"] == donation["category_id"]),
            None,
        )
        self.category_id = str(category["id"]) if category else ""
        self.category_name = category["name"] if category else ""
        self.condition = donation["condition"] if donation["condition"] in CONDITIONS else ""
        self.delivery_method = (
            donation["delivery_method"]
            if donation["delivery_method"] in DELIVERY_METHODS
            else ""
        )
        self.contact_preference = (
            donation["contact_preference"]
            if donation["contact_preference"] in CONTACT_PREFERENCES
            else ""
        )
        self.view_state = "ready"

    @rx.event
    def set_title(self, value: str) -> None:
        self.title = value

    @rx.event
    def set_description(self, value: str) -> None:
        self.description = value

    @rx.event
    def set_category(self, value: str) -> None:
        selected = next(
            (category for category in self.categories if category["name"] == value),
            None,
        )
        self.category_id = str(selected["id"]) if selected else ""
        self.category_name = selected["name"] if selected else ""

    @rx.event
    def set_condition(self, value: str) -> None:
        self.condition = value

    @rx.event
    def set_delivery_method(self, value: str) -> None:
        self.delivery_method = value

    @rx.event
    def set_contact_preference(self, value: str) -> None:
        self.contact_preference = value

    @rx.event
    async def save(self):
        if self.is_saving or self.view_state != "ready":
            return
        error = _validate_edit(
            self.title,
            self.description,
            self.category_id,
            self.condition,
            self.delivery_method,
            self.contact_preference,
            {category["id"] for category in self.categories},
        )
        if error:
            self.form_error = error
            return

        self.form_error = ""
        self.is_saving = True
        yield
        fields = {
            "category_id": int(self.category_id),
            "title": self.title.strip(),
            "description": self.description.strip(),
            "condition": self.condition,
            "delivery_method": self.delivery_method,
            "contact_preference": self.contact_preference,
        }
        try:
            async with _new_client() as client:
                await update_donation(client, self.auth_token, self.donation_id, fields)
        except MyDonationsUnauthorizedError:
            _clear_session(self)
            self.is_saving = False
            yield rx.redirect("/login")
            return
        except MyDonationNotFoundError:
            self.form_error = SAVE_NOT_FOUND_MESSAGE
        except MyDonationRejectedError:
            self.form_error = SAVE_REJECTED_MESSAGE
        except MyDonationsRateLimitError:
            self.form_error = RATE_LIMIT_MESSAGE
        except (MyDonationsError, httpx.HTTPError, ValueError):
            self.form_error = SAVE_ERROR_MESSAGE
        else:
            self.is_saving = False
            yield MyDonationsState.set_flash(SAVED_MESSAGE)
            yield rx.redirect("/minhas-doacoes")
            return
        self.is_saving = False


# Página: Minhas doações -------------------------------------------------------

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
DANGER_RED = "#B42318"
DANGER_RED_HOVER = "#912018"
CONTENT_MAX_WIDTH = "1396px"
# Selo de status: fundo opaco, para o contraste não depender da foto.
STATUS_BADGE_COLORS = {
    STATUS_AVAILABLE: ("#E3F5EA", "#166B3B"),
    STATUS_RESERVED: ("#FFF1D6", "#7A4B00"),
    STATUS_COMPLETED: ("#ECECEC", "#3D3D3D"),
}


def _status_color(status: rx.Var, index: int) -> rx.Var:
    return rx.match(
        status,
        (STATUS_AVAILABLE, STATUS_BADGE_COLORS[STATUS_AVAILABLE][index]),
        (STATUS_RESERVED, STATUS_BADGE_COLORS[STATUS_RESERVED][index]),
        STATUS_BADGE_COLORS[STATUS_COMPLETED][index],
    )


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


def _status_badge(donation: rx.Var) -> rx.Component:
    return rx.text(
        donation["status_label"],
        class_name="my-donation-status",
        position="absolute",
        top="12px",
        left="12px",
        padding="4px 10px",
        border_radius="999px",
        font_size="0.8rem",
        font_weight="700",
        line_height="1.2",
        background=_status_color(donation["status"], 0),
        color=_status_color(donation["status"], 1),
    )


def _menu_item(label: str, kind: str, donation: rx.Var, **props: Any) -> rx.Component:
    return rx.dropdown_menu.item(
        label,
        on_select=MyDonationsState.request_action(kind, donation["id"], donation["title"]),
        **props,
    )


def _actions_menu(donation: rx.Var) -> rx.Component:
    """Menu de ações com só as ações válidas para o status atual."""
    status = donation["status"]
    edit_item = rx.dropdown_menu.item(
        "Editar",
        on_select=rx.redirect(f"/minhas-doacoes/{donation['id']}/editar"),
    )
    delete_item = _menu_item("Apagar", ACTION_DELETE, donation, color=DANGER_RED)
    return rx.dropdown_menu.root(
        rx.dropdown_menu.trigger(
            rx.el.button(
                rx.icon("ellipsis-vertical", size=22, aria_hidden="true"),
                type="button",
                aria_label=rx.Var.create("Ações da doação ") + donation["title"].to(str),
                title="Ações",
                disabled=MyDonationsState.action_busy,
                class_name="my-donation-menu",
                position="absolute",
                top="8px",
                right="8px",
                display="inline-flex",
                align_items="center",
                justify_content="center",
                width="44px",
                height="44px",
                padding="0",
                border="none",
                border_radius="999px",
                background=WHITE,
                color=TEXT_STRONG,
                box_shadow="0 2px 8px rgba(0, 0, 0, 0.18)",
                cursor="pointer",
                _focus_visible={"outline": f"2px solid {LINK_GREEN}", "outlineOffset": "2px"},
            ),
        ),
        rx.dropdown_menu.content(
            rx.match(
                status,
                (
                    STATUS_AVAILABLE,
                    rx.fragment(
                        _menu_item("Marcar como reservada", ACTION_RESERVE, donation),
                        _menu_item("Marcar como concluída", ACTION_COMPLETE, donation),
                        edit_item,
                        rx.dropdown_menu.separator(),
                        delete_item,
                    ),
                ),
                (
                    STATUS_RESERVED,
                    rx.fragment(
                        _menu_item("Marcar como disponível", ACTION_MAKE_AVAILABLE, donation),
                        _menu_item("Marcar como concluída", ACTION_COMPLETE, donation),
                        edit_item,
                        rx.dropdown_menu.separator(),
                        delete_item,
                    ),
                ),
                rx.fragment(delete_item),
            ),
            align="end",
        ),
    )


def my_donation_card(donation: rx.Var) -> rx.Component:
    """Foto, selo de status, menu, título, “Condição: …” e, só nas
    disponíveis, “Ver anúncio”. Sem o NOVO."""
    is_generic = donation["photo"] == GENERIC_DONATION_IMAGE
    return rx.box(
        rx.cond(
            is_generic,
            rx.image(
                src=donation["photo"],
                alt=donation["title"],
                position="absolute",
                top="4%",
                left="16%",
                width="68%",
                height="68%",
                object_fit="contain",
            ),
            rx.image(
                src=donation["photo"],
                alt=donation["title"],
                position="absolute",
                inset="0",
                width="100%",
                height="100%",
                object_fit="cover",
            ),
        ),
        _status_badge(donation),
        _actions_menu(donation),
        rx.vstack(
            rx.heading(
                donation["title"],
                as_="h3",
                font_size="1.05rem",
                font_weight="700",
                color="white",
                no_of_lines=2,
                overflow_wrap="anywhere",
            ),
            rx.text(
                donation["condition_label"],
                color="white",
                font_size="0.85rem",
                width="100%",
                overflow_wrap="anywhere",
            ),
            rx.cond(
                donation["status"] == STATUS_AVAILABLE,
                rx.link(
                    "Ver anúncio",
                    href=f"/doacao/{donation['id']}",
                    align_self="end",
                    display="inline-flex",
                    align_items="center",
                    min_height="32px",
                    padding="4px 12px",
                    border_radius="999px",
                    background=LINK_GREEN,
                    color="white",
                    font_size="0.85rem",
                    font_weight="700",
                    _hover={"background": LINK_GREEN_HOVER, "textDecoration": "none"},
                ),
                rx.fragment(),
            ),
            align="start",
            spacing="2",
            position="absolute",
            bottom="0",
            left="0",
            width="100%",
            padding="16px",
            min_height="48%",
            background=rx.cond(
                is_generic,
                "linear-gradient(180deg, transparent 0%, rgba(15, 123, 62, 0.92) 55%)",
                "linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.78) 55%)",
            ),
        ),
        class_name="my-donation-card",
        position="relative",
        overflow="hidden",
        border_radius="16px",
        width="100%",
        min_width="0",
        aspect_ratio="1 / 1",
        background=rx.cond(is_generic, "#DDF3E5", CREAM),
        box_shadow="0 4px 16px rgba(39, 39, 39, 0.12)",
    )


def _stat(value: rx.Var, label: rx.Var) -> rx.Component:
    return rx.vstack(
        rx.text(value, color=TITLE_GREEN, font_size="1.5rem", font_weight="700", line_height="1"),
        rx.text(label, color=TEXT_MUTED, font_size="0.85rem", text_align="center"),
        align="center",
        spacing="1",
        min_width="0",
    )


def _owner_card() -> rx.Component:
    """Círculo com a inicial, primeiro nome, os dois contadores, o Sobre (só
    quando preenchido) e “Editar perfil”. Sem foto, e-mail, “Compartilhar”,
    avaliações, selo ou chat."""
    return rx.vstack(
        rx.box(
            rx.text(
                MyDonationsState.initial,
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
            MyDonationsState.first_name,
            color=TEXT_STRONG,
            font_size="1.15rem",
            font_weight="700",
            text_align="center",
            overflow_wrap="anywhere",
        ),
        rx.hstack(
            _stat(MyDonationsState.active_count, MyDonationsState.active_label),
            _stat(MyDonationsState.completed_count, MyDonationsState.completed_label),
            spacing="6",
            justify="center",
            width="100%",
        ),
        about_text(MyDonationsState.about, text_align="center"),
        rx.link(
            "Editar perfil",
            href="/perfil/editar",
            class_name="my-donations-edit-profile",
            display="inline-flex",
            align_items="center",
            justify_content="center",
            min_height="44px",
            width="100%",
            padding="0 16px",
            border=f"1px solid {LINK_GREEN}",
            border_radius="999px",
            color=LINK_GREEN,
            font_weight="700",
            _hover={"background": "#F1F8F3", "textDecoration": "none"},
            _focus_visible={"outline": f"2px solid {LINK_GREEN}", "outlineOffset": "2px"},
        ),
        class_name="my-donations-owner",
        align="center",
        spacing="3",
        width="100%",
        padding="24px 16px",
        background=WHITE,
        border=f"1px solid {BORDER_SOFT}",
        border_radius="8px",
    )


def _page_button(label: str, target: rx.Var, disabled: rx.Var) -> rx.Component:
    return rx.button(
        label,
        on_click=MyDonationsState.go_to_page(target),
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
        _focus_visible={"outline": f"2px solid {LINK_GREEN}", "outlineOffset": "2px"},
    )


def _pagination() -> rx.Component:
    busy = MyDonationsState.page_loading | MyDonationsState.action_busy
    return rx.cond(
        MyDonationsState.page_total > 1,
        rx.vstack(
            rx.hstack(
                _page_button(
                    "Anterior",
                    MyDonationsState.page - 1,
                    (MyDonationsState.page <= 1) | busy,
                ),
                rx.text(
                    "Página ",
                    MyDonationsState.page,
                    " de ",
                    MyDonationsState.page_total,
                    aria_live="polite",
                    color=TEXT_STRONG,
                    font_size="0.95rem",
                    white_space="nowrap",
                ),
                _page_button(
                    "Próxima",
                    MyDonationsState.page + 1,
                    (MyDonationsState.page >= MyDonationsState.page_total) | busy,
                ),
                class_name="my-donations-pagination",
                spacing="4",
                align="center",
                justify="center",
                wrap="wrap",
                width="100%",
            ),
            rx.cond(
                MyDonationsState.page_error != "",
                rx.text(
                    MyDonationsState.page_error,
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


def _donations_grid() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.foreach(MyDonationsState.items, my_donation_card),
            class_name="my-donations-grid",
            style={
                "display": "grid",
                "gridTemplateColumns": rx.breakpoints(
                    initial="minmax(0, 1fr)",
                    sm="repeat(2, minmax(0, 1fr))",
                    lg="repeat(3, minmax(0, 1fr))",
                ),
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
        rx.text(EMPTY_TEXT, color=TEXT_MUTED, text_align="center"),
        rx.link(
            "Quero Doar",
            href="/cadastro-doacao",
            display="inline-flex",
            align_items="center",
            min_height="44px",
            padding="0 24px",
            border_radius="999px",
            background=LINK_GREEN,
            color="white",
            font_weight="700",
            _hover={"background": LINK_GREEN_HOVER, "textDecoration": "none"},
        ),
        class_name="my-donations-empty",
        align="center",
        spacing="3",
        width="100%",
        padding=rx.breakpoints(initial="32px 16px", md="48px 40px"),
        background=WHITE,
        border=f"1px solid {BORDER_SOFT}",
        border_radius="8px",
    )


def _notice() -> rx.Component:
    return rx.cond(
        MyDonationsState.notice != "",
        rx.text(
            MyDonationsState.notice,
            role="status",
            class_name="my-donations-notice",
            color=rx.cond(MyDonationsState.notice_is_error, TEXT_ERROR, TITLE_GREEN),
            font_weight="600",
            width="100%",
        ),
        rx.fragment(),
    )


def _confirm_dialog() -> rx.Component:
    """Confirmação de concluir e de apagar (prende o foco, Esc cancela)."""
    is_delete = MyDonationsState.pending_kind == ACTION_DELETE
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(MyDonationsState.confirm_heading, color=TEXT_STRONG),
            rx.alert_dialog.description(
                MyDonationsState.confirm_text,
                color=TEXT_STRONG,
                overflow_wrap="anywhere",
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancelar",
                        variant="outline",
                        color=TEXT_STRONG,
                        border="1px solid #85858D",
                        min_height="44px",
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        MyDonationsState.confirm_button_label,
                        on_click=MyDonationsState.confirm_action,
                        min_height="44px",
                        color="white",
                        background=rx.cond(is_delete, DANGER_RED, LINK_GREEN),
                        _hover={
                            "background": rx.cond(is_delete, DANGER_RED_HOVER, LINK_GREEN_HOVER)
                        },
                    ),
                ),
                spacing="3",
                justify="end",
                wrap="wrap",
                padding_top="16px",
            ),
            max_width="480px",
            background=WHITE,
        ),
        open=MyDonationsState.confirm_open,
        on_open_change=MyDonationsState.set_confirm_open,
    )


def _my_donations_content() -> rx.Component:
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
            _notice(),
            rx.box(
                rx.box(_owner_card(), min_width="0"),
                rx.box(
                    rx.cond(
                        MyDonationsState.items.length() == 0,
                        _empty_state(),
                        _donations_grid(),
                    ),
                    min_width="0",
                ),
                class_name="my-donations-layout",
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
            _confirm_dialog(),
            align="stretch",
            spacing="5",
            width="100%",
            max_width=CONTENT_MAX_WIDTH,
            margin="0 auto",
        ),
        width="100%",
        min_height="calc(100vh - 88px)",
        padding=rx.breakpoints(initial="24px 16px 48px", md="32px 24px 56px"),
        background=CREAM,
    )


def my_donations_page() -> rx.Component:
    return rx.box(
        back_link_header("/", "Voltar ao início", LINK_GREEN),
        rx.cond(
            MyDonationsState.view_state == "loading",
            _state_message(LOADING_MESSAGE, TEXT_MUTED),
            rx.cond(
                MyDonationsState.view_state == "error",
                _state_message(MyDonationsState.load_error, TEXT_ERROR),
                _my_donations_content(),
            ),
        ),
        display="flex",
        flex_direction="column",
        width="100%",
        min_height="100vh",
        background=CREAM,
        font_family="'LINE Seed JP', Arial, sans-serif",
    )


# Página: edição ---------------------------------------------------------------


def _field_label(text: str, html_for: str) -> rx.Component:
    return rx.el.label(
        text,
        html_for=html_for,
        color="#333333",
        font_weight="700",
        font_size="0.8rem",
        width="100%",
    )


EDIT_FIELD_TEXT = "#1F1F1F"
EDIT_FIELD_BORDER = "1px solid #C8C8C8"
EDIT_SELECT_PLACEHOLDER = "#333333"


def _edit_select(
    label: str,
    options: tuple[str, ...] | rx.Var,
    value: rx.Var,
    on_change: Any,
    placeholder: str,
    field_id: str,
) -> rx.Component:
    """Select da edição com o estilo no Trigger (o botão visível): fundo
    branco, borda e altura dos campos de texto, texto #1F1F1F e foco visível.
    No Root, o estilo não chega ao botão, que ficava com o fundo cinza."""
    if isinstance(options, rx.Var):
        items = rx.foreach(options, lambda option: rx.select.item(option, value=option))
    else:
        items = [rx.select.item(option, value=option) for option in options]
    return rx.vstack(
        _field_label(label, field_id),
        rx.select.root(
            rx.select.trigger(
                placeholder=placeholder,
                id=field_id,
                class_name="edit-donation-select",
                width="100%",
                height="40px",
                background=WHITE,
                color=EDIT_FIELD_TEXT,
                border=EDIT_FIELD_BORDER,
                border_radius="8px",
                box_shadow="none",
                cursor="pointer",
                _focus_visible={
                    "outline": f"2px solid {LINK_GREEN}",
                    "outlineOffset": "1px",
                },
                style={
                    "&[data-placeholder] .rt-SelectTriggerInner": {
                        "color": EDIT_SELECT_PLACEHOLDER,
                    },
                },
            ),
            rx.select.content(rx.select.group(items), high_contrast=True),
            value=value,
            on_change=on_change,
        ),
        align="start",
        spacing="2",
        width="100%",
    )


def _edit_form() -> rx.Component:
    # Os campos de texto usam os ids do cadastro: as regras de cor do
    # placeholder e do texto digitado no app.style valem aqui também. Os
    # selects têm ids próprios e o estilo no Trigger (_edit_select).
    return rx.vstack(
        rx.heading(
            "Editar doação",
            as_="h1",
            color=TITLE_GREEN,
            font_size="1.5rem",
            font_weight="700",
            width="100%",
        ),
        rx.text(
            "As fotos, a cidade e a UF não mudam por aqui.",
            color=TEXT_MUTED,
            font_size="0.9rem",
            width="100%",
        ),
        _field_label("Nome do item", "donation-title"),
        rx.input(
            value=EditDonationState.title,
            on_change=EditDonationState.set_title,
            placeholder="Ex.: Carrinho de brinquedo",
            id="donation-title",
            max_length=TITLE_MAX_LENGTH,
            width="100%",
            height="40px",
            background="white",
            color="#333333",
            border="1px solid #C8C8C8",
            border_radius="8px",
        ),
        _field_label("Descrição", "donation-description"),
        rx.text_area(
            value=EditDonationState.description,
            on_change=EditDonationState.set_description,
            placeholder="Conte detalhes importantes sobre o objeto.",
            id="donation-description",
            max_length=DESCRIPTION_MAX_LENGTH,
            min_height="120px",
            width="100%",
            background="white",
            color="#333333",
            border="1px solid #C8C8C8",
            border_radius="8px",
        ),
        _edit_select(
            "Categoria",
            EditDonationState.category_options,
            EditDonationState.category_name,
            EditDonationState.set_category,
            "Selecione uma categoria",
            "edit-donation-category",
        ),
        _edit_select(
            "Condição do item",
            CONDITIONS,
            EditDonationState.condition,
            EditDonationState.set_condition,
            "Selecione a condição",
            "edit-donation-condition",
        ),
        _edit_select(
            "Forma de entrega",
            DELIVERY_METHODS,
            EditDonationState.delivery_method,
            EditDonationState.set_delivery_method,
            "Selecione a forma de entrega",
            "edit-donation-delivery-method",
        ),
        _edit_select(
            "Forma de contato",
            CONTACT_PREFERENCES,
            EditDonationState.contact_preference,
            EditDonationState.set_contact_preference,
            "Selecione uma forma de contato",
            "edit-donation-contact-preference",
        ),
        rx.cond(
            EditDonationState.form_error != "",
            rx.text(
                EditDonationState.form_error,
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
                rx.cond(EditDonationState.is_saving, "Salvando...", "Salvar alterações"),
                on_click=EditDonationState.save,
                disabled=EditDonationState.is_saving,
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
            justify="end",
            wrap="wrap",
            width="100%",
            padding_top="8px",
        ),
        class_name="auth-card-enter",
        align="start",
        spacing="3",
        width="100%",
        max_width="640px",
        margin="0 auto",
        padding=rx.breakpoints(initial="24px 16px", md="32px 40px"),
        background=WHITE,
        border=f"1px solid {BORDER_SOFT}",
        border_radius="8px",
    )


def edit_donation_page() -> rx.Component:
    return rx.box(
        back_link_header("/minhas-doacoes", "Voltar a Minhas doações", LINK_GREEN),
        rx.match(
            EditDonationState.view_state,
            ("loading", _state_message(EDIT_LOADING_MESSAGE, TEXT_MUTED)),
            ("not_found", _state_message(DONATION_NOT_FOUND_MESSAGE, TEXT_MUTED)),
            ("completed", _state_message(EDIT_COMPLETED_MESSAGE, TEXT_MUTED)),
            ("error", _state_message(EditDonationState.load_error, TEXT_ERROR)),
            rx.box(
                _edit_form(),
                width="100%",
                min_height="calc(100vh - 88px)",
                padding=rx.breakpoints(initial="24px 16px 48px", md="32px 24px 56px"),
                background=CREAM,
            ),
        ),
        display="flex",
        flex_direction="column",
        width="100%",
        min_height="100vh",
        background=CREAM,
        font_family="'LINE Seed JP', Arial, sans-serif",
    )
