"""Chat da doação: cliente HTTP dos endpoints do Xano e estado da página /chat.

A página (componentes) entra numa etapa posterior da change chat-frontend.
Nenhum texto vindo do chat é interpretado como HTML: tudo é guardado como
texto simples e renderizado com componentes de texto.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import reflex as rx

from doafacil.cadastro_doacao import (
    CATALOG_API_ENV,
    DonationServiceError,
    _api_endpoint,
)
from doafacil.login import LoginState


# Endpoints do grupo Catalog.
START_PATH = "/catalog/chat/conversations/start"
CONVERSATIONS_PATH = "/catalog/chat/conversations"
MESSAGES_PATH = "/catalog/chat/messages"
UNREAD_TOTAL_PATH = "/catalog/chat/unread_total"

CONVERSATIONS_PAGE_LIMIT = 20
MESSAGES_PAGE_LIMIT = 50
POLL_MESSAGES_LIMIT = 100
MAX_MESSAGE_LENGTH = 1000
POLL_PAUSE_SECONDS = 60
MESSAGE_INPUT_ID = "chat-message-input"
DONATION_STATUS_COMPLETED = "concluída"

# Mensagem que o endpoint do chat devolve no 429 do limite de envio.
CHAT_RATE_LIMIT_MARKER = "Limite de mensagens atingido"

# Textos da interface.
CONVERSATION_NOT_FOUND_MESSAGE = "Conversa não encontrada."
LIST_ERROR_MESSAGE = "Não foi possível carregar as conversas. Tente novamente."
MESSAGES_ERROR_MESSAGE = "Não foi possível carregar as mensagens. Tente novamente."
SEND_INVALID_MESSAGE = "A mensagem precisa ter entre 1 e 1000 caracteres."
SEND_NOT_FOUND_MESSAGE = (
    "Não foi possível enviar. Esta conversa não está mais disponível para "
    "novas mensagens."
)
SEND_ERROR_MESSAGE = "Não foi possível enviar a mensagem. Tente novamente."
CHAT_RATE_LIMIT_MESSAGE = (
    "Você enviou muitas mensagens em pouco tempo. Aguarde um minuto."
)
PLATFORM_RATE_LIMIT_MESSAGE = (
    "O site está com muitos acessos agora. Tente de novo em instantes."
)
READ_ONLY_MESSAGE = (
    "Esta doação foi concluída. A conversa fica disponível somente para "
    "leitura."
)
EMPTY_LIST_MESSAGE = "Você ainda não tem conversas."
NO_CONVERSATION_MESSAGE = "Escolha uma conversa para ver as mensagens."
EMPTY_CONVERSATION_MESSAGE = "Ainda não há mensagens. Escreva a primeira."
MESSAGE_PLACEHOLDER = "Digite aqui..."
POLL_INTERVAL_MS = 15000
LIST_POLL_INTERVAL_MS = 30000
UNREAD_DISPLAY_MAX = 99

# Edição e “visto”.
EDIT_WINDOW_SECONDS = 15 * 60
EDITING_LABEL = "Editando mensagem"
EDITED_LABEL = "(editada)"
SENT_STATUS_LABEL = "Enviada"
READ_STATUS_LABEL = "Lida"
EDIT_BUTTON_LABEL = "Editar mensagem"
EDIT_EXPIRED_MESSAGE = "Não foi possível editar. O prazo de 15 minutos terminou."
EDIT_NOT_FOUND_MESSAGE = "Não foi possível editar esta mensagem."
EDIT_ERROR_MESSAGE = "Não foi possível salvar a edição. Tente novamente."

# Cores (contraste AA sobre os fundos usados).
GREEN_TEXT = "#166B3B"
GREEN_BUTTON = "#007A42"
GREEN_BUTTON_HOVER = "#006B39"
GREEN_AVATAR = "#00A859"
GREEN_BORDER = "#18A566"
LIGHT_BORDER = "#DDEFE4"
BUBBLE_OTHER = "#E9ECEF"
TEXT_DARK = "#1F1F1F"
TEXT_MUTED = "#555555"
TEXT_TIME = "#6b6b6b"
CREAM = "#FFF6E8"

# Brasil sem horário de verão desde 2019: fuso fixo evita depender de tzdata.
BRASILIA = timezone(timedelta(hours=-3))


# ---------------------------------------------------------------------------
# Erros
# ---------------------------------------------------------------------------


class ChatError(Exception):
    """Erro do chat sem detalhes do corpo da resposta."""


class ChatServiceError(ChatError):
    """Rede, configuração, resposta malformada ou erro inesperado do serviço."""


class ChatUnauthorizedError(ChatError):
    """HTTP 401: sessão ausente, inválida ou expirada."""


class ChatNotFoundError(ChatError):
    """HTTP 404 genérico do chat."""


class ChatInvalidMessageError(ChatError):
    """HTTP 400: texto vazio, acima do limite ou cursores juntos."""


class ChatRateLimitError(ChatError):
    """HTTP 429, do limite do chat ("chat") ou da plataforma ("platform")."""

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


# ---------------------------------------------------------------------------
# Auxiliares puros
# ---------------------------------------------------------------------------


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def classify_rate_limit(payload: object) -> str:
    """'chat' quando a mensagem é a do limite do chat; senão, 'platform'."""
    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str) and CHAT_RATE_LIMIT_MARKER in message:
            return "chat"
    return "platform"


def rate_limit_message(kind: str) -> str:
    if kind == "chat":
        return CHAT_RATE_LIMIT_MESSAGE
    return PLATFORM_RATE_LIMIT_MESSAGE


def avatar_initial(name: object) -> str:
    if not isinstance(name, str):
        return "?"
    cleaned = name.strip()
    if not cleaned or cleaned == "Usuário":
        return "?"
    return cleaned[0].upper()


def format_unread(count: int) -> str:
    """Texto do contador: '' com 0 (sem contador), o número até 99 e '99+' acima."""
    if not _is_int(count) or count <= 0:
        return ""
    if count > UNREAD_DISPLAY_MAX:
        return f"{UNREAD_DISPLAY_MAX}+"
    return str(count)


def unread_label(count: int) -> str:
    """Rótulo acessível do contador, com o número real (singular ou plural)."""
    if not _is_int(count) or count <= 0:
        return ""
    if count == 1:
        return "1 mensagem não lida"
    return f"{count} mensagens não lidas"


def messages_link_label(count: int) -> str:
    """Rótulo acessível do link “Mensagens” da home."""
    if not _is_int(count) or count <= 0:
        return "Mensagens"
    if count == 1:
        return "Mensagens, 1 não lida"
    return f"Mensagens, {count} não lidas"


def _with_unread(item: dict[str, Any], count: int) -> dict[str, Any]:
    """Cópia do item com o contador e os textos já formatados para a tela."""
    updated = dict(item)
    updated["unread_count"] = count
    updated["unread_text"] = format_unread(count)
    updated["unread_label"] = unread_label(count)
    return updated


def day_label(created_at_ms: object, now_ms: float) -> str:
    """'Hoje', 'Ontem' ou dd/mm/aaaa, no fuso de Brasília."""
    if not _is_int(created_at_ms) and not isinstance(created_at_ms, float):
        return ""
    day = datetime.fromtimestamp(created_at_ms / 1000, tz=BRASILIA).date()
    today = datetime.fromtimestamp(now_ms / 1000, tz=BRASILIA).date()
    if day == today:
        return "Hoje"
    if day == today - timedelta(days=1):
        return "Ontem"
    return day.strftime("%d/%m/%Y")


def time_label(created_at_ms: object) -> str:
    """Horário de envio HH:MM, no fuso de Brasília (mesma regra do day_label)."""
    if not _is_int(created_at_ms) and not isinstance(created_at_ms, float):
        return ""
    moment = datetime.fromtimestamp(created_at_ms / 1000, tz=BRASILIA)
    return moment.strftime("%H:%M")


def _chat_endpoint(path: str) -> str:
    try:
        return _api_endpoint(CATALOG_API_ENV, path)
    except DonationServiceError:
        raise ChatServiceError from None


def _raise_for_chat_status(response: httpx.Response) -> None:
    if response.status_code == 401:
        raise ChatUnauthorizedError
    if response.status_code == 404:
        raise ChatNotFoundError
    if response.status_code == 400:
        raise ChatInvalidMessageError
    if response.status_code == 429:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        raise ChatRateLimitError(classify_rate_limit(payload))
    if response.status_code != 200:
        raise ChatServiceError


def _json(response: httpx.Response) -> object:
    try:
        return response.json()
    except ValueError:
        raise ChatServiceError from None


def _parse_conversation(
    payload: object, *, require_unread: bool = False
) -> dict[str, Any]:
    """Item de conversa. O unread_count é obrigatório nos itens da lista; o
    start não o devolve, e a conversa iniciada fica com 0."""
    if not isinstance(payload, dict):
        raise ChatServiceError
    unread = payload.get("unread_count", None if require_unread else 0)
    if not _is_int(unread) or unread < 0:
        raise ChatServiceError
    conversation_id = payload.get("conversation_id")
    donation_id = payload.get("donation_id")
    name = payload.get("other_user_first_name")
    title = payload.get("donation_title")
    status = payload.get("donation_status")
    last_message_at = payload.get("last_message_at")
    if (
        not _is_int(conversation_id)
        or conversation_id <= 0
        or not _is_int(donation_id)
        or not isinstance(name, str)
        or not isinstance(title, str)
        or not isinstance(status, str)
        or not (last_message_at is None or _is_int(last_message_at))
    ):
        raise ChatServiceError
    # Só os campos esperados; qualquer outro campo da resposta é descartado.
    item = {
        "conversation_id": conversation_id,
        "donation_id": donation_id,
        "other_user_first_name": name,
        "donation_title": title,
        "donation_status": status,
        "last_message_at": last_message_at or 0,
        "initial": avatar_initial(name),
    }
    return _with_unread(item, unread)


def _parse_message(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ChatServiceError
    message_id = payload.get("id")
    sender = payload.get("sender_first_name")
    sent_by_me = payload.get("sent_by_me")
    text = payload.get("text")
    created_at = payload.get("created_at")
    # edited_at é obrigatório na resposta, mas vazio (nulo ou 0) sem edição.
    edited_at = payload.get("edited_at", False)
    if (
        not _is_int(message_id)
        or not isinstance(sender, str)
        or not isinstance(sent_by_me, bool)
        or not isinstance(text, str)
        or not _is_int(created_at)
        or not (edited_at is None or _is_int(edited_at))
    ):
        raise ChatServiceError
    return {
        "id": message_id,
        "sender_first_name": sender,
        "sent_by_me": sent_by_me,
        "text": text,
        "created_at": created_at,
        "edited_at": edited_at or 0,
    }


def _parse_messages_page(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ChatServiceError
    messages = payload.get("messages")
    title = payload.get("donation_title")
    status = payload.get("donation_status")
    has_older = payload.get("has_older")
    has_newer = payload.get("has_newer")
    other_last_read = payload.get("other_last_read_message_id")
    server_time = payload.get("server_time")
    edited = payload.get("edited_messages")
    if (
        not isinstance(messages, list)
        or not isinstance(title, str)
        or not isinstance(status, str)
        or not isinstance(has_older, bool)
        or not isinstance(has_newer, bool)
        or not _is_int(other_last_read)
        or other_last_read < 0
        or not _is_int(server_time)
        or not isinstance(edited, list)
    ):
        raise ChatServiceError
    return {
        "messages": [_parse_message(item) for item in messages],
        "donation_title": title,
        "donation_status": status,
        "has_older": has_older,
        "has_newer": has_newer,
        "other_last_read_message_id": other_last_read,
        "server_time": server_time,
        "edited_messages": [_parse_message(item) for item in edited],
    }


def _bearer(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}


# ---------------------------------------------------------------------------
# Cliente HTTP (cliente httpx injetado)
# ---------------------------------------------------------------------------


async def start_conversation(
    client: httpx.AsyncClient, auth_token: str, donation_id: int
) -> dict[str, Any]:
    endpoint = _chat_endpoint(START_PATH)
    try:
        response = await client.post(
            endpoint,
            json={"donation_id": donation_id},
            headers=_bearer(auth_token),
        )
    except httpx.HTTPError:
        raise ChatServiceError from None
    _raise_for_chat_status(response)
    return _parse_conversation(_json(response))


async def list_conversations(
    client: httpx.AsyncClient,
    auth_token: str,
    page: int = 1,
    limit: int = CONVERSATIONS_PAGE_LIMIT,
) -> dict[str, Any]:
    endpoint = _chat_endpoint(CONVERSATIONS_PATH)
    try:
        response = await client.get(
            endpoint,
            params={"page": page, "limit": limit},
            headers=_bearer(auth_token),
        )
    except httpx.HTTPError:
        raise ChatServiceError from None
    _raise_for_chat_status(response)
    payload = _json(response)
    if not isinstance(payload, dict):
        raise ChatServiceError
    items = payload.get("conversations")
    has_more = payload.get("has_more")
    if not isinstance(items, list) or not isinstance(has_more, bool):
        raise ChatServiceError
    return {
        "conversations": [
            _parse_conversation(item, require_unread=True) for item in items
        ],
        "has_more": has_more,
    }


async def fetch_unread_total(client: httpx.AsyncClient, auth_token: str) -> int:
    """Total de não lidas da pessoa; mesma classificação de erros do chat."""
    endpoint = _chat_endpoint(UNREAD_TOTAL_PATH)
    try:
        response = await client.get(endpoint, headers=_bearer(auth_token))
    except httpx.HTTPError:
        raise ChatServiceError from None
    _raise_for_chat_status(response)
    payload = _json(response)
    total = payload.get("unread_total") if isinstance(payload, dict) else None
    if not _is_int(total) or total < 0:
        raise ChatServiceError
    return total


async def fetch_messages(
    client: httpx.AsyncClient,
    auth_token: str,
    conversation_id: int,
    *,
    before_message_id: int | None = None,
    after_message_id: int | None = None,
    edited_since: int | None = None,
    limit: int = MESSAGES_PAGE_LIMIT,
) -> dict[str, Any]:
    if before_message_id is not None and after_message_id is not None:
        raise ValueError("Use somente um cursor de mensagens.")
    params: dict[str, int] = {"conversation_id": conversation_id, "limit": limit}
    if before_message_id is not None:
        params["before_message_id"] = before_message_id
    if after_message_id is not None:
        params["after_message_id"] = after_message_id
        # edited_since só tem efeito junto com after_message_id.
        if edited_since is not None:
            params["edited_since"] = edited_since
    endpoint = _chat_endpoint(MESSAGES_PATH)
    try:
        response = await client.get(
            endpoint, params=params, headers=_bearer(auth_token)
        )
    except httpx.HTTPError:
        raise ChatServiceError from None
    _raise_for_chat_status(response)
    return _parse_messages_page(_json(response))


async def send_message(
    client: httpx.AsyncClient,
    auth_token: str,
    conversation_id: int,
    text: str,
) -> dict[str, Any]:
    endpoint = _chat_endpoint(MESSAGES_PATH)
    try:
        response = await client.post(
            endpoint,
            json={"conversation_id": conversation_id, "message_text": text},
            headers=_bearer(auth_token),
        )
    except httpx.HTTPError:
        raise ChatServiceError from None
    _raise_for_chat_status(response)
    return _parse_message(_json(response))


async def edit_message(
    client: httpx.AsyncClient,
    auth_token: str,
    message_id: int,
    text: str,
) -> dict[str, Any]:
    """PATCH da mensagem própria; 400 com texto válido é o prazo encerrado."""
    endpoint = _chat_endpoint(MESSAGES_PATH)
    try:
        response = await client.patch(
            endpoint,
            json={"message_id": message_id, "message_text": text},
            headers=_bearer(auth_token),
        )
    except httpx.HTTPError:
        raise ChatServiceError from None
    _raise_for_chat_status(response)
    return _parse_message(_json(response))


# ---------------------------------------------------------------------------
# Lógica de estado (funções do módulo, testáveis com SimpleNamespace)
# ---------------------------------------------------------------------------


def _now() -> float:
    return time.time()


def _new_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=15.0)


def _decorate_messages(
    messages: list[dict[str, Any]],
    *,
    other_last_read: int = 0,
    read_only: bool = False,
    expired_ids: list[int] | tuple[int, ...] = (),
) -> list[dict[str, Any]]:
    """Ordena por id, remove repetidas, marca o primeiro de cada dia e calcula
    o “visto” (is_read), a edição (edited) e se o lápis aparece (editable)."""
    unique: dict[int, dict[str, Any]] = {}
    for message in messages:
        unique[message["id"]] = message
    now_ms = _now() * 1000
    edit_floor_ms = now_ms - EDIT_WINDOW_SECONDS * 1000
    expired = set(expired_ids)
    decorated: list[dict[str, Any]] = []
    previous_label = None
    for message_id in sorted(unique):
        message = dict(unique[message_id])
        label = day_label(message["created_at"], now_ms)
        message["day_label"] = label
        message["show_day"] = label != previous_label
        message["time_label"] = time_label(message["created_at"])
        mine = bool(message.get("sent_by_me"))
        # “Visto” só nas próprias mensagens.
        message["is_read"] = mine and message_id <= other_last_read
        message["edited"] = bool(message.get("edited_at"))
        # O backend decide; aqui só se esconde o lápis quando não faz sentido.
        message["editable"] = (
            mine
            and not read_only
            and message_id not in expired
            and message["created_at"] >= edit_floor_ms
        )
        previous_label = label
        decorated.append(message)
    return decorated


def _redecorate(state: Any, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _decorate_messages(
        messages,
        other_last_read=state.other_last_read_id,
        read_only=state.read_only,
        expired_ids=state.expired_edit_ids,
    )


def _apply_read_marker(state: Any, page: dict[str, Any]) -> None:
    """O “visto” só avança (duas abas lendo ao mesmo tempo não fazem piscar)."""
    state.other_last_read_id = max(
        state.other_last_read_id, page["other_last_read_message_id"]
    )


def _apply_edits(
    messages: list[dict[str, Any]], edited: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Troca texto e edited_at das mensagens já exibidas, pelo id."""
    by_id = {item["id"]: item for item in edited}
    updated: list[dict[str, Any]] = []
    for message in messages:
        change = by_id.get(message["id"])
        if change is None:
            updated.append(message)
        else:
            updated.append(
                {**message, "text": change["text"], "edited_at": change["edited_at"]}
            )
    return updated


