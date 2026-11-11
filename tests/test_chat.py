import asyncio
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Callable
from unittest.mock import patch

import httpx

from doafacil.chat import (
    CHAT_RATE_LIMIT_MESSAGE,
    CONVERSATION_NOT_FOUND_MESSAGE,
    EDIT_ERROR_MESSAGE,
    EDIT_EXPIRED_MESSAGE,
    EDIT_NOT_FOUND_MESSAGE,
    _decorate_messages,
    edit_message,
    LIST_ERROR_MESSAGE,
    MESSAGE_INPUT_ID,
    PLATFORM_RATE_LIMIT_MESSAGE,
    POLL_PAUSE_SECONDS,
    SEND_INVALID_MESSAGE,
    SEND_NOT_FOUND_MESSAGE,
    ChatInvalidMessageError,
    ChatNotFoundError,
    ChatRateLimitError,
    ChatServiceError,
    ChatState,
    ChatUnauthorizedError,
    avatar_initial,
    classify_rate_limit,
    day_label,
    fetch_messages,
    fetch_unread_total,
    format_unread,
    messages_link_label,
    time_label,
    unread_label,
    list_conversations,
    send_message,
    start_conversation,
)

BASE_URL = "https://xano.example/api:catalog"
ENV = {"XANO_API_URL": BASE_URL}

# Corpos no formato real dos endpoints publicados (teste real 37/37).
CHAT_429 = {
    "code": "ERROR_CODE_TOO_MANY_REQUESTS",
    "message": "Limite de mensagens atingido. Tente novamente em instantes.",
    "payload": None,
}
# Corpo real observado no limite da plataforma (plano gratuito do Xano).
PLATFORM_429 = {
    "code": "ERROR_CODE_TOO_MANY_REQUESTS",
    "message": (
        "Whoa there! Your plan only supports 10 requests per 20 seconds. "
        "Upgrade options and additional information is available at: "
        "https://docs.xano.com/api-rate-limit"
    ),
}
GENERIC_404 = {
    "code": "ERROR_CODE_NOT_FOUND",
    "message": "Conversa não encontrada.",
    "payload": None,
}


def _conversation(conversation_id: int, **overrides: Any) -> dict[str, Any]:
    item = {
        "conversation_id": conversation_id,
        "donation_id": 100 + conversation_id,
        "last_message_at": 1_762_800_000_000 + conversation_id,
        "other_user_first_name": "Ana",
        "donation_title": "Carrinho de brinquedo",
        "donation_status": "disponível",
        "unread_count": 0,
    }
    item.update(overrides)
    return item


def _message(message_id: int, *, mine: bool = False, **overrides: Any) -> dict[str, Any]:
    item = {
        "id": message_id,
        "conversation_id": 7,
        "sender_first_name": "Você" if mine else "Ana",
        "sent_by_me": mine,
        "text": f"Mensagem {message_id}",
        "created_at": 1_762_800_000_000 + message_id * 1000,
        "edited_at": None,
    }
    item.update(overrides)
    return item


SERVER_TIME = 1_762_800_500_000


def _messages_page(
    messages: list[dict[str, Any]],
    *,
    status: str = "disponível",
    has_older: bool = False,
    has_newer: bool = False,
    other_last_read: int = 0,
    edited: list[dict[str, Any]] | None = None,
    server_time: int = SERVER_TIME,
) -> dict[str, Any]:
    return {
        "messages": messages,
        "donation_title": "Carrinho de brinquedo",
        "donation_status": status,
        "has_older": has_older,
        "has_newer": has_newer,
        "other_last_read_message_id": other_last_read,
        "edited_messages": edited or [],
        "server_time": server_time,
    }


def _list_page(items: list[dict[str, Any]], *, has_more: bool = False, page: int = 1) -> dict[str, Any]:
    return {
        "conversations": items,
        "page": page,
        "limit": 20,
        "has_more": has_more,
        "next_page": page + 1 if has_more else None,
    }


class _Recorder:
    """Transporte simulado que guarda as requisições recebidas."""

    def __init__(self, respond: Callable[[httpx.Request], httpx.Response]) -> None:
        self.requests: list[httpx.Request] = []
        self._respond = respond

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._respond(request)

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self))


def _json(status: int, body: object) -> Callable[[httpx.Request], httpx.Response]:
    return lambda request: httpx.Response(status, json=body, request=request)


