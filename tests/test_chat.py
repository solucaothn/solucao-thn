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
    time_label,
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
    }
    item.update(overrides)
    return item


def _messages_page(
    messages: list[dict[str, Any]],
    *,
    status: str = "disponível",
    has_older: bool = False,
    has_newer: bool = False,
) -> dict[str, Any]:
    return {
        "messages": messages,
        "donation_title": "Carrinho de brinquedo",
        "donation_status": status,
        "has_older": has_older,
        "has_newer": has_newer,
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
    }
    values.update(overrides)
    return SimpleNamespace(**values)


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
        self.assertEqual(len(moments), 1)
        self.assertIn("interval:15000", self.rendered)
        conds_with_moment = [
            n
            for n in _nodes(self.page)
            if type(n).__name__ == "Cond"
            and "Moment" in str(n)
            and "active_conversation_id" in str(n)
        ]
        self.assertTrue(conds_with_moment)

    def test_chat_content_is_never_rendered_as_html(self) -> None:
        kinds = {type(n).__name__ for n in _nodes(self.page)}
        self.assertNotIn("Html", kinds)
        self.assertNotIn("Markdown", kinds)
        self.assertNotIn("dangerouslySetInnerHTML", self.rendered)


if __name__ == "__main__":
    unittest.main()