def _end_edit(state: Any) -> None:
    state.editing_message_id = 0
    state.selected_message_id = 0


async def _save_edit(state: Any, text: str) -> rx.event.EventSpec | None:
    """Caminho de edição do formulário (o mesmo campo e o mesmo Enter)."""
    message_id = state.editing_message_id
    state.is_sending = True
    try:
        async with _new_client() as client:
            message = await edit_message(client, state.auth_token, message_id, text)
    except ChatUnauthorizedError:
        _clear_session(state)
        return rx.redirect("/login")
    except ChatInvalidMessageError:
        # O tamanho já foi validado antes: o 400 é o prazo encerrado.
        # O texto fica no campo, agora como rascunho de mensagem nova.
        state.send_error = EDIT_EXPIRED_MESSAGE
        state.expired_edit_ids = [*state.expired_edit_ids, message_id]
        _end_edit(state)
        state.chat_messages = _redecorate(state, state.chat_messages)
        return None
    except ChatNotFoundError:
        state.send_error = EDIT_NOT_FOUND_MESSAGE
        _end_edit(state)
        return None
    except ChatRateLimitError as error:
        state.send_error = rate_limit_message(error.kind)
        return None
    except ChatServiceError:
        state.send_error = EDIT_ERROR_MESSAGE
        return None
    finally:
        state.is_sending = False

    state.chat_messages = _redecorate(
        state, _apply_edits(state.chat_messages, [message])
    )
    _end_edit(state)
    return rx.set_value(MESSAGE_INPUT_ID, "")