def _state(**overrides: Any) -> SimpleNamespace:
    values: dict[str, Any] = {
        "auth_token": "token-teste",
        "account_name": "Bia",
        "router": SimpleNamespace(page=SimpleNamespace(params={})),
        "chat_conversations": [],
        "conversations_page": 1,
        "conversations_has_more": False,
        "list_error": "",
        "is_loading_list": False,
        "active_conversation_id": 0,
        "active_other_name": "",
        "active_donation_title": "",
        "active_donation_status": "",
        "chat_messages": [],
        "has_older": False,
        "is_loading_older": False,
        "read_only": False,
        "conversation_error": "",
        "send_error": "",
        "is_sending": False,
        "poll_paused_until": 0.0,
        "mobile_view": "list",
        "unread_total": 0,
        "unread_total_text": "",
        "unread_link_label": "Mensagens",
        "other_last_read_id": 0,
        "last_server_time": 0,
        "editing_message_id": 0,
        "selected_message_id": 0,
        "expired_edit_ids": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _listed(conversation_id: int, unread: int = 0, **overrides: Any) -> dict[str, Any]:
    """Item como fica no estado depois do parsing (com os textos do contador)."""
    return {
        **_conversation(conversation_id, **overrides),
        "initial": "A",
        "unread_count": unread,
        "unread_text": format_unread(unread),
        "unread_label": unread_label(unread),
    }


def _decorated(*ids: int) -> list[dict[str, Any]]:
    return [
        {**_message(message_id), "day_label": "Hoje", "show_day": index == 0}
        for index, message_id in enumerate(ids)
    ]


def _run(coroutine: Any) -> Any:
    return asyncio.run(coroutine)


class ChatClientTests(unittest.TestCase):
    def setUp(self) -> None:
        patcher = patch.dict("os.environ", ENV)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_list_conversations_uses_bearer_page_and_limit(self) -> None:
        recorder = _Recorder(_json(200, _list_page([_conversation(1)], has_more=True)))

        async def call() -> dict[str, Any]:
            async with recorder.client() as client:
                return await list_conversations(client, "token-teste", page=2)

        result = _run(call())
        request = recorder.requests[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url.path, "/api:catalog/catalog/chat/conversations")
        self.assertEqual(request.url.params["page"], "2")
        self.assertEqual(request.url.params["limit"], "20")
        self.assertEqual(request.headers["Authorization"], "Bearer token-teste")
        self.assertTrue(result["has_more"])
        self.assertEqual(result["conversations"][0]["donation_title"], "Carrinho de brinquedo")
        self.assertEqual(result["conversations"][0]["initial"], "A")

    def test_fetch_messages_sends_only_the_requested_cursor(self) -> None:
        recorder = _Recorder(_json(200, _messages_page([_message(1)])))

        async def call() -> None:
            async with recorder.client() as client:
                await fetch_messages(client, "t", 7)
                await fetch_messages(client, "t", 7, before_message_id=30)
                await fetch_messages(client, "t", 7, after_message_id=40, limit=100)

        _run(call())
        latest, before, after = (r.url.params for r in recorder.requests)
        self.assertEqual(dict(latest), {"conversation_id": "7", "limit": "50"})
        self.assertEqual(dict(before), {"conversation_id": "7", "limit": "50", "before_message_id": "30"})
        self.assertEqual(dict(after), {"conversation_id": "7", "limit": "100", "after_message_id": "40"})

    def test_fetch_messages_rejects_two_cursors_without_request(self) -> None:
        recorder = _Recorder(_json(200, _messages_page([])))

        async def call() -> None:
            async with recorder.client() as client:
                await fetch_messages(client, "t", 7, before_message_id=2, after_message_id=1)

        with self.assertRaises(ValueError):
            _run(call())
        self.assertEqual(recorder.requests, [])

    def test_send_and_start_send_json_bodies(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/start"):
                return httpx.Response(200, json=_conversation(7), request=request)
            return httpx.Response(200, json=_message(9, mine=True), request=request)

        recorder = _Recorder(respond)

        async def call() -> tuple[dict[str, Any], dict[str, Any]]:
            async with recorder.client() as client:
                started = await start_conversation(client, "t", 107)
                sent = await send_message(client, "t", 7, "Olá!")
                return started, sent

        started, sent = _run(call())
        start_request, send_request = recorder.requests
        self.assertEqual(start_request.method, "POST")
        self.assertEqual(start_request.read(), b'{"donation_id":107}')
        self.assertEqual(send_request.url.path, "/api:catalog/catalog/chat/messages")
        self.assertIn(b'"message_text":"Ol', send_request.read())
        self.assertEqual(started["conversation_id"], 7)
        self.assertEqual(started["donation_status"], "disponível")
        self.assertIs(sent["sent_by_me"], True)

    def test_parsing_keeps_only_expected_fields(self) -> None:
        item = _conversation(1, email="nao@deve.aparecer")
        message = _message(1, sender_id=55, email="x@y.z")
        recorder = _Recorder(
            lambda request: httpx.Response(
                200,
                json=_list_page([item]) if "conversations" in request.url.path else _messages_page([message]),
                request=request,
            )
        )

        async def call() -> tuple[dict[str, Any], dict[str, Any]]:
            async with recorder.client() as client:
                return (
                    await list_conversations(client, "t"),
                    await fetch_messages(client, "t", 7),
                )

        listed, page = _run(call())
        self.assertNotIn("email", listed["conversations"][0])
        self.assertNotIn("sender_id", page["messages"][0])
        self.assertNotIn("email", page["messages"][0])

    def test_malformed_responses_raise_service_error(self) -> None:
        cases = {
            "sem sent_by_me": _messages_page([{k: v for k, v in _message(1).items() if k != "sent_by_me"}]),
            "messages não é lista": {**_messages_page([]), "messages": {}},
            "sem donation_status": {k: v for k, v in _messages_page([]).items() if k != "donation_status"},
            "has_older não booleano": {**_messages_page([]), "has_older": "sim"},
        }
        for name, body in cases.items():
            with self.subTest(name=name):
                recorder = _Recorder(_json(200, body))

                async def call() -> None:
                    async with recorder.client() as client:
                        await fetch_messages(client, "t", 7)

                with self.assertRaises(ChatServiceError):
                    _run(call())

        recorder = _Recorder(lambda request: httpx.Response(200, text="<html>", request=request))

        async def not_json() -> None:
            async with recorder.client() as client:
                await list_conversations(client, "t")

        with self.assertRaises(ChatServiceError):
            _run(not_json())

    def test_status_codes_are_classified(self) -> None:
        cases = [
            (400, {"code": "ERROR_CODE_INPUT_ERROR", "message": "x"}, ChatInvalidMessageError),
            (401, {"code": "ERROR_CODE_UNAUTHORIZED", "message": "x"}, ChatUnauthorizedError),
            (404, GENERIC_404, ChatNotFoundError),
            (429, CHAT_429, ChatRateLimitError),
            (500, {"message": "x"}, ChatServiceError),
        ]
        for status, body, error in cases:
            with self.subTest(status=status):
                recorder = _Recorder(_json(status, body))

                async def call() -> None:
                    async with recorder.client() as client:
                        await send_message(client, "t", 7, "oi")

                with self.assertRaises(error):
                    _run(call())

    def test_rate_limit_kind_separates_chat_and_platform(self) -> None:
        self.assertEqual(classify_rate_limit(CHAT_429), "chat")
        self.assertEqual(classify_rate_limit(PLATFORM_429), "platform")
        self.assertEqual(classify_rate_limit(None), "platform")

        for body, kind in ((CHAT_429, "chat"), (PLATFORM_429, "platform")):
            with self.subTest(kind=kind):
                recorder = _Recorder(_json(429, body))

                async def call() -> None:
                    async with recorder.client() as client:
                        await send_message(client, "t", 7, "oi")

                with self.assertRaises(ChatRateLimitError) as raised:
                    _run(call())
                self.assertEqual(raised.exception.kind, kind)

        recorder = _Recorder(lambda request: httpx.Response(429, text="Too Many Requests", request=request))

        async def not_json() -> None:
            async with recorder.client() as client:
                await send_message(client, "t", 7, "oi")

        with self.assertRaises(ChatRateLimitError) as raised:
            _run(not_json())
        self.assertEqual(raised.exception.kind, "platform")

    def test_network_error_and_invalid_base_url(self) -> None:
        def fail(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("sem rede", request=request)

        recorder = _Recorder(fail)

        async def call() -> None:
            async with recorder.client() as client:
                await list_conversations(client, "t")

        with self.assertRaises(ChatServiceError):
            _run(call())

        with patch.dict("os.environ", {"XANO_API_URL": "ftp://errado"}):
            recorder = _Recorder(_json(200, _list_page([])))

            async def bad_url() -> None:
                async with recorder.client() as client:
                    await list_conversations(client, "t")

            with self.assertRaises(ChatServiceError):
                _run(bad_url())
            self.assertEqual(recorder.requests, [])


def _created_ms(message_id: int) -> int:
    return _message(message_id)["created_at"]


class ChatReadEditClientTests(unittest.TestCase):
    """4.1: “visto”, edited_at, edited_messages, server_time e o PATCH."""

    def setUp(self) -> None:
        patcher = patch.dict("os.environ", ENV)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _fetch(self, body: object, **kwargs: Any) -> tuple[dict[str, Any], _Recorder]:
        recorder = _Recorder(_json(200, body))

        async def call() -> dict[str, Any]:
            async with recorder.client() as client:
                return await fetch_messages(client, "t", 7, **kwargs)

        return _run(call()), recorder

    def test_page_carries_read_marker_server_time_and_edited_messages(self) -> None:
        edited = _message(2, text="Corrigida", edited_at=1_762_800_400_000)
        page, _ = self._fetch(
            _messages_page([_message(3)], other_last_read=2, edited=[edited])
        )
        self.assertEqual(page["other_last_read_message_id"], 2)
        self.assertEqual(page["server_time"], SERVER_TIME)
        self.assertEqual(page["edited_messages"][0]["text"], "Corrigida")
        self.assertEqual(page["edited_messages"][0]["edited_at"], 1_762_800_400_000)
        # Sem edição, edited_at vazio vira 0.
        self.assertEqual(page["messages"][0]["edited_at"], 0)
        self.assertNotIn("sender_id", page["edited_messages"][0])

    def test_malformed_read_and_edit_fields_raise_service_error(self) -> None:
        sem_edited_at = {k: v for k, v in _message(1).items() if k != "edited_at"}
        cases = {
            "sem other_last_read": {
                k: v for k, v in _messages_page([]).items() if k != "other_last_read_message_id"
            },
            "other_last_read negativo": _messages_page([], other_last_read=-1),
            "sem server_time": {k: v for k, v in _messages_page([]).items() if k != "server_time"},
            "server_time texto": {**_messages_page([]), "server_time": "agora"},
            "edited_messages não é lista": {**_messages_page([]), "edited_messages": {}},
            "mensagem sem edited_at": _messages_page([sem_edited_at]),
            "edited_at texto": _messages_page([_message(1, edited_at="ontem")]),
        }
        for name, body in cases.items():
            with self.subTest(name=name):
                recorder = _Recorder(_json(200, body))

                async def call() -> None:
                    async with recorder.client() as client:
                        await fetch_messages(client, "t", 7)

                with self.assertRaises(ChatServiceError):
                    _run(call())

    def test_edited_since_goes_only_with_after_cursor(self) -> None:
        _, recorder = self._fetch(_messages_page([]), after_message_id=5, edited_since=SERVER_TIME)
        self.assertEqual(recorder.requests[0].url.params["edited_since"], str(SERVER_TIME))
        _, recorder = self._fetch(_messages_page([]), edited_since=SERVER_TIME)
        self.assertNotIn("edited_since", recorder.requests[0].url.params)
        _, recorder = self._fetch(_messages_page([]), after_message_id=5)
        self.assertNotIn("edited_since", recorder.requests[0].url.params)

    def test_edit_message_sends_patch_with_bearer_and_parses_message(self) -> None:
        body = _message(9, mine=True, text="Novo texto", edited_at=1_762_800_400_000)
        recorder = _Recorder(_json(200, body))

        async def call() -> dict[str, Any]:
            async with recorder.client() as client:
                return await edit_message(client, "token-teste", 9, "Novo texto")

        result = _run(call())
        request = recorder.requests[0]
        self.assertEqual(request.method, "PATCH")
        self.assertEqual(request.url.path, "/api:catalog/catalog/chat/messages")
        self.assertEqual(request.headers["Authorization"], "Bearer token-teste")
        self.assertEqual(request.read(), b'{"message_id":9,"message_text":"Novo texto"}')
        self.assertEqual(result["text"], "Novo texto")
        self.assertEqual(result["edited_at"], 1_762_800_400_000)
        self.assertIs(result["sent_by_me"], True)

    def test_edit_message_classifies_errors(self) -> None:
        cases = [
            (400, {"code": "ERROR_CODE_INPUT_ERROR", "message": "x"}, ChatInvalidMessageError),
            (401, {"message": "x"}, ChatUnauthorizedError),
            (404, GENERIC_404, ChatNotFoundError),
            (429, PLATFORM_429, ChatRateLimitError),
            (500, {"message": "x"}, ChatServiceError),
        ]
        for status, body, error in cases:
            with self.subTest(status=status):
                recorder = _Recorder(_json(status, body))

                async def call() -> None:
                    async with recorder.client() as client:
                        await edit_message(client, "t", 9, "oi")

                with self.assertRaises(error):
                    _run(call())


class ChatReadEditStateTests(unittest.TestCase):
    """4.2 a 4.4: marcas da mensagem, consulta automática e edição."""

    def setUp(self) -> None:
        patcher = patch.dict("os.environ", ENV)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _patch_client(self, recorder: _Recorder) -> Any:
        return patch("doafacil.chat._new_client", side_effect=lambda: recorder.client())

    def _now_after(self, message_id: int, minutes: float) -> Any:
        """Relógio do navegador `minutes` minutos depois do envio da mensagem."""
        return patch(
            "doafacil.chat._now",
            return_value=(_created_ms(message_id) + minutes * 60_000) / 1000,
        )

    def _mine_decorated(self, *ids: int, **kwargs: Any) -> list[dict[str, Any]]:
        with self._now_after(max(ids), 1):
            return _decorate_messages([_message(i, mine=True) for i in ids], **kwargs)

    # 4.2 ------------------------------------------------------------------

    def test_read_status_only_on_own_messages(self) -> None:
        messages = [_message(1, mine=True), _message(2, mine=True), _message(3)]
        with self._now_after(3, 1):
            decorated = _decorate_messages(messages, other_last_read=3)
        self.assertEqual([m["is_read"] for m in decorated], [True, True, False])
        with self._now_after(3, 1):
            decorated = _decorate_messages(messages, other_last_read=1)
        self.assertEqual([m["is_read"] for m in decorated], [True, False, False])

    def test_edited_flag_follows_edited_at(self) -> None:
        with self._now_after(2, 1):
            decorated = _decorate_messages(
                [_message(1, edited_at=1_762_800_400_000), _message(2)]
            )
        self.assertEqual([m["edited"] for m in decorated], [True, False])

    def test_editable_only_own_within_15_minutes_and_not_read_only(self) -> None:
        own = [_message(1, mine=True)]
        with self._now_after(1, 14):
            self.assertTrue(_decorate_messages(own)[0]["editable"])
            self.assertFalse(_decorate_messages(own, read_only=True)[0]["editable"])
            self.assertFalse(_decorate_messages(own, expired_ids=[1])[0]["editable"])
            self.assertFalse(_decorate_messages([_message(1)])[0]["editable"])
        with self._now_after(1, 16):
            self.assertFalse(_decorate_messages(own)[0]["editable"])

    def test_open_conversation_resets_and_takes_read_marker_and_server_time(self) -> None:
        state = _state(
            chat_conversations=[_conversation(7), _conversation(8)],
            active_conversation_id=7,
            other_last_read_id=50,
            last_server_time=123,
            editing_message_id=5,
        )
        recorder = _Recorder(_json(200, _messages_page([_message(1, mine=True)], other_last_read=1)))
        with self._patch_client(recorder), patch("doafacil.chat.rx.set_value", return_value="clear") as set_value:
            result = _run(ChatState.select_conversation.fn(state, 8))
        self.assertEqual(state.other_last_read_id, 1)
        self.assertEqual(state.last_server_time, SERVER_TIME)
        self.assertTrue(state.chat_messages[0]["is_read"])
        # Trocar de conversa durante a edição encerra a edição e limpa o campo.
        self.assertEqual(state.editing_message_id, 0)
        self.assertEqual(result, "clear")
        set_value.assert_called_once_with(MESSAGE_INPUT_ID, "")

    def test_read_marker_never_goes_back(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=self._mine_decorated(5, 6), other_last_read_id=6)
        recorder = _Recorder(_json(200, _messages_page([], other_last_read=5)))
        with self._patch_client(recorder):
            _run(ChatState.poll_if_visible.fn(state, "visible"))
        self.assertEqual(state.other_last_read_id, 6)
        self.assertTrue(all(m["is_read"] for m in state.chat_messages))

    # 4.3 ------------------------------------------------------------------

    def test_first_poll_without_server_time_sends_no_edited_since(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=self._mine_decorated(5))
        recorder = _Recorder(_json(200, _messages_page([])))
        with self._patch_client(recorder):
            _run(ChatState.poll_if_visible.fn(state, "visible"))
        self.assertNotIn("edited_since", recorder.requests[0].url.params)
        self.assertEqual(state.last_server_time, SERVER_TIME)

    def test_poll_applies_edits_read_marker_and_new_messages_in_one_request(self) -> None:
        state = _state(
            active_conversation_id=7,
            chat_messages=self._mine_decorated(5, 6),
            last_server_time=1_762_800_100_000,
        )
        edited = _message(5, text="Mensagem 5 corrigida", edited_at=1_762_800_200_000)
        body = _messages_page(
            [_message(7)],
            other_last_read=6,
            # A folga de 5 s pode repetir a mesma edição: é aplicada pelo id.
            edited=[edited, edited],
            server_time=1_762_800_300_000,
        )
        recorder = _Recorder(_json(200, body))
        with self._patch_client(recorder), self._now_after(7, 1):
            _run(ChatState.poll_if_visible.fn(state, "visible"))
        self.assertEqual(len(recorder.requests), 1)
        params = recorder.requests[0].url.params
        self.assertEqual(params["after_message_id"], "6")
        self.assertEqual(params["edited_since"], "1762800100000")
        by_id = {m["id"]: m for m in state.chat_messages}
        self.assertEqual(list(by_id), [5, 6, 7])
        self.assertEqual(by_id[5]["text"], "Mensagem 5 corrigida")
        self.assertTrue(by_id[5]["edited"])
        self.assertFalse(by_id[6]["edited"])
        self.assertTrue(by_id[5]["is_read"] and by_id[6]["is_read"])
        self.assertFalse(by_id[7]["is_read"])
        self.assertEqual(state.last_server_time, 1_762_800_300_000)

    def test_poll_recomputes_pencil_as_time_passes(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=self._mine_decorated(5))
        self.assertTrue(state.chat_messages[0]["editable"])
        with self._patch_client(_Recorder(_json(200, _messages_page([])))), self._now_after(5, 16):
            _run(ChatState.poll_if_visible.fn(state, "visible"))
        self.assertFalse(state.chat_messages[0]["editable"])

    def test_poll_ends_edit_when_donation_becomes_completed(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=self._mine_decorated(5), editing_message_id=5)
        recorder = _Recorder(_json(200, _messages_page([], status="concluída")))
        with self._patch_client(recorder), patch("doafacil.chat.rx.set_value", return_value="clear"):
            result = _run(ChatState.poll_if_visible.fn(state, "visible"))
        self.assertEqual(result, "clear")
        self.assertEqual(state.editing_message_id, 0)
        self.assertFalse(state.chat_messages[0]["editable"])

    def test_load_older_keeps_server_time(self) -> None:
        state = _state(
            active_conversation_id=7,
            chat_messages=self._mine_decorated(5),
            has_older=True,
            last_server_time=111,
        )
        recorder = _Recorder(_json(200, _messages_page([_message(4)], other_last_read=5, server_time=999)))
        with self._patch_client(recorder):
            _run(ChatState.load_older_messages.fn(state))
        self.assertEqual(state.last_server_time, 111)
        self.assertEqual(state.other_last_read_id, 5)

    # 4.4 ------------------------------------------------------------------

    def _editing_state(self, **overrides: Any) -> SimpleNamespace:
        values = {"active_conversation_id": 7, "chat_messages": self._mine_decorated(5, 6)}
        values.update(overrides)
        return _state(**values)

    def test_start_edit_fills_the_field_and_focuses_it(self) -> None:
        state = self._editing_state(selected_message_id=6)
        with (
            patch("doafacil.chat.rx.set_value", return_value="fill") as set_value,
            patch("doafacil.chat.rx.set_focus", return_value="focus") as set_focus,
        ):
            result = ChatState.start_edit.fn(state, 6)
        self.assertEqual(result, ["fill", "focus"])
        set_value.assert_called_once_with(MESSAGE_INPUT_ID, "Mensagem 6")
        set_focus.assert_called_once_with(MESSAGE_INPUT_ID)
        self.assertEqual(state.editing_message_id, 6)
        self.assertEqual(state.selected_message_id, 0)

    def test_start_edit_ignores_messages_that_are_not_editable(self) -> None:
        with self._now_after(5, 1):
            messages = _decorate_messages([_message(5), _message(6, mine=True)], read_only=False)
        state = _state(active_conversation_id=7, chat_messages=messages)
        with patch("doafacil.chat.rx.set_value") as set_value:
            self.assertIsNone(ChatState.start_edit.fn(state, 5))
            self.assertIsNone(ChatState.start_edit.fn(state, 99))
        set_value.assert_not_called()
        self.assertEqual(state.editing_message_id, 0)

    def test_save_edit_replaces_bubble_marks_edited_and_clears_field(self) -> None:
        state = self._editing_state(editing_message_id=5)
        body = _message(5, mine=True, text="Corrigido", edited_at=1_762_800_400_000)
        recorder = _Recorder(_json(200, body))
        with (
            self._patch_client(recorder),
            self._now_after(6, 1),
            patch("doafacil.chat.rx.set_value", return_value="clear") as set_value,
        ):
            result = _run(ChatState.send_message.fn(state, {"message_text": "  Corrigido  "}))
        request = recorder.requests[0]
        self.assertEqual(request.method, "PATCH")
        self.assertEqual(request.read(), b'{"message_id":5,"message_text":"Corrigido"}')
        self.assertEqual(result, "clear")
        set_value.assert_called_once_with(MESSAGE_INPUT_ID, "")
        first = state.chat_messages[0]
        self.assertEqual((first["text"], first["edited"]), ("Corrigido", True))
        self.assertEqual([m["id"] for m in state.chat_messages], [5, 6])
        self.assertEqual(state.editing_message_id, 0)
        self.assertFalse(state.is_sending)

    def test_save_same_text_keeps_message_not_edited(self) -> None:
        state = self._editing_state(editing_message_id=5)
        recorder = _Recorder(_json(200, _message(5, mine=True)))
        with self._patch_client(recorder), self._now_after(6, 1), patch("doafacil.chat.rx.set_value"):
            _run(ChatState.send_message.fn(state, {"message_text": "Mensagem 5"}))
        self.assertFalse(state.chat_messages[0]["edited"])
        self.assertEqual(state.editing_message_id, 0)

    def test_cancel_and_escape_end_edit_without_request(self) -> None:
        for trigger in ("cancelar", "esc"):
            with self.subTest(trigger=trigger):
                state = self._editing_state(editing_message_id=5)
                recorder = _Recorder(_json(200, _message(5, mine=True)))
                with self._patch_client(recorder), patch("doafacil.chat.rx.set_value", return_value="clear") as set_value:
                    if trigger == "cancelar":
                        result = ChatState.cancel_edit.fn(state)
                    else:
                        result = ChatState.composer_key_down.fn(state, "Escape")
                self.assertEqual(result, "clear")
                set_value.assert_called_once_with(MESSAGE_INPUT_ID, "")
                self.assertEqual(state.editing_message_id, 0)
                self.assertEqual(recorder.requests, [])
                self.assertEqual(state.chat_messages[0]["text"], "Mensagem 5")

    def test_other_keys_and_escape_without_edit_do_nothing(self) -> None:
        state = self._editing_state(editing_message_id=5)
        with patch("doafacil.chat.rx.set_value") as set_value:
            self.assertIsNone(ChatState.composer_key_down.fn(state, "a"))
            self.assertIsNone(ChatState.composer_key_down.fn(state, "Enter"))
            self.assertEqual(state.editing_message_id, 5)
            self.assertIsNone(ChatState.composer_key_down.fn(_state(), "Escape"))
            self.assertIsNone(ChatState.cancel_edit.fn(_state()))
        set_value.assert_not_called()

    def test_edit_400_means_expired_hides_pencil_and_keeps_text(self) -> None:
        state = self._editing_state(editing_message_id=5)
        with (
            self._patch_client(_Recorder(_json(400, {"message": "x"}))),
            self._now_after(6, 1),
            patch("doafacil.chat.rx.set_value") as set_value,
        ):
            result = _run(ChatState.send_message.fn(state, {"message_text": "Novo"}))
        self.assertIsNone(result)
        set_value.assert_not_called()
        self.assertEqual(state.send_error, EDIT_EXPIRED_MESSAGE)
        self.assertEqual(state.editing_message_id, 0)
        self.assertEqual(state.expired_edit_ids, [5])
        self.assertFalse(state.chat_messages[0]["editable"])
        self.assertTrue(state.chat_messages[1]["editable"])

    def test_edit_404_and_429_messages(self) -> None:
        cases = [
            (404, GENERIC_404, EDIT_NOT_FOUND_MESSAGE, 0),
            (429, CHAT_429, CHAT_RATE_LIMIT_MESSAGE, 5),
            (429, PLATFORM_429, PLATFORM_RATE_LIMIT_MESSAGE, 5),
            (500, {"message": "x"}, EDIT_ERROR_MESSAGE, 5),
        ]
        for status, body, expected, editing in cases:
            with self.subTest(status=status, message=expected):
                state = self._editing_state(editing_message_id=5)
                with (
                    self._patch_client(_Recorder(_json(status, body))),
                    patch("doafacil.chat.rx.set_value") as set_value,
                ):
                    result = _run(ChatState.send_message.fn(state, {"message_text": "Novo"}))
                self.assertIsNone(result)
                set_value.assert_not_called()
                self.assertEqual(state.send_error, expected)
                self.assertEqual(state.editing_message_id, editing)
                self.assertEqual(state.chat_messages[0]["text"], "Mensagem 5")
                self.assertFalse(state.is_sending)

    def test_edit_with_empty_or_long_text_makes_no_request(self) -> None:
        for text, error in (("   ", ""), ("a" * 1001, SEND_INVALID_MESSAGE)):
            with self.subTest(size=len(text)):
                state = self._editing_state(editing_message_id=5)
                recorder = _Recorder(_json(200, _message(5, mine=True)))
                with self._patch_client(recorder):
                    _run(ChatState.send_message.fn(state, {"message_text": text}))
                self.assertEqual(recorder.requests, [])
                self.assertEqual(state.send_error, error)
                self.assertEqual(state.editing_message_id, 5)

    def test_toggle_selection_only_for_editable_messages(self) -> None:
        with self._now_after(6, 1):
            messages = _decorate_messages([_message(5), _message(6, mine=True)])
        state = _state(active_conversation_id=7, chat_messages=messages)
        ChatState.toggle_message_selection.fn(state, 6)
        self.assertEqual(state.selected_message_id, 6)
        ChatState.toggle_message_selection.fn(state, 6)
        self.assertEqual(state.selected_message_id, 0)
        ChatState.toggle_message_selection.fn(state, 6)
        ChatState.toggle_message_selection.fn(state, 5)
        self.assertEqual(state.selected_message_id, 0)


class ChatUnreadClientTests(unittest.TestCase):
    """4.1: unread_count obrigatório na lista, fetch_unread_total e formato."""

    def setUp(self) -> None:
        patcher = patch.dict("os.environ", ENV)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _list(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        recorder = _Recorder(_json(200, _list_page(items)))

        async def call() -> dict[str, Any]:
            async with recorder.client() as client:
                return await list_conversations(client, "t")

        return _run(call())

    def test_list_item_carries_unread_count_and_texts(self) -> None:
        result = self._list([_conversation(1, unread_count=3), _conversation(2)])
        first, second = result["conversations"]
        self.assertEqual(first["unread_count"], 3)
        self.assertEqual(first["unread_text"], "3")
        self.assertEqual(first["unread_label"], "3 mensagens não lidas")
        self.assertEqual(second["unread_count"], 0)
        self.assertEqual(second["unread_text"], "")

    def test_list_item_without_or_with_invalid_unread_count_is_malformed(self) -> None:
        missing = {k: v for k, v in _conversation(1).items() if k != "unread_count"}
        for name, item in {
            "ausente": missing,
            "negativo": _conversation(1, unread_count=-1),
            "texto": _conversation(1, unread_count="3"),
            "booleano": _conversation(1, unread_count=True),
            "nulo": _conversation(1, unread_count=None),
        }.items():
            with self.subTest(name=name), self.assertRaises(ChatServiceError):
                self._list([item])

    def test_start_without_unread_count_still_parses_with_zero(self) -> None:
        body = {k: v for k, v in _conversation(7).items() if k != "unread_count"}
        recorder = _Recorder(_json(200, body))

        async def call() -> dict[str, Any]:
            async with recorder.client() as client:
                return await start_conversation(client, "t", 107)

        self.assertEqual(_run(call())["unread_count"], 0)

    def test_fetch_unread_total_uses_bearer_and_returns_the_number(self) -> None:
        recorder = _Recorder(_json(200, {"unread_total": 12}))

        async def call() -> int:
            async with recorder.client() as client:
                return await fetch_unread_total(client, "token-teste")

        self.assertEqual(_run(call()), 12)
        request = recorder.requests[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url.path, "/api:catalog/catalog/chat/unread_total")
        self.assertEqual(request.headers["Authorization"], "Bearer token-teste")
        self.assertEqual(dict(request.url.params), {})

    def test_fetch_unread_total_classifies_errors_and_malformed_bodies(self) -> None:
        cases = [
            (401, {"message": "x"}, ChatUnauthorizedError),
            (429, PLATFORM_429, ChatRateLimitError),
            (500, {"message": "x"}, ChatServiceError),
            (200, {}, ChatServiceError),
            (200, {"unread_total": -1}, ChatServiceError),
            (200, {"unread_total": "2"}, ChatServiceError),
            (200, [], ChatServiceError),
        ]
        for status, body, error in cases:
            with self.subTest(status=status, body=body):
                recorder = _Recorder(_json(status, body))

                async def call() -> None:
                    async with recorder.client() as client:
                        await fetch_unread_total(client, "t")

                with self.assertRaises(error):
                    _run(call())

    def test_format_unread(self) -> None:
        for count, expected in ((0, ""), (1, "1"), (99, "99"), (100, "99+"), (150, "99+"), (-3, "")):
            with self.subTest(count=count):
                self.assertEqual(format_unread(count), expected)

    def test_accessible_labels_singular_and_plural(self) -> None:
        self.assertEqual(unread_label(0), "")
        self.assertEqual(unread_label(1), "1 mensagem não lida")
        self.assertEqual(unread_label(3), "3 mensagens não lidas")
        # O rótulo diz o número real mesmo quando o círculo mostra "99+".
        self.assertEqual(unread_label(150), "150 mensagens não lidas")
        self.assertEqual(messages_link_label(0), "Mensagens")
        self.assertEqual(messages_link_label(1), "Mensagens, 1 não lida")
        self.assertEqual(messages_link_label(42), "Mensagens, 42 não lidas")


class ChatUnreadStateTests(unittest.TestCase):
    """4.2 a 4.4: contador zerado na conversa aberta, lista a cada 30 s e total."""

    def setUp(self) -> None:
        patcher = patch.dict("os.environ", ENV)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _patch_client(self, recorder: _Recorder) -> Any:
        return patch("doafacil.chat._new_client", side_effect=lambda: recorder.client())

    # 4.2 ------------------------------------------------------------------

    def test_opening_a_conversation_clears_its_counter_immediately(self) -> None:
        state = _state(chat_conversations=[_listed(7, 3), _listed(8, 2)])
        seen_during_request: list[int] = []

        def respond(request: httpx.Request) -> httpx.Response:
            seen_during_request.append(state.chat_conversations[0]["unread_count"])
            return httpx.Response(200, json=_messages_page([_message(1)]), request=request)

        with self._patch_client(_Recorder(respond)):
            _run(ChatState.select_conversation.fn(state, 7))
        # Já estava 0 enquanto a leitura ainda estava em andamento.
        self.assertEqual(seen_during_request, [0])
        first, second = state.chat_conversations
        self.assertEqual((first["unread_count"], first["unread_text"], first["unread_label"]), (0, "", ""))
        self.assertEqual(second["unread_count"], 2)

    def test_list_received_with_open_conversation_forces_zero_for_it(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/conversations"):
                items = [_conversation(7, unread_count=4), _conversation(8, unread_count=1)]
                return httpx.Response(200, json=_list_page(items), request=request)
            return httpx.Response(200, json=_messages_page([_message(1)]), request=request)

        state = _state(router=SimpleNamespace(page=SimpleNamespace(params={"conversa": "7"})))
        with self._patch_client(_Recorder(respond)):
            _run(ChatState.load_chat.fn(state))
        counts = {c["conversation_id"]: c["unread_count"] for c in state.chat_conversations}
        self.assertEqual(counts, {7: 0, 8: 1})

        # A atualização da lista chega antes da leitura das mensagens novas.
        recorder = _Recorder(_json(200, _list_page([_conversation(7, unread_count=2)])))
        with self._patch_client(recorder):
            _run(ChatState.list_poll_if_visible.fn(state, "visible"))
        self.assertEqual(state.chat_conversations[0]["unread_count"], 0)

        # Na lista vinda de "Carregar mais conversas" também.
        state.conversations_has_more = True
        recorder = _Recorder(_json(200, _list_page([_conversation(7, unread_count=5)], page=2)))
        state.chat_conversations = [_listed(8, 1)]
        with self._patch_client(recorder):
            _run(ChatState.load_more_conversations.fn(state))
        counts = {c["conversation_id"]: c["unread_count"] for c in state.chat_conversations}
        self.assertEqual(counts, {8: 1, 7: 0})

    # 4.3 ------------------------------------------------------------------

    def test_list_poll_tick_checks_visibility_only_when_allowed(self) -> None:
        with (
            patch("doafacil.chat.rx.call_script", return_value="check-visibility") as call_script,
            patch("doafacil.chat._now", return_value=1000.0),
        ):
            self.assertIsNone(ChatState.list_poll_tick.fn(_state(auth_token="")))
            self.assertIsNone(ChatState.list_poll_tick.fn(_state(poll_paused_until=1030.0)))
            self.assertIsNone(ChatState.list_poll_tick.fn(_state(is_loading_list=True)))
            # Sem conversa aberta a lista continua atualizando.
            self.assertEqual(ChatState.list_poll_tick.fn(_state(active_conversation_id=0)), "check-visibility")
        self.assertEqual(call_script.call_count, 1)
        self.assertEqual(call_script.call_args.args[0], "document.visibilityState")
        self.assertIn("list_poll_if_visible", str(call_script.call_args.kwargs["callback"]))

    def test_list_poll_with_hidden_tab_makes_no_request(self) -> None:
        state = _state(chat_conversations=[_listed(1)])
        recorder = _Recorder(_json(200, _list_page([_conversation(1, unread_count=3)])))
        with self._patch_client(recorder):
            _run(ChatState.list_poll_if_visible.fn(state, "hidden"))
        self.assertEqual(recorder.requests, [])
        self.assertEqual(state.chat_conversations[0]["unread_count"], 0)

    def test_list_poll_with_active_pause_makes_no_request(self) -> None:
        state = _state(poll_paused_until=1030.0)
        recorder = _Recorder(_json(200, _list_page([])))
        with self._patch_client(recorder), patch("doafacil.chat._now", return_value=1000.0):
            _run(ChatState.list_poll_if_visible.fn(state, "visible"))
        self.assertEqual(recorder.requests, [])

    def test_list_poll_429_pauses_lists_and_messages_silently(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=_decorated(5), chat_conversations=[_listed(7)])
        with (
            self._patch_client(_Recorder(_json(429, PLATFORM_429))),
            patch("doafacil.chat._now", return_value=1000.0),
        ):
            result = _run(ChatState.list_poll_if_visible.fn(state, "visible"))
        self.assertIsNone(result)
        self.assertEqual(state.poll_paused_until, 1000.0 + POLL_PAUSE_SECONDS)
        self.assertEqual(state.list_error, "")
        self.assertEqual(len(state.chat_conversations), 1)

        # A pausa vale também para as mensagens.
        recorder = _Recorder(_json(200, _messages_page([_message(6)])))
        with self._patch_client(recorder), patch("doafacil.chat._now", return_value=1030.0):
            _run(ChatState.poll_if_visible.fn(state, "visible"))
            self.assertIsNone(ChatState.list_poll_tick.fn(state))
        self.assertEqual(recorder.requests, [])

        # E um 429 nas mensagens pausa a lista.
        state = _state(active_conversation_id=7, chat_messages=_decorated(5))
        with (
            self._patch_client(_Recorder(_json(429, CHAT_429))),
            patch("doafacil.chat._now", return_value=2000.0),
        ):
            _run(ChatState.poll_if_visible.fn(state, "visible"))
        recorder = _Recorder(_json(200, _list_page([])))
        with self._patch_client(recorder), patch("doafacil.chat._now", return_value=2030.0):
            _run(ChatState.list_poll_if_visible.fn(state, "visible"))
        self.assertEqual(recorder.requests, [])

    def test_list_poll_merges_first_page_on_top_without_losing_or_repeating(self) -> None:
        # Páginas 1 e 2 já carregadas: 1, 2 | 3, 4.
        state = _state(
            chat_conversations=[_listed(1), _listed(2), _listed(3), _listed(4)],
            conversations_page=2,
            conversations_has_more=True,
        )
        # Nova página 1: a conversa 3 ganhou mensagem e subiu; 9 é nova.
        page_one = [_conversation(3, unread_count=2), _conversation(9, unread_count=1)]
        recorder = _Recorder(_json(200, _list_page(page_one, has_more=True)))
        with self._patch_client(recorder):
            result = _run(ChatState.list_poll_if_visible.fn(state, "visible"))
        self.assertIsNone(result)
        self.assertEqual(recorder.requests[0].url.params["page"], "1")
        self.assertEqual([c["conversation_id"] for c in state.chat_conversations], [3, 9, 1, 2, 4])
        self.assertEqual(state.chat_conversations[0]["unread_text"], "2")
        # As páginas já carregadas continuam valendo para "Carregar mais".
        self.assertEqual(state.conversations_page, 2)
        self.assertTrue(state.conversations_has_more)

    def test_list_poll_errors_are_silent_and_401_redirects(self) -> None:
        state = _state(chat_conversations=[_listed(1, 2)])
        with self._patch_client(_Recorder(_json(500, {"message": "x"}))):
            self.assertIsNone(_run(ChatState.list_poll_if_visible.fn(state, "visible")))
        self.assertEqual(state.list_error, "")
        self.assertEqual(state.chat_conversations[0]["unread_count"], 2)

        with (
            self._patch_client(_Recorder(_json(401, {"message": "x"}))),
            patch("doafacil.chat.rx.redirect", return_value="login-redirect"),
        ):
            result = _run(ChatState.list_poll_if_visible.fn(state, "visible"))
        self.assertEqual(result, "login-redirect")
        self.assertEqual(state.auth_token, "")

    # 4.4 ------------------------------------------------------------------

    def test_unread_total_without_token_makes_no_request(self) -> None:
        state = _state(auth_token="", unread_total=5, unread_total_text="5")
        recorder = _Recorder(_json(200, {"unread_total": 3}))
        with self._patch_client(recorder):
            _run(ChatState.load_unread_total.fn(state))
        self.assertEqual(recorder.requests, [])
        self.assertEqual((state.unread_total, state.unread_total_text), (0, ""))

    def test_unread_total_loads_number_text_and_link_label(self) -> None:
        for total, text, label in (
            (3, "3", "Mensagens, 3 não lidas"),
            (150, "99+", "Mensagens, 150 não lidas"),
            (0, "", "Mensagens"),
        ):
            with self.subTest(total=total):
                state = _state()
                recorder = _Recorder(_json(200, {"unread_total": total}))
                with self._patch_client(recorder):
                    _run(ChatState.load_unread_total.fn(state))
                self.assertEqual(len(recorder.requests), 1)
                self.assertEqual(
                    (state.unread_total, state.unread_total_text, state.unread_link_label),
                    (total, text, label),
                )

    def test_unread_total_errors_and_401_leave_zero_without_warning(self) -> None:
        for status, body in (
            (401, {"message": "x"}),
            (429, PLATFORM_429),
            (500, {"message": "x"}),
            (200, {"unread_total": "x"}),
        ):
            with self.subTest(status=status):
                state = _state(unread_total=4, unread_total_text="4")
                with (
                    self._patch_client(_Recorder(_json(status, body))),
                    patch("doafacil.chat.rx.redirect") as redirect,
                ):
                    result = _run(ChatState.load_unread_total.fn(state))
                self.assertIsNone(result)
                redirect.assert_not_called()
                self.assertEqual((state.unread_total, state.unread_total_text), (0, ""))
                self.assertEqual(state.unread_link_label, "Mensagens")
                # O token não é apagado aqui; quem trata o 401 é o load_account.
                self.assertEqual(state.auth_token, "token-teste")


class ChatHelperTests(unittest.TestCase):
    def test_avatar_initial(self) -> None:
        self.assertEqual(avatar_initial("ana"), "A")
        self.assertEqual(avatar_initial("  Élio "), "É")
        self.assertEqual(avatar_initial(""), "?")
        self.assertEqual(avatar_initial("Usuário"), "?")
        self.assertEqual(avatar_initial(None), "?")

    def test_day_label_uses_brasilia_near_utc_midnight(self) -> None:
        def ms(text: str) -> int:
            return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp() * 1000)

        now = ms("2026-11-10T12:00:00")
        # 02:30 UTC de 10/11 = 23:30 de 09/11 em Brasília.
        self.assertEqual(day_label(ms("2026-11-10T02:30:00"), now), "Ontem")
        # 03:30 UTC de 10/11 = 00:30 de 10/11 em Brasília.
        self.assertEqual(day_label(ms("2026-11-10T03:30:00"), now), "Hoje")
        self.assertEqual(day_label(ms("2026-11-07T15:00:00"), now), "07/11/2026")

    def test_time_label_uses_brasilia_with_same_rule_as_day_label(self) -> None:
        def ms(text: str) -> int:
            return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp() * 1000)

        # 02:30 UTC de 10/11 = 23:30 de 09/11 em Brasília ("Ontem" no day_label).
        self.assertEqual(time_label(ms("2026-11-10T02:30:00")), "23:30")
        # 03:05 UTC = 00:05 em Brasília: zero à esquerda nas horas e minutos.
        self.assertEqual(time_label(ms("2026-11-10T03:05:00")), "00:05")
        self.assertEqual(time_label(ms("2026-11-10T15:41:59")), "12:41")
        self.assertEqual(time_label("x"), "")

    def test_decorated_messages_carry_time_label(self) -> None:
        from doafacil.chat import _decorate_messages

        created = int(datetime(2026, 11, 10, 15, 41, tzinfo=timezone.utc).timestamp() * 1000)
        decorated = _decorate_messages([_message(1, created_at=created)])
        self.assertEqual(decorated[0]["time_label"], "12:41")


class ChatStateTests(unittest.TestCase):
    def setUp(self) -> None:
        patcher = patch.dict("os.environ", ENV)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _patch_client(self, recorder: _Recorder) -> Any:
        return patch("doafacil.chat._new_client", side_effect=lambda: recorder.client())

    # 4.3 ------------------------------------------------------------------

    def test_load_chat_without_session_redirects_without_requests(self) -> None:
        state = _state(auth_token="")
        recorder = _Recorder(_json(200, _list_page([])))
        with (
            self._patch_client(recorder),
            patch("doafacil.chat.rx.redirect", return_value="login-redirect") as redirect,
        ):
            result = _run(ChatState.load_chat.fn(state))
        self.assertEqual(result, "login-redirect")
        redirect.assert_called_once_with("/login")
        self.assertEqual(recorder.requests, [])

    def test_load_chat_opens_conversation_from_route(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/conversations"):
                return httpx.Response(200, json=_list_page([_conversation(7, other_user_first_name="Carla")]), request=request)
            return httpx.Response(
                200,
                json=_messages_page([_message(1), _message(2, mine=True)], has_older=True),
                request=request,
            )

        recorder = _Recorder(respond)
        state = _state(router=SimpleNamespace(page=SimpleNamespace(params={"conversa": "7"})))
        with self._patch_client(recorder):
            result = _run(ChatState.load_chat.fn(state))

        self.assertIsNone(result)
        self.assertEqual(len(recorder.requests), 2)
        self.assertNotIn("before_message_id", recorder.requests[1].url.params)
        self.assertNotIn("after_message_id", recorder.requests[1].url.params)
        self.assertEqual(state.active_conversation_id, 7)
        self.assertEqual(state.active_other_name, "Carla")
        self.assertEqual(state.active_donation_title, "Carrinho de brinquedo")
        self.assertEqual([m["id"] for m in state.chat_messages], [1, 2])
        self.assertEqual([m["sent_by_me"] for m in state.chat_messages], [False, True])
        self.assertTrue(state.chat_messages[0]["show_day"])
        self.assertTrue(state.has_older)
        self.assertFalse(state.read_only)
        self.assertEqual(state.mobile_view, "conversation")

    def test_load_chat_with_invalid_route_keeps_list(self) -> None:
        recorder = _Recorder(_json(200, _list_page([_conversation(1)])))
        state = _state(router=SimpleNamespace(page=SimpleNamespace(params={"conversa": "abc"})))
        with self._patch_client(recorder):
            _run(ChatState.load_chat.fn(state))
        self.assertEqual(state.conversation_error, CONVERSATION_NOT_FOUND_MESSAGE)
        self.assertEqual(len(state.chat_conversations), 1)
        self.assertEqual(len(recorder.requests), 1)

    def test_load_chat_conversation_404_shows_not_found(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/conversations"):
                return httpx.Response(200, json=_list_page([]), request=request)
            return httpx.Response(404, json=GENERIC_404, request=request)

        state = _state(router=SimpleNamespace(page=SimpleNamespace(params={"conversa": "99"})))
        with self._patch_client(_Recorder(respond)):
            _run(ChatState.load_chat.fn(state))
        self.assertEqual(state.conversation_error, CONVERSATION_NOT_FOUND_MESSAGE)
        self.assertEqual(state.active_conversation_id, 0)

    def test_401_clears_session_and_redirects(self) -> None:
        recorder = _Recorder(_json(401, {"code": "ERROR_CODE_UNAUTHORIZED", "message": "x"}))
        state = _state()
        with (
            self._patch_client(recorder),
            patch("doafacil.chat.rx.redirect", return_value="login-redirect"),
        ):
            result = _run(ChatState.load_chat.fn(state))
        self.assertEqual(result, "login-redirect")
        self.assertEqual(state.auth_token, "")
        self.assertEqual(state.account_name, "")

    def test_list_failure_and_rate_limit_messages(self) -> None:
        for status, body, expected in (
            (500, {"message": "x"}, LIST_ERROR_MESSAGE),
            (429, PLATFORM_429, PLATFORM_RATE_LIMIT_MESSAGE),
        ):
            with self.subTest(status=status):
                state = _state()
                with self._patch_client(_Recorder(_json(status, body))):
                    _run(ChatState.load_chat.fn(state))
                self.assertEqual(state.list_error, expected)

    def test_completed_donation_opens_read_only_and_reserved_does_not(self) -> None:
        for status, read_only in (("concluída", True), ("reservada", False)):
            with self.subTest(status=status):
                state = _state(chat_conversations=[_conversation(7)])
                recorder = _Recorder(_json(200, _messages_page([_message(1)], status=status)))
                with self._patch_client(recorder):
                    _run(ChatState.select_conversation.fn(state, 7))
                self.assertIs(state.read_only, read_only)
                self.assertEqual(state.active_donation_status, status)

    # 4.4 ------------------------------------------------------------------

    def test_load_older_prepends_without_duplicates_and_hides_button(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=_decorated(5, 6), has_older=True)
        # A resposta repete a mensagem 5 para provar a deduplicação.
        recorder = _Recorder(_json(200, _messages_page([_message(3), _message(4), _message(5)], has_older=False)))
        with self._patch_client(recorder):
            _run(ChatState.load_older_messages.fn(state))
        self.assertEqual(recorder.requests[0].url.params["before_message_id"], "5")
        self.assertEqual([m["id"] for m in state.chat_messages], [3, 4, 5, 6])
        self.assertFalse(state.has_older)

    def test_load_older_does_nothing_without_older_messages(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=_decorated(5), has_older=False)
        recorder = _Recorder(_json(200, _messages_page([])))
        with self._patch_client(recorder):
            _run(ChatState.load_older_messages.fn(state))
        self.assertEqual(recorder.requests, [])

    def test_load_more_conversations_appends_without_duplicates(self) -> None:
        state = _state(
            chat_conversations=[_conversation(1), _conversation(2)],
            conversations_has_more=True,
        )
        recorder = _Recorder(_json(200, _list_page([_conversation(2), _conversation(3)], page=2)))
        with self._patch_client(recorder):
            _run(ChatState.load_more_conversations.fn(state))
        self.assertEqual(recorder.requests[0].url.params["page"], "2")
        self.assertEqual([c["conversation_id"] for c in state.chat_conversations], [1, 2, 3])
        self.assertEqual(state.conversations_page, 2)
        self.assertFalse(state.conversations_has_more)

    def test_select_conversation_switches_history(self) -> None:
        state = _state(
            chat_conversations=[_conversation(7), _conversation(8, other_user_first_name="Davi")],
            active_conversation_id=7,
            chat_messages=_decorated(1, 2),
        )
        recorder = _Recorder(_json(200, _messages_page([_message(40)])))
        with self._patch_client(recorder):
            _run(ChatState.select_conversation.fn(state, 8))
        self.assertEqual(state.active_conversation_id, 8)
        self.assertEqual(state.active_other_name, "Davi")
        self.assertEqual([m["id"] for m in state.chat_messages], [40])

    def test_back_to_list(self) -> None:
        state = _state(mobile_view="conversation")
        ChatState.back_to_list.fn(state)
        self.assertEqual(state.mobile_view, "list")

    # 4.5 ------------------------------------------------------------------

    def test_empty_text_does_not_call_endpoint(self) -> None:
        state = _state(active_conversation_id=7)
        recorder = _Recorder(_json(200, _message(9, mine=True)))
        with self._patch_client(recorder):
            _run(ChatState.send_message.fn(state, {"message_text": "   "}))
        self.assertEqual(recorder.requests, [])

    def test_too_long_text_is_rejected_locally(self) -> None:
        state = _state(active_conversation_id=7)
        recorder = _Recorder(_json(200, _message(9, mine=True)))
        with self._patch_client(recorder):
            _run(ChatState.send_message.fn(state, {"message_text": "a" * 1001}))
        self.assertEqual(recorder.requests, [])
        self.assertEqual(state.send_error, SEND_INVALID_MESSAGE)

    def test_successful_send_appends_clears_field_and_moves_conversation(self) -> None:
        state = _state(
            active_conversation_id=7,
            chat_messages=_decorated(5),
            chat_conversations=[_conversation(3), _conversation(7)],
        )
        recorder = _Recorder(_json(200, _message(9, mine=True, text="Olá! Ainda está disponível?")))
        with (
            self._patch_client(recorder),
            patch("doafacil.chat.rx.set_value", return_value="clear-input") as set_value,
        ):
            result = _run(ChatState.send_message.fn(state, {"message_text": "  Olá! Ainda está disponível?  "}))
        self.assertIn(b'"message_text":"Ol', recorder.requests[0].read())
        self.assertEqual(result, "clear-input")
        set_value.assert_called_once_with(MESSAGE_INPUT_ID, "")
        self.assertEqual([m["id"] for m in state.chat_messages], [5, 9])
        self.assertIs(state.chat_messages[-1]["sent_by_me"], True)
        self.assertEqual(state.chat_conversations[0]["conversation_id"], 7)
        self.assertFalse(state.is_sending)

    def test_send_errors_keep_text_and_show_friendly_messages(self) -> None:
        cases = [
            (400, {"code": "ERROR_CODE_INPUT_ERROR", "message": "x"}, SEND_INVALID_MESSAGE, False),
            (404, GENERIC_404, SEND_NOT_FOUND_MESSAGE, True),
            (429, CHAT_429, CHAT_RATE_LIMIT_MESSAGE, False),
            (429, PLATFORM_429, PLATFORM_RATE_LIMIT_MESSAGE, False),
        ]
        for status, body, expected, read_only in cases:
            with self.subTest(status=status, message=expected):
                state = _state(active_conversation_id=7, chat_messages=_decorated(5))
                with (
                    self._patch_client(_Recorder(_json(status, body))),
                    patch("doafacil.chat.rx.set_value") as set_value,
                ):
                    result = _run(ChatState.send_message.fn(state, {"message_text": "oi"}))
                self.assertIsNone(result)
                set_value.assert_not_called()
                self.assertEqual(state.send_error, expected)
                self.assertIs(state.read_only, read_only)
                self.assertEqual([m["id"] for m in state.chat_messages], [5])
                self.assertFalse(state.is_sending)

    def test_read_only_conversation_does_not_send(self) -> None:
        state = _state(active_conversation_id=7, read_only=True)
        recorder = _Recorder(_json(200, _message(9, mine=True)))
        with self._patch_client(recorder):
            _run(ChatState.send_message.fn(state, {"message_text": "oi"}))
        self.assertEqual(recorder.requests, [])

    # 4.6 ------------------------------------------------------------------

    def test_poll_tick_checks_visibility_only_when_allowed(self) -> None:
        with (
            patch("doafacil.chat.rx.call_script", return_value="check-visibility") as call_script,
            patch("doafacil.chat._now", return_value=1000.0),
        ):
            self.assertIsNone(ChatState.poll_tick.fn(_state(active_conversation_id=0)))
            self.assertIsNone(ChatState.poll_tick.fn(_state(active_conversation_id=7, poll_paused_until=1030.0)))
            self.assertEqual(ChatState.poll_tick.fn(_state(active_conversation_id=7)), "check-visibility")
        self.assertEqual(call_script.call_count, 1)
        self.assertEqual(call_script.call_args.args[0], "document.visibilityState")

    def test_poll_with_hidden_tab_makes_no_request(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=_decorated(5))
        recorder = _Recorder(_json(200, _messages_page([_message(6)])))
        with self._patch_client(recorder):
            _run(ChatState.poll_if_visible.fn(state, "hidden"))
        self.assertEqual(recorder.requests, [])

    def test_poll_fetches_only_new_messages_with_after_cursor(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=_decorated(5, 6))
        # Resposta repete a 6 para provar que não duplica.
        recorder = _Recorder(_json(200, _messages_page([_message(6), _message(7)], has_newer=False)))
        with self._patch_client(recorder):
            _run(ChatState.poll_if_visible.fn(state, "visible"))
        params = recorder.requests[0].url.params
        self.assertEqual(params["after_message_id"], "6")
        self.assertEqual(params["limit"], "100")
        self.assertNotIn("before_message_id", params)
        self.assertEqual([m["id"] for m in state.chat_messages], [5, 6, 7])

    def test_poll_rate_limit_pauses_silently(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=_decorated(5))
        with (
            self._patch_client(_Recorder(_json(429, PLATFORM_429))),
            patch("doafacil.chat._now", return_value=1000.0),
        ):
            result = _run(ChatState.poll_if_visible.fn(state, "visible"))
        self.assertIsNone(result)
        self.assertEqual(state.poll_paused_until, 1000.0 + POLL_PAUSE_SECONDS)
        self.assertEqual(state.send_error, "")
        self.assertEqual(state.conversation_error, "")

        recorder = _Recorder(_json(200, _messages_page([])))
        with self._patch_client(recorder), patch("doafacil.chat._now", return_value=1030.0):
            _run(ChatState.poll_if_visible.fn(state, "visible"))
        self.assertEqual(recorder.requests, [])

    def test_poll_switches_to_read_only_when_donation_is_completed(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=_decorated(5))
        recorder = _Recorder(_json(200, _messages_page([], status="concluída")))
        with self._patch_client(recorder):
            _run(ChatState.poll_if_visible.fn(state, "visible"))
        self.assertTrue(state.read_only)

    def test_poll_401_clears_session(self) -> None:
        state = _state(active_conversation_id=7, chat_messages=_decorated(5))
        with (
            self._patch_client(_Recorder(_json(401, {"message": "x"}))),
            patch("doafacil.chat.rx.redirect", return_value="login-redirect"),
        ):
            result = _run(ChatState.poll_if_visible.fn(state, "visible"))
        self.assertEqual(result, "login-redirect")
        self.assertEqual(state.auth_token, "")


def _nodes(component: object) -> list[object]:
    found: list[object] = []

    def collect(value: object) -> None:
        if hasattr(value, "children"):
            found.append(value)
            collect(value.children)
            for attr in ("cond", "comp1", "comp2"):
                if hasattr(value, attr):
                    collect(getattr(value, attr))
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return found


class ChatPageTests(unittest.TestCase):
    def setUp(self) -> None:
        from doafacil.chat import chat_page

        self.page = chat_page()
        self.rendered = str(self.page)

    def test_route_is_registered_with_load_event(self) -> None:
        from doafacil.doafacil import app

        self.assertIn("chat", app._unevaluated_pages)
        self.assertEqual(app._unevaluated_pages["chat"].route, "chat")

    def test_fixed_texts_are_present(self) -> None:
        from doafacil.chat import (
            EMPTY_CONVERSATION_MESSAGE,
            EMPTY_LIST_MESSAGE,
            NO_CONVERSATION_MESSAGE,
            READ_ONLY_MESSAGE,
        )

        expected = [
            "Digite aqui...",
            "Enviar",
            "Carregar anteriores",
            "Carregar mais conversas",
            "Voltar \\u00e0s conversas",
            "Tentar novamente",
        ]
        for text in expected:
            with self.subTest(text=text):
                self.assertIn(text, self.rendered)
        for text in (EMPTY_LIST_MESSAGE, NO_CONVERSATION_MESSAGE, EMPTY_CONVERSATION_MESSAGE, READ_ONLY_MESSAGE):
            with self.subTest(text=text):
                escaped = text.encode("ascii", "backslashreplace").decode().replace("\\x", "\\u00")
                self.assertTrue(text in self.rendered or escaped in self.rendered)

    def test_entry_animation_and_no_online_or_photos(self) -> None:
        self.assertIn("page-fade-enter", self.rendered)
        self.assertNotIn("Online", self.rendered)
        # Avatares são círculos com a inicial; a única imagem é o logotipo.
        images = [n for n in _nodes(self.page) if type(n).__name__ in {"Img", "Image"}]
        self.assertEqual(len(images), 1)
        # O item da lista (renderizado pelo foreach) também não tem imagem.
        from doafacil.chat import ChatState, _conversation_item

        item = _conversation_item(ChatState.chat_conversations[0])
        self.assertFalse([n for n in _nodes(item) if type(n).__name__ in {"Img", "Image"}])

    def test_message_input_limits_length_and_form_sends(self) -> None:
        inputs = [n for n in _nodes(self.page) if getattr(n, "id", None) is not None and "chat-message-input" in str(n.id)]
        self.assertEqual(len(inputs), 1)
        self.assertIn("maxLength:1000", self.rendered)
        self.assertIn('type:"submit"', self.rendered)

    def test_enter_submits_because_input_and_button_are_inside_the_form(self) -> None:
        # Enter num campo de formulário dispara o submit nativo; isso só
        # funciona com o campo e o botão type="submit" dentro do mesmo form.
        forms = [n for n in _nodes(self.page) if type(n).__name__ == "Form"]
        self.assertEqual(len(forms), 1)
        form = forms[0]
        rendered_form = str(form)
        self.assertIn("chat-message-input", rendered_form)
        self.assertIn('type:"submit"', rendered_form)
        self.assertIn("onSubmit", rendered_form)
        self.assertIn("send_message", str(form.event_triggers["on_submit"]))

    def test_layout_paddings_and_back_link_in_header(self) -> None:
        from doafacil.chat import _conversation_item, _header, _messages_area, ChatState

        header = str(_header())
        self.assertIn('"aria-label":"Voltar ao in\\u00edcio"', header)
        self.assertIn('to:"/"', header)
        self.assertIn('"padding"] : "16px 24px"', str(_messages_area()))
        self.assertIn('"padding"] : "8px 16px"', str(_conversation_item(ChatState.chat_conversations[0])))
        # Sem a faixa separada da seta abaixo do cabeçalho.
        self.assertEqual(self.rendered.count("Voltar ao in\\u00edcio"), 2)

    def test_bubble_shows_send_time_below_in_small_gray_text(self) -> None:
        from doafacil.chat import ChatState, _message_bubble

        bubble = _message_bubble(ChatState.chat_messages[0])
        times = [
            n
            for n in _nodes(bubble)
            if type(n).__name__ == "Text" and "time_label" in str(n)
        ]
        self.assertEqual(len(times), 1)
        rendered_time = str(times[0])
        self.assertIn('"color"] : "#6b6b6b"', rendered_time)
        self.assertIn('"fontSize"] : "0.7rem"', rendered_time)
        # A bolha e o horário ficam numa coluna alinhada ao lado de quem enviou.
        rendered = str(bubble)
        self.assertIn('direction:"column"', rendered)
        self.assertIn("sent_by_me", rendered)

    def test_message_input_disables_browser_autocomplete(self) -> None:
        self.assertIn('autoComplete:"off"', self.rendered)

    def test_poller_only_exists_with_open_conversation(self) -> None:
        moments = [n for n in _nodes(self.page) if type(n).__name__ == "Moment"]
        # Um das mensagens (15 s, com conversa aberta) e um da lista (30 s).
        self.assertEqual(len(moments), 2)
        self.assertIn("interval:15000", self.rendered)
        conds_with_moment = [
            n
            for n in _nodes(self.page)
            if type(n).__name__ == "Cond"
            and "Moment" in str(n)
            and "active_conversation_id" in str(n)
        ]
        self.assertTrue(conds_with_moment)

    def test_list_poller_is_always_mounted_every_30_seconds(self) -> None:
        moments = [n for n in _nodes(self.page) if type(n).__name__ == "Moment"]
        list_moments = [m for m in moments if "list_poll_tick" in str(m.event_triggers.get("on_change"))]
        self.assertEqual(len(list_moments), 1)
        self.assertIn("interval:30000", str(list_moments[0]))
        # Fora de qualquer cond: não depende de conversa aberta.
        conds = [n for n in _nodes(self.page) if type(n).__name__ == "Cond"]
        self.assertFalse([c for c in conds if "list_poll_tick" in str(c)])

    def test_conversation_item_shows_green_badge_only_with_unread(self) -> None:
        from doafacil.chat import ChatState, _conversation_item

        item = _conversation_item(ChatState.chat_conversations[0])
        badge_conds = [
            n for n in _nodes(item) if type(n).__name__ == "Cond" and "chat-unread-badge" in str(n)
        ]
        self.assertEqual(len(badge_conds), 1)
        cond = badge_conds[0]
        # Oculto com 0: a condição é o texto do contador não vazio.
        condition = str(cond.cond)
        self.assertIn('["unread_text"]', condition)
        self.assertTrue(condition.startswith("!(") and '=== ""' in condition.replace("?.valueOf?.()", ""))
        rendered = str(cond.children[0])
        self.assertIn('"#007A42"', rendered)
        self.assertIn('"white"', rendered)
        self.assertIn("unread_text", rendered)
        self.assertIn('role:"img"', rendered)
        self.assertIn('"aria-label":', rendered)
        self.assertIn("unread_label", rendered)
        self.assertNotIn("chat-unread-badge", str(cond.children[1]))
        # O contador fica à direita: depois do nome e do título.
        row = str(item)
        self.assertLess(row.index("donation_title"), row.index("chat-unread-badge"))

    def _bubble(self) -> object:
        from doafacil.chat import ChatState, _message_bubble

        return _message_bubble(ChatState.chat_messages[0])

    def test_read_status_on_time_line_only_for_own_messages(self) -> None:
        bubble = self._bubble()
        status_conds = [
            n
            for n in _nodes(bubble)
            if type(n).__name__ == "Cond"
            and "chat-read-status" in str(n)
            and "sent_by_me" in str(getattr(n, "cond", ""))
        ]
        self.assertEqual(len(status_conds), 1)
        mine, other = status_conds[0].children
        self.assertNotIn("chat-read-status", str(other))
        rendered = str(mine)
        self.assertIn("is_read", rendered)
        # ✓✓ verde “Lida” e ✓ cinza “Enviada”.
        self.assertIn("LucideCheckCheck", rendered)
        self.assertIn('"#007A42"', rendered)
        self.assertIn('"aria-label":"Lida"', rendered)
        self.assertIn("LucideCheck,", rendered)
        self.assertIn('"#6b6b6b"', rendered)
        self.assertIn('"aria-label":"Enviada"', rendered)
        self.assertIn('role:"img"', rendered)

    def test_time_line_holds_time_edited_label_and_status_outside_bubble(self) -> None:
        bubble = self._bubble()
        stacks = [
            n
            for n in _nodes(bubble)
            if type(n).__name__ == "HStack"
            and "time_label" in str(n)
            and "chat-read-status" in str(n)
        ]
        self.assertEqual(len(stacks), 1)
        line = str(stacks[0])
        self.assertIn("(editada)", line)
        self.assertIn('["edited"]', line)
        # A linha não fica dentro da bolha (o texto da mensagem não está nela).
        self.assertNotIn('["text"]', line)

    def test_pencil_only_on_editable_messages_with_hover_and_tap_hooks(self) -> None:
        bubble = self._bubble()
        pencil_conds = [
            n
            for n in _nodes(bubble)
            if type(n).__name__ == "Cond"
            and "chat-edit-btn" in str(n)
            and "editable" in str(getattr(n, "cond", ""))
        ]
        self.assertEqual(len(pencil_conds), 1)
        pencil = str(pencil_conds[0].children[0])
        self.assertIn('"aria-label":"Editar mensagem"', pencil)
        self.assertIn('type:"button"', pencil)
        self.assertIn("start_edit", pencil)
        self.assertNotIn("chat-edit-btn", str(pencil_conds[0].children[1]))
        rendered = str(bubble)
        self.assertIn("chat-bubble-row", rendered)
        self.assertIn('"data-selected"', rendered)
        self.assertIn("selected_message_id", rendered)
        self.assertIn("toggle_message_selection", rendered)

    def test_composer_edit_mode_with_save_cancel_and_escape(self) -> None:
        from doafacil.chat import _composer

        rendered = str(_composer())
        for text in ("Editando mensagem", "Salvar", "Cancelar", "Enviar", "(Esc cancela)"):
            with self.subTest(text=text):
                self.assertIn(text, rendered)
        self.assertIn("editing_message_id", rendered)
        self.assertIn("cancel_edit", rendered)
        self.assertIn("composer_key_down", rendered)
        self.assertIn("onKeyDown", rendered)
        # Salvar continua sendo o submit do mesmo formulário (Enter salva).
        forms = [n for n in _nodes(_composer()) if type(n).__name__ == "Form"]
        self.assertEqual(len(forms), 1)
        self.assertIn('type:"submit"', str(forms[0]))

    def test_chat_css_shows_pencil_on_hover_focus_and_selection(self) -> None:
        from pathlib import Path

        from doafacil.doafacil import app

        css = (Path(__file__).resolve().parents[1] / "assets" / "chat.css").read_text(encoding="utf-8")
        self.assertIn(".chat-edit-btn {\n  opacity: 0;\n  pointer-events: none;", css)
        self.assertIn("@media (hover: hover)", css)
        self.assertIn(".chat-bubble-row:hover .chat-edit-btn", css)
        self.assertIn(".chat-edit-btn:focus-visible", css)
        self.assertIn('.chat-bubble-row[data-selected="true"] .chat-edit-btn', css)
        # O lápis não tem transição (nada a desligar com reduced-motion).
        pencil_css = css.split("/* Botão flutuante")[0]
        self.assertNotIn("transition", pencil_css)
        self.assertIn("/chat.css", app.stylesheets)

    def test_chat_content_is_never_rendered_as_html(self) -> None:
        kinds = {type(n).__name__ for n in _nodes(self.page)}
        self.assertNotIn("Html", kinds)
        self.assertNotIn("Markdown", kinds)
        self.assertNotIn("dangerouslySetInnerHTML", self.rendered)


def _contrast(foreground: str, background: str) -> float:
    def luminance(hex_color: str) -> float:
        channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


class ChatFabTests(unittest.TestCase):
    """Botão flutuante “Mensagens” (change chat-botao-flutuante)."""

    def setUp(self) -> None:
        from doafacil.chat import chat_fab

        self.fab = chat_fab()
        self.rendered = str(self.fab)

    def test_destination_and_label_depend_on_login(self) -> None:
        self.assertEqual(type(self.fab).__name__, "Link")
        self.assertIn('"/chat"', self.rendered)
        self.assertIn('"/login"', self.rendered)
        self.assertIn("auth_token", self.rendered)
        # Com login: "Mensagens" ou "Mensagens, N não lidas"; sem: "Mensagens".
        self.assertIn("unread_link_label", self.rendered)
        self.assertIn('"Mensagens"', self.rendered)
        self.assertIn('"aria-label":', self.rendered)

    def test_appearance_and_position(self) -> None:
        self.assertIn("chat-fab", str(self.fab.class_name))
        self.assertIn("LucideMessageCircle", self.rendered)
        self.assertIn('"position"] : "fixed"', self.rendered)
        self.assertIn('"width"] : "56px"', self.rendered)
        self.assertIn('"height"] : "56px"', self.rendered)
        self.assertIn('"background"] : "#007A42"', self.rendered)
        self.assertIn('"0 4px 12px rgba(0, 0, 0, 0.2)"', self.rendered)
        # 16 px das bordas no celular, 24 px no computador.
        for side in ("bottom", "right"):
            with self.subTest(side=side):
                self.assertIn(f'["{side}"] : "16px"', self.rendered)
                self.assertIn(f'["{side}"] : "24px"', self.rendered)
        # Ícone branco sobre o verde: acima de 3:1 (não texto) e até do AA.
        self.assertGreaterEqual(_contrast("#FFFFFF", "#007A42"), 4.5)

    def test_red_badge_only_with_login_and_unread(self) -> None:
        badges = [
            node
            for node in _nodes(self.fab)
            if type(node).__name__ == "Cond" and "chat-unread-badge" in str(node)
        ]
        self.assertEqual(len(badges), 1)
        condition = str(badges[0].cond)
        self.assertIn("auth_token", condition)
        self.assertIn("unread_total_rx_state_ > 0", condition)
        self.assertNotIn("chat-unread-badge", str(badges[0].children[1]))
        badge = str(badges[0].children[0])
        self.assertIn("unread_total_text", badge)  # já vem com "99+"
        self.assertIn('"#C62828"', badge)
        self.assertIn('"position"] : "absolute"', badge)
        # O total está no rótulo do link: o círculo fica oculto.
        self.assertIn('"aria-hidden":"true"', badge)
        self.assertGreaterEqual(_contrast("#FFFFFF", "#C62828"), 4.5)

    def test_badge_keeps_green_by_default(self) -> None:
        from doafacil.chat import unread_badge

        rendered = str(unread_badge("3"))
        self.assertIn('"#007A42"', rendered)
        self.assertNotIn("#C62828", rendered)

    def test_css_highlight_focus_and_reduced_motion(self) -> None:
        from pathlib import Path

        css = (Path(__file__).resolve().parents[1] / "assets" / "chat.css").read_text(encoding="utf-8")
        fab_css = css.split("/* Botão flutuante")[1]
        self.assertIn(".chat-fab {\n  transition:", fab_css)
        self.assertIn(".chat-fab:hover", fab_css)
        self.assertIn(".chat-fab:focus-visible {\n  outline: 2px solid #1F1F1F;", fab_css)
        reduced = fab_css.split("@media (prefers-reduced-motion: reduce)")[1]
        self.assertIn("transition: none;", reduced)
        self.assertIn("transform: none;", reduced)

    def test_clearance_reserved_at_the_end_of_the_home(self) -> None:
        from doafacil.doafacil import public_home_footer

        footer = str(public_home_footer())
        self.assertIn('["paddingBottom"] : "88px"', footer)
        self.assertIn('["paddingBottom"] : "104px"', footer)

    def test_button_absent_from_excluded_pages(self) -> None:
        import doafacil.doafacil as main
        from doafacil.detalhe_doacao import donation_detail_page

        pages = {
            # O detalhe já tem o botão “Chat” da doação; dois confundem.
            "/doacao/<id>": donation_detail_page,
            "/chat": main.chat_page,
            "/login": main.login_page,
            "/cadastro": main.signup_page,
            "/verificar-email": main.verify_recovery_page,
            "/recuperar-senha": main.request_recovery_page,
            "/nova-senha": main.new_password_page,
            "/cadastro-doacao": main.donation_creation_page,
        }
        for route, page in pages.items():
            with self.subTest(route=route):
                self.assertNotIn("chat-fab", str(page()))


if __name__ == "__main__":
    unittest.main()