def _clear_session(state: Any) -> None:
    state.auth_token = ""
    state.account_name = ""


def _reset_conversation(state: Any) -> None:
    state.active_conversation_id = 0
    state.active_other_name = ""
    state.active_donation_title = ""
    state.active_donation_status = ""
    state.chat_messages = []
    state.has_older = False
    state.is_loading_older = False
    state.read_only = False
    state.conversation_error = ""
    state.send_error = ""
    state.is_sending = False
    state.poll_paused_until = 0.0
    state.other_last_read_id = 0
    state.last_server_time = 0
    state.expired_edit_ids = []
    _end_edit(state)


def _merge_conversations(
    current: list[dict[str, Any]], new_items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    seen = {item["conversation_id"] for item in current}
    merged = list(current)
    for item in new_items:
        if item["conversation_id"] not in seen:
            seen.add(item["conversation_id"])
            merged.append(item)
    return merged


def _without_unread_for(
    items: list[dict[str, Any]], conversation_id: int
) -> list[dict[str, Any]]:
    """Zera o contador da conversa aberta: ela nunca mostra não lidas."""
    if not conversation_id:
        return list(items)
    return [
        _with_unread(item, 0)
        if item["conversation_id"] == conversation_id and item.get("unread_count")
        else item
        for item in items
    ]


def _merge_first_page(
    current: list[dict[str, Any]], first_page: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Página 1 nova no topo, na ordem dela; as já carregadas de páginas
    seguintes continuam abaixo, sem repetir."""
    on_first_page = {item["conversation_id"] for item in first_page}
    rest = [item for item in current if item["conversation_id"] not in on_first_page]
    return [*first_page, *rest]


def _set_unread_total(state: Any, total: int) -> None:
    state.unread_total = total
    state.unread_total_text = format_unread(total)
    state.unread_link_label = messages_link_label(total)


async def _load_list(state: Any, client: httpx.AsyncClient) -> None:
    state.list_error = ""
    try:
        result = await list_conversations(client, state.auth_token, page=1)
    except ChatRateLimitError as error:
        state.list_error = rate_limit_message(error.kind)
        return
    except (ChatServiceError, ChatNotFoundError, ChatInvalidMessageError):
        state.list_error = LIST_ERROR_MESSAGE
        return
    state.chat_conversations = _without_unread_for(
        result["conversations"], state.active_conversation_id
    )
    state.conversations_page = 1
    state.conversations_has_more = result["has_more"]


def _apply_page_metadata(state: Any, page: dict[str, Any]) -> None:
    state.active_donation_title = page["donation_title"]
    state.active_donation_status = page["donation_status"]
    if page["donation_status"] == DONATION_STATUS_COMPLETED:
        state.read_only = True


def _other_name_for(state: Any, conversation_id: int, messages: list[dict[str, Any]]) -> str:
    for item in state.chat_conversations:
        if item["conversation_id"] == conversation_id:
            return item["other_user_first_name"]
    for message in messages:
        if not message["sent_by_me"]:
            return message["sender_first_name"]
    return ""


async def _open_conversation(
    state: Any, client: httpx.AsyncClient, conversation_id: int
) -> None:
    _reset_conversation(state)
    state.active_conversation_id = conversation_id
    # O contador some na hora; a leitura no Xano acontece no GET abaixo.
    state.chat_conversations = _without_unread_for(
        state.chat_conversations, conversation_id
    )
    try:
        page = await fetch_messages(client, state.auth_token, conversation_id)
    except ChatNotFoundError:
        state.active_conversation_id = 0
        state.conversation_error = CONVERSATION_NOT_FOUND_MESSAGE
        return
    except ChatRateLimitError as error:
        state.conversation_error = rate_limit_message(error.kind)
        return
    except (ChatServiceError, ChatInvalidMessageError):
        state.conversation_error = MESSAGES_ERROR_MESSAGE
        return
    _apply_page_metadata(state, page)
    _apply_read_marker(state, page)
    state.last_server_time = page["server_time"]
    state.chat_messages = _redecorate(state, page["messages"])
    state.has_older = page["has_older"]
    state.active_other_name = _other_name_for(state, conversation_id, page["messages"])
    state.mobile_view = "conversation"


def _parse_route_conversation_id(value: object) -> int | None:
    if not isinstance(value, str) or not value.isdigit():
        return None
    conversation_id = int(value)
    return conversation_id if conversation_id > 0 else None


def _move_conversation_to_top(state: Any, conversation_id: int, timestamp: int) -> None:
    items = list(state.chat_conversations)
    for index, item in enumerate(items):
        if item["conversation_id"] == conversation_id:
            updated = dict(item)
            updated["last_message_at"] = timestamp
            items.pop(index)
            state.chat_conversations = [updated, *items]
            return


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------


class ChatState(LoginState):
    chat_conversations: list[dict[str, Any]] = []
    conversations_page: int = 1
    conversations_has_more: bool = False
    list_error: str = ""
    is_loading_list: bool = False

    active_conversation_id: int = 0
    active_other_name: str = ""
    active_donation_title: str = ""
    active_donation_status: str = ""
    chat_messages: list[dict[str, Any]] = []
    has_older: bool = False
    is_loading_older: bool = False
    read_only: bool = False
    conversation_error: str = ""

    send_error: str = ""
    is_sending: bool = False
    # Pausa compartilhada pelas consultas automáticas de mensagens e da lista.
    poll_paused_until: float = 0.0
    mobile_view: str = "list"

    # “Visto” e edição da conversa aberta.
    other_last_read_id: int = 0
    last_server_time: int = 0
    editing_message_id: int = 0
    selected_message_id: int = 0
    expired_edit_ids: list[int] = []

    # Total de não lidas do link “Mensagens” da home.
    unread_total: int = 0
    unread_total_text: str = ""
    unread_link_label: str = "Mensagens"

    @rx.event
    async def load_unread_total(self) -> None:
        """Uma consulta por carregamento da home; sem token, nenhuma.

        Qualquer erro, inclusive 401 (o load_account já trata o token
        recusado), deixa o total em 0, sem aviso.
        """
        if not self.auth_token:
            _set_unread_total(self, 0)
            return
        try:
            async with _new_client() as client:
                total = await fetch_unread_total(client, self.auth_token)
        except ChatError:
            _set_unread_total(self, 0)
            return
        _set_unread_total(self, total)

    @rx.event
    async def load_chat(self) -> rx.event.EventSpec | None:
        self.chat_conversations = []
        self.conversations_page = 1
        self.conversations_has_more = False
        self.list_error = ""
        self.mobile_view = "list"
        _reset_conversation(self)
        if not self.auth_token:
            return rx.redirect("/login")

        route_value = self.router.page.params.get("conversa")
        self.is_loading_list = True
        try:
            async with _new_client() as client:
                await _load_list(self, client)
                if route_value is not None:
                    conversation_id = _parse_route_conversation_id(route_value)
                    if conversation_id is None:
                        self.conversation_error = CONVERSATION_NOT_FOUND_MESSAGE
                    else:
                        await _open_conversation(self, client, conversation_id)
        except ChatUnauthorizedError:
            _clear_session(self)
            return rx.redirect("/login")
        finally:
            self.is_loading_list = False
        return None

    @rx.event
    async def refresh_conversations(self) -> rx.event.EventSpec | None:
        if not self.auth_token:
            return rx.redirect("/login")
        self.is_loading_list = True
        try:
            async with _new_client() as client:
                await _load_list(self, client)
        except ChatUnauthorizedError:
            _clear_session(self)
            return rx.redirect("/login")
        finally:
            self.is_loading_list = False
        return None

    @rx.event
    async def select_conversation(
        self, conversation_id: int
    ) -> rx.event.EventSpec | None:
        if not self.auth_token:
            return rx.redirect("/login")
        was_editing = bool(self.editing_message_id)
        try:
            async with _new_client() as client:
                await _open_conversation(self, client, int(conversation_id))
        except ChatUnauthorizedError:
            _clear_session(self)
            return rx.redirect("/login")
        # A edição em andamento termina ao trocar de conversa.
        if was_editing:
            return rx.set_value(MESSAGE_INPUT_ID, "")
        return None

    @rx.event
    async def load_older_messages(self) -> rx.event.EventSpec | None:
        if (
            not self.auth_token
            or not self.active_conversation_id
            or not self.has_older
            or self.is_loading_older
            or not self.chat_messages
        ):
            return None
        oldest_id = self.chat_messages[0]["id"]
        self.is_loading_older = True
        self.conversation_error = ""
        try:
            async with _new_client() as client:
                page = await fetch_messages(
                    client,
                    self.auth_token,
                    self.active_conversation_id,
                    before_message_id=oldest_id,
                )
        except ChatUnauthorizedError:
            _clear_session(self)
            return rx.redirect("/login")
        except ChatRateLimitError as error:
            self.conversation_error = rate_limit_message(error.kind)
            return None
        except ChatError:
            self.conversation_error = MESSAGES_ERROR_MESSAGE
            return None
        finally:
            self.is_loading_older = False
        _apply_page_metadata(self, page)
        # last_server_time não muda aqui: as editadas vêm só da consulta
        # automática, e trocar o horário faria perder edições entre as duas.
        _apply_read_marker(self, page)
        self.chat_messages = _redecorate(self, [*page["messages"], *self.chat_messages])
        self.has_older = page["has_older"]
        return None

    @rx.event
    async def load_more_conversations(self) -> rx.event.EventSpec | None:
        if not self.auth_token:
            return rx.redirect("/login")
        if not self.conversations_has_more or self.is_loading_list:
            return None
        next_page = self.conversations_page + 1
        self.is_loading_list = True
        self.list_error = ""
        try:
            async with _new_client() as client:
                result = await list_conversations(
                    client, self.auth_token, page=next_page
                )
        except ChatUnauthorizedError:
            _clear_session(self)
            return rx.redirect("/login")
        except ChatRateLimitError as error:
            self.list_error = rate_limit_message(error.kind)
            return None
        except ChatError:
            self.list_error = LIST_ERROR_MESSAGE
            return None
        finally:
            self.is_loading_list = False
        self.chat_conversations = _without_unread_for(
            _merge_conversations(self.chat_conversations, result["conversations"]),
            self.active_conversation_id,
        )
        self.conversations_page = next_page
        self.conversations_has_more = result["has_more"]
        return None

    @rx.event
    def back_to_list(self) -> None:
        self.mobile_view = "list"

    @rx.event
    async def send_message(
        self, form_data: dict[str, Any]
    ) -> rx.event.EventSpec | None:
        text = str(form_data.get("message_text", "")).strip()
        if (
            not text
            or not self.active_conversation_id
            or self.read_only
            or self.is_sending
        ):
            return None
        if not self.auth_token:
            return rx.redirect("/login")
        self.send_error = ""
        if len(text) > MAX_MESSAGE_LENGTH:
            self.send_error = SEND_INVALID_MESSAGE
            return None
        if self.editing_message_id:
            return await _save_edit(self, text)

        self.is_sending = True
        try:
            async with _new_client() as client:
                message = await send_message(
                    client, self.auth_token, self.active_conversation_id, text
                )
        except ChatUnauthorizedError:
            _clear_session(self)
            return rx.redirect("/login")
        except ChatInvalidMessageError:
            self.send_error = SEND_INVALID_MESSAGE
            return None
        except ChatNotFoundError:
            self.send_error = SEND_NOT_FOUND_MESSAGE
            self.read_only = True
            return None
        except ChatRateLimitError as error:
            self.send_error = rate_limit_message(error.kind)
            return None
        except ChatServiceError:
            self.send_error = SEND_ERROR_MESSAGE
            return None
        finally:
            self.is_sending = False

        self.chat_messages = _redecorate(self, [*self.chat_messages, message])
        _move_conversation_to_top(
            self, self.active_conversation_id, message["created_at"]
        )
        # Limpa o campo só depois do sucesso.
        return rx.set_value(MESSAGE_INPUT_ID, "")

    @rx.event
    def start_edit(self, message_id: int) -> list[rx.event.EventSpec] | None:
        message = next(
            (m for m in self.chat_messages if m["id"] == int(message_id)), None
        )
        if message is None or not message.get("editable") or self.is_sending:
            return None
        self.editing_message_id = message["id"]
        self.selected_message_id = 0
        self.send_error = ""
        return [
            rx.set_value(MESSAGE_INPUT_ID, message["text"]),
            rx.set_focus(MESSAGE_INPUT_ID),
        ]

    @rx.event
    def cancel_edit(self) -> rx.event.EventSpec | None:
        if not self.editing_message_id:
            return None
        _end_edit(self)
        self.send_error = ""
        return rx.set_value(MESSAGE_INPUT_ID, "")

    @rx.event
    def composer_key_down(self, key: str) -> rx.event.EventSpec | None:
        # Esc cancela a edição; as outras teclas não fazem nada aqui.
        if key == "Escape" and self.editing_message_id:
            return ChatState.cancel_edit.fn(self)
        return None

    @rx.event
    def toggle_message_selection(self, message_id: int) -> None:
        """Toque na bolha (celular): mostra ou esconde o lápis dela."""
        message_id = int(message_id)
        message = next((m for m in self.chat_messages if m["id"] == message_id), None)
        if message is None or not message.get("editable"):
            self.selected_message_id = 0
            return
        self.selected_message_id = (
            0 if self.selected_message_id == message_id else message_id
        )

    @rx.event
    def poll_tick(self, _value: Any = None) -> rx.event.EventSpec | None:
        if (
            not self.auth_token
            or not self.active_conversation_id
            or _now() < self.poll_paused_until
        ):
            return None
        return rx.call_script(
            "document.visibilityState",
            callback=ChatState.poll_if_visible,
        )

    @rx.event
    async def poll_if_visible(
        self, visibility: str
    ) -> rx.event.EventSpec | None:
        if (
            visibility != "visible"
            or not self.auth_token
            or not self.active_conversation_id
            or _now() < self.poll_paused_until
        ):
            return None
        conversation_id = self.active_conversation_id
        last_id = self.chat_messages[-1]["id"] if self.chat_messages else None
        try:
            async with _new_client() as client:
                if last_id is None:
                    page = await fetch_messages(
                        client, self.auth_token, conversation_id
                    )
                else:
                    page = await fetch_messages(
                        client,
                        self.auth_token,
                        conversation_id,
                        after_message_id=last_id,
                        edited_since=self.last_server_time or None,
                        limit=POLL_MESSAGES_LIMIT,
                    )
        except ChatUnauthorizedError:
            _clear_session(self)
            return rx.redirect("/login")
        except ChatRateLimitError:
            # Pausa silenciosa: sem aviso bloqueante.
            self.poll_paused_until = _now() + POLL_PAUSE_SECONDS
            return None
        except ChatError:
            return None
        if conversation_id != self.active_conversation_id:
            return None
        _apply_page_metadata(self, page)
        _apply_read_marker(self, page)
        self.last_server_time = page["server_time"]
        # Edições das já exibidas, mensagens novas, ✓✓ e lápis: tudo desta
        # mesma resposta, sem requisição a mais.
        messages = _apply_edits(self.chat_messages, page["edited_messages"])
        self.chat_messages = _redecorate(self, [*messages, *page["messages"]])
        if page["messages"] and last_id is None:
            self.has_older = page["has_older"]
        # A doação foi concluída durante a edição: a edição termina.
        if self.read_only and self.editing_message_id:
            _end_edit(self)
            return rx.set_value(MESSAGE_INPUT_ID, "")
        return None

    @rx.event
    def list_poll_tick(self, _value: Any = None) -> rx.event.EventSpec | None:
        if (
            not self.auth_token
            or self.is_loading_list
            or _now() < self.poll_paused_until
        ):
            return None
        return rx.call_script(
            "document.visibilityState",
            callback=ChatState.list_poll_if_visible,
        )

    @rx.event
    async def list_poll_if_visible(
        self, visibility: str
    ) -> rx.event.EventSpec | None:
        """Atualiza a página 1 da lista (contadores, ordem e conversas novas)."""
        if (
            visibility != "visible"
            or not self.auth_token
            or self.is_loading_list
            or _now() < self.poll_paused_until
        ):
            return None
        try:
            async with _new_client() as client:
                result = await list_conversations(client, self.auth_token, page=1)
        except ChatUnauthorizedError:
            _clear_session(self)
            return rx.redirect("/login")
        except ChatRateLimitError:
            # Mesma pausa silenciosa das mensagens.
            self.poll_paused_until = _now() + POLL_PAUSE_SECONDS
            return None
        except ChatError:
            return None
        self.chat_conversations = _without_unread_for(
            _merge_first_page(self.chat_conversations, result["conversations"]),
            self.active_conversation_id,
        )
        # Com páginas seguintes já carregadas, has_more continua o da última.
        if self.conversations_page <= 1:
            self.conversations_has_more = result["has_more"]
        return None


# ---------------------------------------------------------------------------
# Página /chat
# ---------------------------------------------------------------------------
# Todo conteúdo vindo do chat (mensagens, nomes, títulos) é renderizado com
# rx.text: o React escapa o texto. Nunca usar rx.html nem markdown aqui.


def _show_on_mobile_when(view: str) -> rx.Var:
    """Em telas estreitas mostra só a lista ou só a conversa; do md em diante, as duas."""
    return rx.breakpoints(
        initial=rx.cond(ChatState.mobile_view == view, "flex", "none"),
        md="flex",
    )


def _avatar(initial: rx.Var, size: str = "38px") -> rx.Component:
    return rx.center(
        rx.text(initial, color="white", font_weight="700", font_size="1rem"),
        width=size,
        height=size,
        min_width=size,
        border_radius="50%",
        background=GREEN_AVATAR,
        aria_hidden="true",
    )


def unread_badge(
    text: rx.Var | str,
    label: rx.Var | str | None = None,
    background: str | None = None,
    **props: Any,
) -> rx.Component:
    """Círculo de não lidas: #007A42 (ou `background`) com número branco
    (contraste AA).

    Com `label`, o círculo é lido como imagem com esse rótulo; sem ele, fica
    oculto do leitor de tela (o rótulo está no elemento em volta).
    """
    accessibility: dict[str, Any] = (
        {"role": "img", "aria_label": label}
        if label is not None
        else {"aria_hidden": "true"}
    )
    return rx.center(
        rx.text(
            text,
            color="white",
            font_weight="700",
            font_size="0.7rem",
            line_height="1",
        ),
        class_name="chat-unread-badge",
        min_width="20px",
        height="20px",
        padding="0 6px",
        border_radius="999px",
        background=background or GREEN_BUTTON,
        flex_shrink="0",
        **accessibility,
        **props,
    )


# Botão flutuante “Mensagens” (canto inferior direito).
CHAT_FAB_SIZE = "56px"
CHAT_FAB_OFFSET = rx.breakpoints(initial="16px", md="24px")
# Espaço livre no fim das páginas com o botão: botão + as duas margens, para
# que nada fique coberto com a página rolada até o fim.
CHAT_FAB_CLEARANCE = rx.breakpoints(initial="88px", md="104px")
CHAT_FAB_SHADOW = "0 4px 12px rgba(0, 0, 0, 0.2)"
# Branco sobre #C62828 dá 5,6:1 (AA).
CHAT_FAB_BADGE_RED = "#C62828"


def chat_fab() -> rx.Component:
    """Entrada no chat: com login abre /chat; sem login vai para /login (e o
    load_unread_total não consulta nada). O total fica no rótulo do link, então
    o contador é oculto do leitor de tela. Realce e prefers-reduced-motion
    ficam em assets/chat.css (.chat-fab)."""
    logged_in = LoginState.auth_token != ""
    return rx.link(
        rx.icon("message-circle", size=26, color="white", aria_hidden="true"),
        rx.cond(
            logged_in & (ChatState.unread_total > 0),
            unread_badge(
                ChatState.unread_total_text,
                background=CHAT_FAB_BADGE_RED,
                position="absolute",
                top="-4px",
                right="-4px",
                border="2px solid white",
            ),
            rx.fragment(),
        ),
        href=rx.cond(logged_in, "/chat", "/login"),
        aria_label=rx.cond(logged_in, ChatState.unread_link_label, "Mensagens"),
        title="Mensagens",
        class_name="chat-fab",
        position="fixed",
        bottom=CHAT_FAB_OFFSET,
        right=CHAT_FAB_OFFSET,
        z_index="20",
        display="flex",
        align_items="center",
        justify_content="center",
        width=CHAT_FAB_SIZE,
        height=CHAT_FAB_SIZE,
        border_radius="999px",
        background=GREEN_BUTTON,
        box_shadow=CHAT_FAB_SHADOW,
    )


def back_link_header(
    href: str | rx.Var, label: str, color: str = GREEN_TEXT
) -> rx.Component:
    """Cabeçalho branco com um link de voltar na linha do logotipo.

    Como nos frames chat-1, detalhes-doacao e perfil-doador do Figma: o link
    fica à esquerda, na mesma linha do logotipo centralizado, sem faixa
    própria. A coluna da direita fica vazia para manter o logotipo no centro.
    Em telas estreitas aparece só a seta, com o rótulo acessível e 44 px de
    área de toque.
    """
    return rx.grid(
        rx.link(
            rx.hstack(
                rx.icon("chevron-left", size=20),
                rx.text(
                    label,
                    display=rx.breakpoints(initial="none", sm="inline"),
                ),
                spacing="1",
                align="center",
            ),
            href=href,
            color=color,
            font_weight="600",
            aria_label=label,
            justify_self="start",
            # Área de toque confortável mesmo quando só a seta aparece.
            display="inline-flex",
            align_items="center",
            min_height="44px",
            min_width="44px",
        ),
        rx.link(
            rx.image(
                src="/logo.svg",
                alt="DoaFácil",
                width="140px",
                height="52px",
                object_fit="contain",
            ),
            href="/",
        ),
        rx.box(),
        grid_template_columns="1fr auto 1fr",
        align_items="center",
        width="100%",
        background="white",
        padding="0.25rem 1rem",
        box_shadow="0 2px 8px rgba(39, 39, 39, 0.06)",
    )


def back_home_header() -> rx.Component:
    """“Voltar ao início” (para /) em #166B3B. Usado no /chat e no detalhe."""
    return back_link_header("/", "Voltar ao início", GREEN_TEXT)


def _header() -> rx.Component:
    return back_home_header()


def _conversation_item(item: rx.Var) -> rx.Component:
    selected = ChatState.active_conversation_id == item["conversation_id"]
    return rx.el.button(
        rx.hstack(
            _avatar(item["initial"]),
            rx.vstack(
                rx.text(
                    item["other_user_first_name"],
                    color=TEXT_DARK,
                    font_weight="700",
                    font_size="0.85rem",
                ),
                rx.text(
                    item["donation_title"],
                    color=TEXT_MUTED,
                    font_size="0.75rem",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                    max_width="100%",
                ),
                spacing="0",
                align="start",
                min_width="0",
                flex="1",
            ),
            # Contador de não lidas à direita; oculto com 0.
            rx.cond(
                item["unread_text"] != "",
                unread_badge(item["unread_text"], item["unread_label"]),
                rx.fragment(),
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        type="button",
        on_click=ChatState.select_conversation(item["conversation_id"]),
        aria_current=rx.cond(selected, "true", "false"),
        width="100%",
        min_height="54px",
        padding="8px 16px",
        text_align="left",
        cursor="pointer",
        border="none",
        border_bottom=f"1px solid {LIGHT_BORDER}",
        background=rx.cond(selected, "#F2F2F2", "white"),
        _hover={"background": "#F7F8F7"},
    )


def _conversation_list() -> rx.Component:
    return rx.flex(
        rx.hstack(
            rx.text("Conversas", color=TEXT_DARK, font_weight="700"),
            rx.spacer(),
            rx.icon_button(
                rx.icon("refresh-cw", size=16),
                on_click=ChatState.refresh_conversations,
                disabled=ChatState.is_loading_list,
                variant="ghost",
                color=GREEN_TEXT,
                aria_label="Atualizar conversas",
                type="button",
            ),
            align="center",
            width="100%",
            min_height="52px",
            padding="0 16px",
            border_bottom=f"2px solid {GREEN_BORDER}",
        ),
        rx.cond(
            ChatState.list_error != "",
            rx.vstack(
                rx.text(
                    ChatState.list_error,
                    role="alert",
                    color="#9B2C2C",
                    font_size="0.85rem",
                ),
                rx.button(
                    "Tentar novamente",
                    type="button",
                    on_click=ChatState.refresh_conversations,
                    variant="outline",
                    color=GREEN_TEXT,
                    size="1",
                ),
                padding="10px 16px",
                spacing="2",
                align="start",
            ),
            rx.fragment(),
        ),
        rx.box(
            rx.foreach(ChatState.chat_conversations, _conversation_item),
            rx.cond(
                (ChatState.chat_conversations.length() == 0)
                & ~ChatState.is_loading_list
                & (ChatState.list_error == ""),
                rx.text(
                    EMPTY_LIST_MESSAGE,
                    color=TEXT_MUTED,
                    font_size="0.9rem",
                    padding="16px",
                ),
                rx.fragment(),
            ),
            rx.cond(
                ChatState.conversations_has_more,
                rx.box(
                    rx.button(
                        "Carregar mais conversas",
                        type="button",
                        on_click=ChatState.load_more_conversations,
                        disabled=ChatState.is_loading_list,
                        variant="ghost",
                        color=GREEN_TEXT,
                        width="100%",
                    ),
                    padding="8px",
                ),
                rx.fragment(),
            ),
            overflow_y="auto",
            flex="1",
        ),
        direction="column",
        display=_show_on_mobile_when("list"),
        width=rx.breakpoints(initial="100%", md="280px"),
        min_width=rx.breakpoints(initial="100%", md="280px"),
        background="white",
        border_right=rx.breakpoints(initial="none", md=f"2px solid {GREEN_BORDER}"),
        height="100%",
    )


def _day_separator(message: rx.Var) -> rx.Component:
    return rx.cond(
        message["show_day"],
        rx.center(
            rx.text(
                message["day_label"],
                color="white",
                background=GREEN_BUTTON,
                font_weight="700",
                font_size="0.7rem",
                padding="3px 10px",
                border_radius="999px",
            ),
            width="100%",
            padding="8px 0",
        ),
        rx.fragment(),
    )


def _read_status(message: rx.Var) -> rx.Component:
    """✓ cinza (enviada) ou ✓✓ verde (lida), só nas próprias mensagens."""
    return rx.cond(
        message["sent_by_me"],
        rx.cond(
            message["is_read"],
            rx.el.span(
                rx.icon("check-check", size=14, color=GREEN_BUTTON, aria_hidden="true"),
                role="img",
                aria_label=READ_STATUS_LABEL,
                class_name="chat-read-status",
                display="inline-flex",
            ),
            rx.el.span(
                rx.icon("check", size=14, color=TEXT_TIME, aria_hidden="true"),
                role="img",
                aria_label=SENT_STATUS_LABEL,
                class_name="chat-read-status",
                display="inline-flex",
            ),
        ),
        rx.fragment(),
    )


def _edit_button(message: rx.Var) -> rx.Component:
    """Lápis: aparece no hover (computador), no foco do teclado ou com a bolha
    selecionada por toque (celular); a visibilidade fica no assets/chat.css."""
    return rx.cond(
        message["editable"],
        rx.icon_button(
            rx.icon("pencil", size=14),
            type="button",
            on_click=ChatState.start_edit(message["id"]),
            class_name="chat-edit-btn",
            aria_label=EDIT_BUTTON_LABEL,
            title=EDIT_BUTTON_LABEL,
            variant="ghost",
            size="1",
            color=GREEN_TEXT,
        ),
        rx.fragment(),
    )


def _message_bubble(message: rx.Var) -> rx.Component:
    mine = message["sent_by_me"]
    selected = ChatState.selected_message_id == message["id"]
    return rx.fragment(
        _day_separator(message),
        rx.flex(
            rx.hstack(
                _edit_button(message),
                rx.box(
                    rx.text(
                        message["text"],
                        color=rx.cond(mine, "white", TEXT_DARK),
                        font_weight="700",
                        font_size="1rem",
                        white_space="pre-wrap",
                        word_break="break-word",
                    ),
                    # Toque na bolha (celular) mostra ou esconde o lápis.
                    on_click=ChatState.toggle_message_selection(message["id"]),
                    background=rx.cond(mine, GREEN_BUTTON, BUBBLE_OTHER),
                    padding="10px",
                    border_radius="8px",
                    max_width="100%",
                    box_shadow=rx.cond(
                        mine,
                        "2px 2px 1px rgba(0, 0, 0, 0.25)",
                        "-2px 2px 1px rgba(0, 0, 0, 0.25)",
                    ),
                ),
                spacing="1",
                align="center",
                justify=rx.cond(mine, "end", "start"),
                max_width="min(450px, 85%)",
            ),
            # Linha do horário, fora da bolha e do mesmo lado dela:
            # horário, “(editada)” e o “visto” nas próprias mensagens.
            rx.hstack(
                rx.text(
                    message["time_label"],
                    class_name="chat-message-time",
                    color=TEXT_TIME,
                    font_size="0.7rem",
                ),
                rx.cond(
                    message["edited"],
                    rx.text(
                        EDITED_LABEL,
                        class_name="chat-message-edited",
                        color=TEXT_TIME,
                        font_size="0.7rem",
                    ),
                    rx.fragment(),
                ),
                _read_status(message),
                spacing="1",
                align="center",
                margin_top="2px",
            ),
            class_name="chat-bubble-row",
            custom_attrs={"data-selected": rx.cond(selected, "true", "false")},
            direction="column",
            align=rx.cond(mine, "end", "start"),
            width="100%",
        ),
    )


def _conversation_header() -> rx.Component:
    return rx.hstack(
        rx.el.button(
            rx.hstack(
                rx.icon("chevron-left", size=18),
                rx.text("Voltar às conversas", font_size="0.85rem"),
                spacing="1",
                align="center",
            ),
            type="button",
            on_click=ChatState.back_to_list,
            display=rx.breakpoints(initial="flex", md="none"),
            color=GREEN_TEXT,
            background="transparent",
            border="none",
            cursor="pointer",
            padding="0",
        ),
        rx.cond(
            ChatState.active_conversation_id > 0,
            rx.vstack(
                rx.text(
                    ChatState.active_other_name,
                    color=TEXT_DARK,
                    font_weight="700",
                    font_size="1rem",
                ),
                rx.text(
                    ChatState.active_donation_title,
                    color=TEXT_MUTED,
                    font_size="0.8rem",
                ),
                spacing="0",
                align="center",
                flex="1",
            ),
            rx.spacer(),
        ),
        align="center",
        width="100%",
        min_height="52px",
        padding="0 24px",
        background="white",
        border_bottom=f"2px solid {GREEN_BORDER}",
    )


def _messages_area() -> rx.Component:
    return rx.auto_scroll(
        rx.cond(
            ChatState.has_older,
            rx.center(
                rx.button(
                    "Carregar anteriores",
                    type="button",
                    on_click=ChatState.load_older_messages,
                    disabled=ChatState.is_loading_older,
                    variant="outline",
                    color=GREEN_TEXT,
                    background="white",
                    size="1",
                ),
                width="100%",
                padding="4px 0 8px",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ChatState.conversation_error != "",
            rx.text(
                ChatState.conversation_error,
                role="alert",
                color="#9B2C2C",
                text_align="center",
                width="100%",
                padding="8px",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ChatState.active_conversation_id == 0,
            rx.cond(
                ChatState.conversation_error == "",
                rx.center(
                    rx.text(NO_CONVERSATION_MESSAGE, color=TEXT_MUTED),
                    width="100%",
                    height="100%",
                ),
                rx.fragment(),
            ),
            rx.cond(
                (ChatState.chat_messages.length() == 0)
                & (ChatState.conversation_error == ""),
                rx.center(
                    rx.text(EMPTY_CONVERSATION_MESSAGE, color=TEXT_MUTED),
                    width="100%",
                    height="100%",
                ),
                rx.vstack(
                    rx.foreach(ChatState.chat_messages, _message_bubble),
                    spacing="3",
                    width="100%",
                ),
            ),
        ),
        flex="1",
        width="100%",
        padding="16px 24px",
        background=CREAM,
        overflow_y="auto",
        overflow_anchor="auto",
    )


def _composer() -> rx.Component:
    return rx.vstack(
        rx.cond(
            ChatState.read_only,
            rx.text(
                READ_ONLY_MESSAGE,
                role="status",
                color=GREEN_TEXT,
                background="#E8F5EC",
                padding="0.5rem 0.75rem",
                border_radius="6px",
                font_size="0.85rem",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ChatState.send_error != "",
            rx.text(
                ChatState.send_error,
                role="alert",
                color="#9B2C2C",
                font_size="0.85rem",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ChatState.editing_message_id > 0,
            rx.hstack(
                rx.icon("pencil", size=14, aria_hidden="true"),
                rx.text(EDITING_LABEL, font_weight="700", font_size="0.85rem"),
                rx.text(
                    "(Esc cancela)",
                    color=TEXT_MUTED,
                    font_size="0.75rem",
                    display=rx.breakpoints(initial="none", md="inline"),
                ),
                role="status",
                class_name="chat-editing-banner",
                color=GREEN_TEXT,
                background="#E8F5EC",
                padding="0.35rem 0.75rem",
                border_radius="6px",
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.form(
            rx.hstack(
                rx.input(
                    name="message_text",
                    id=MESSAGE_INPUT_ID,
                    placeholder=MESSAGE_PLACEHOLDER,
                    max_length=MAX_MESSAGE_LENGTH,
                    disabled=ChatState.read_only,
                    # Esc cancela a edição (nenhuma requisição ao Xano).
                    on_key_down=ChatState.composer_key_down,
                    aria_label=rx.cond(
                        ChatState.editing_message_id > 0, EDITING_LABEL, "Mensagem"
                    ),
                    # O prop auto_complete só aceita booleano e não gera
                    # autocomplete="off"; o atributo vai direto no campo.
                    custom_attrs={"autoComplete": "off"},
                    width="100%",
                    height="40px",
                    background="white",
                    color=TEXT_DARK,
                    border=f"1px solid {GREEN_BORDER}",
                    border_radius="4px",
                ),
                rx.cond(
                    ChatState.editing_message_id > 0,
                    rx.button(
                        "Cancelar",
                        type="button",
                        on_click=ChatState.cancel_edit,
                        variant="outline",
                        color=GREEN_TEXT,
                        background="white",
                        height="40px",
                    ),
                    rx.fragment(),
                ),
                rx.button(
                    rx.cond(
                        ChatState.editing_message_id > 0,
                        rx.icon("check", size=16),
                        rx.icon("send", size=16),
                    ),
                    rx.cond(ChatState.editing_message_id > 0, "Salvar", "Enviar"),
                    type="submit",
                    disabled=ChatState.is_sending | ChatState.read_only,
                    background=GREEN_BUTTON,
                    color="white",
                    _hover={"background": GREEN_BUTTON_HOVER},
                    height="40px",
                ),
                spacing="2",
                width="100%",
                align="center",
            ),
            on_submit=ChatState.send_message,
            reset_on_submit=False,
            width="100%",
        ),
        spacing="2",
        width="100%",
        padding="8px 24px",
        background=CREAM,
    )


def _conversation_panel() -> rx.Component:
    return rx.flex(
        _conversation_header(),
        _messages_area(),
        rx.cond(
            ChatState.active_conversation_id > 0,
            _composer(),
            rx.fragment(),
        ),
        # Atualização automática: só existe com uma conversa aberta; ao fechar
        # a conversa ou sair da página, o componente desmonta e o timer para.
        rx.cond(
            ChatState.active_conversation_id > 0,
            rx.moment(
                interval=POLL_INTERVAL_MS,
                on_change=ChatState.poll_tick,
                display="none",
            ),
            rx.fragment(),
        ),
        direction="column",
        display=_show_on_mobile_when("conversation"),
        flex="1",
        min_width="0",
        height="100%",
    )


def chat_page() -> rx.Component:
    return rx.box(
        _header(),
        rx.flex(
            _conversation_list(),
            _conversation_panel(),
            # Atualização da lista: sempre montada em /chat (a 30 s, só com a
            # aba visível); para ao sair da página.
            rx.moment(
                interval=LIST_POLL_INTERVAL_MS,
                on_change=ChatState.list_poll_tick,
                display="none",
            ),
            class_name="page-fade-enter",
            width="100%",
            height="calc(100vh - 64px)",
            min_height="420px",
            border_top=f"1px solid {LIGHT_BORDER}",
            background="white",
        ),
        min_height="100vh",
        background=CREAM,
        font_family="'LINE Seed JP', Arial, sans-serif",
    )
