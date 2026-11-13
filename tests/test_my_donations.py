import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx

from doafacil.chat import back_link_header
from doafacil.detalhe_doacao import DONATION_NOT_FOUND_MESSAGE
from doafacil.doafacil import app, index
from doafacil.minhas_doacoes import (
    ACTION_COMPLETE,
    ACTION_DELETE,
    ACTION_MAKE_AVAILABLE,
    ACTION_NOT_FOUND_MESSAGE,
    ACTION_REJECTED_MESSAGE,
    ACTION_RESERVE,
    ACTION_SUCCESS_MESSAGES,
    EDIT_COMPLETED_MESSAGE,
    EDIT_ERROR_MESSAGE,
    EMPTY_TITLE,
    LIST_ERROR_MESSAGE,
    PAGE_ERROR_MESSAGE,
    RATE_LIMIT_MESSAGE,
    SAVE_ERROR_MESSAGE,
    SAVE_NOT_FOUND_MESSAGE,
    SAVE_REJECTED_MESSAGE,
    SAVED_MESSAGE,
    STATUS_BADGE_COLORS,
    EditDonationState,
    MyDonationNotFoundError,
    MyDonationRejectedError,
    MyDonationsRateLimitError,
    MyDonationsServiceError,
    MyDonationsState,
    MyDonationsUnauthorizedError,
    _actions_menu,
    _confirm_dialog,
    _edit_form,
    _empty_state,
    _owner_card,
    _pagination,
    _parse_my_donation,
    _parse_my_donations,
    _validate_edit,
    change_status,
    delete_donation,
    edit_donation_page,
    fetch_my_donation,
    fetch_my_donations,
    my_donation_card,
    my_donations_page,
    update_donation,
)


BASE_URL = "https://xano.example/api:catalog"
TOKEN = "token-de-teste"

LIST_PAYLOAD = {
    "owner": {"first_name": "Ana"},
    "counts": {"active": 2, "completed": 1},
    "items": [
        {"id": 17, "created_at": 1_700_000_000_000, "title": "Carrinho", "photo": "https://img.example/a.jpg", "condition": "Bom", "status": "disponível"},
        {"id": 12, "created_at": 1_690_000_000_000, "title": "Livro", "photo": None, "condition": None, "status": "reservada"},
        {"id": 9, "created_at": 1_680_000_000_000, "title": "Mesa", "photo": None, "condition": "Ótimo", "status": "concluída"},
    ],
    "page": 1,
    "per_page": 6,
    "total": 3,
    "page_total": 1,
}

ITEM_PAYLOAD = {
    "id": 17,
    "title": "Carrinho",
    "description": "Em bom estado.",
    "category_id": 3,
    "condition": "Bom",
    "delivery_method": "A combinar",
    "contact_preference": "E-mail",
    "status": "disponível",
}

CATEGORIES = [{"id": 3, "name": "Brinquedos"}, {"id": 4, "name": "Livros"}]


def _run(coro):
    return asyncio.run(coro)


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _call(handler, function, *args):
    async def run():
        async with _client(handler) as client:
            return await function(client, TOKEN, *args)

    with patch.dict("os.environ", {"XANO_API_URL": BASE_URL}):
        return _run(run())


def _events(generator) -> list:
    async def run():
        return [event async for event in generator]

    return _run(run())


def _list_state(**fields) -> SimpleNamespace:
    base = dict(
        auth_token=TOKEN,
        account_name="Ana",
        view_state="loading",
        load_error="",
        first_name="",
        initial="",
        active_count=0,
        completed_count=0,
        items=[],
        total=0,
        page=1,
        page_total=0,
        page_loading=False,
        page_error="",
        notice="",
        notice_is_error=False,
        flash="",
        action_busy=False,
        confirm_open=False,
        pending_kind="",
        pending_id=0,
        pending_title="",
    )
    base.update(fields)
    return SimpleNamespace(**base)


def _ready_list_state(**fields) -> SimpleNamespace:
    ready = dict(
        view_state="ready",
        first_name="Ana",
        items=[{"id": 1}],
        total=13,
        page=1,
        page_total=3,
        active_count=10,
        completed_count=3,
    )
    ready.update(fields)
    return _list_state(**ready)


def _edit_state(route_id: str = "17", **fields) -> SimpleNamespace:
    base = dict(
        router=SimpleNamespace(page=SimpleNamespace(params={"id": route_id})),
        auth_token=TOKEN,
        account_name="Ana",
        view_state="loading",
        load_error="",
        donation_id=0,
        title="",
        description="",
        category_id="",
        category_name="",
        condition="",
        delivery_method="",
        contact_preference="",
        categories=[],
        form_error="",
        is_saving=False,
    )
    base.update(fields)
    return SimpleNamespace(**base)


def _ready_edit_state(**fields) -> SimpleNamespace:
    ready = dict(
        view_state="ready",
        donation_id=17,
        title="Carrinho",
        description="Em bom estado.",
        category_id="3",
        category_name="Brinquedos",
        condition="Bom",
        delivery_method="A combinar",
        contact_preference="E-mail",
        categories=CATEGORIES,
    )
    ready.update(fields)
    return _edit_state(**ready)


def _contents(component) -> list[str]:
    found: list[str] = []

    def collect(value) -> None:
        if hasattr(value, "contents"):
            text = value.contents
            if isinstance(text, str):
                found.append(text)
            elif type(text).__name__ == "LiteralStringVar":
                found.append(text._var_value)
        if hasattr(value, "children"):
            collect(value.children)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return found


def _nodes(component) -> list:
    nodes: list = []

    def collect(value) -> None:
        if hasattr(value, "tag") or hasattr(value, "component_name"):
            nodes.append(value)
        if hasattr(value, "children"):
            collect(value.children)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return nodes


def _computed(name: str, state: SimpleNamespace):
    return MyDonationsState.computed_vars[name].fget(state)


def _luminance(color: str) -> float:
    channels = [int(color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground: str, background: str) -> float:
    a, b = _luminance(foreground), _luminance(background)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


class MyDonationsClientTests(unittest.TestCase):
    def test_list_sends_token_and_page(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api:catalog/catalog/donations/mine")
            self.assertEqual(request.url.params.get("page"), "2")
            self.assertEqual(request.headers.get("Authorization"), f"Bearer {TOKEN}")
            return httpx.Response(200, json={**LIST_PAYLOAD, "page": 2})

        data = _call(handler, fetch_my_donations, 2)
        self.assertEqual(data["page"], 2)
        self.assertEqual((data["active"], data["completed"]), (2, 1))
        self.assertEqual(data["first_name"], "Ana")

    def test_list_items_have_status_label_condition_and_generic_photo(self) -> None:
        data = _parse_my_donations(LIST_PAYLOAD)
        first, second, third = data["items"]
        self.assertEqual(first["status_label"], "Disponível")
        self.assertEqual(second["status_label"], "Reservada")
        self.assertEqual(third["status_label"], "Concluída")
        self.assertEqual(first["condition_label"], "Condição: Bom")
        self.assertEqual(second["condition_label"], "Condição não informada")
        self.assertEqual(second["photo"], "/doacao-generica.svg")
        self.assertNotIn("is_new", first)

    def test_list_ignores_extra_fields(self) -> None:
        payload = {
            **LIST_PAYLOAD,
            "email": "x@y.z",
            "owner": {"first_name": "Ana", "email": "x@y.z", "owner_id": 9},
            "items": [{**LIST_PAYLOAD["items"][0], "owner_id": 9}],
        }
        data = _parse_my_donations(payload)
        self.assertEqual(
            set(data),
            {"first_name", "active", "completed", "items", "page", "total", "page_total"},
        )
        self.assertEqual(
            set(data["items"][0]),
            {"id", "title", "photo", "condition_label", "status", "status_label"},
        )
        self.assertNotIn("x@y.z", repr(data))

    def test_invalid_list_responses_raise(self) -> None:
        cases = {
            "lista": [],
            "sem owner": {k: v for k, v in LIST_PAYLOAD.items() if k != "owner"},
            "nome vazio": {**LIST_PAYLOAD, "owner": {"first_name": " "}},
            "contador negativo": {**LIST_PAYLOAD, "counts": {"active": -1, "completed": 0}},
            "contador booleano": {**LIST_PAYLOAD, "counts": {"active": True, "completed": 0}},
            "página 0": {**LIST_PAYLOAD, "page": 0},
            "itens não lista": {**LIST_PAYLOAD, "items": {}},
            "status inválido": {**LIST_PAYLOAD, "items": [{**LIST_PAYLOAD["items"][0], "status": "x"}]},
        }
        for label, payload in cases.items():
            with self.subTest(case=label):
                with self.assertRaises(MyDonationsServiceError):
                    _parse_my_donations(payload)

    def test_status_codes_map_to_errors(self) -> None:
        cases = {
            401: MyDonationsUnauthorizedError,
            403: MyDonationNotFoundError,
            404: MyDonationNotFoundError,
            400: MyDonationRejectedError,
            429: MyDonationsRateLimitError,
            500: MyDonationsServiceError,
        }
        for status, error in cases.items():
            with self.subTest(status=status):
                with self.assertRaises(error):
                    _call(lambda request, s=status: httpx.Response(s, json={}), fetch_my_donations, 1)

    def test_non_json_response_is_service_error(self) -> None:
        with self.assertRaises(MyDonationsServiceError):
            _call(lambda request: httpx.Response(200, text="<html>"), fetch_my_donations, 1)

    def test_missing_base_url_is_service_error(self) -> None:
        async def run():
            async with _client(lambda r: httpx.Response(200)) as client:
                await fetch_my_donations(client, TOKEN, 1)

        with patch.dict("os.environ", {"XANO_API_URL": ""}):
            with self.assertRaises(MyDonationsServiceError):
                _run(run())

    def test_fetch_my_donation_reads_editable_fields(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api:catalog/catalog/donations/mine/item")
            self.assertEqual(request.url.params.get("donation_id"), "17")
            self.assertEqual(request.headers.get("Authorization"), f"Bearer {TOKEN}")
            return httpx.Response(200, json={**ITEM_PAYLOAD, "owner_id": 9})

        donation = _call(handler, fetch_my_donation, 17)
        self.assertEqual(donation["category_id"], 3)
        self.assertNotIn("owner_id", donation)
        with self.assertRaises(MyDonationsServiceError):
            _parse_my_donation({**ITEM_PAYLOAD, "id": 18}, 17)
        with self.assertRaises(MyDonationsServiceError):
            _parse_my_donation({**ITEM_PAYLOAD, "status": "x"}, 17)

    def test_change_status_sends_patch(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "PATCH")
            self.assertEqual(request.url.path, "/api:catalog/catalog/donations/status")
            self.assertEqual(request.headers.get("Authorization"), f"Bearer {TOKEN}")
            self.assertIn(b'"status":"reservada"', request.content.replace(b" ", b""))
            return httpx.Response(200, json={"id": 17, "status": "reservada"})

        self.assertEqual(_call(handler, change_status, 17, "reservada"), "reservada")
        with self.assertRaises(MyDonationsServiceError):
            _call(lambda r: httpx.Response(200, json={"status": "disponível"}), change_status, 17, "reservada")

    def test_update_donation_sends_all_fields(self) -> None:
        fields = {key: ITEM_PAYLOAD[key] for key in ("category_id", "title", "description", "condition", "delivery_method", "contact_preference")}

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "PATCH")
            self.assertEqual(request.url.path, "/api:catalog/catalog/donations")
            body = request.read().decode("utf-8")
            for key in ("donation_id", *fields):
                self.assertIn(f'"{key}"', body)
            return httpx.Response(200, json={"id": 17})

        _call(handler, update_donation, 17, fields)

    def test_delete_donation_requires_confirmation_in_response(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "DELETE")
            self.assertEqual(request.url.params.get("donation_id"), "17")
            return httpx.Response(200, json={"deleted": True, "donation_id": 17})

        _call(handler, delete_donation, 17)
        with self.assertRaises(MyDonationsServiceError):
            _call(lambda r: httpx.Response(200, json={"deleted": False}), delete_donation, 17)


class MyDonationsStateTests(unittest.TestCase):
    def test_without_token_redirects_to_login_without_request(self) -> None:
        state = _list_state(auth_token="")
        with (
            patch("doafacil.minhas_doacoes.rx.redirect", return_value="login") as redirect,
            patch("doafacil.minhas_doacoes.fetch_my_donations", new_callable=AsyncMock) as fetch,
        ):
            events = _events(MyDonationsState.load_page.fn(state))
        self.assertEqual(events, ["login"])
        redirect.assert_called_once_with("/login")
        fetch.assert_not_called()

    def test_load_page_fills_owner_counts_and_items(self) -> None:
        state = _list_state(flash=SAVED_MESSAGE)
        with patch(
            "doafacil.minhas_doacoes.fetch_my_donations",
            new_callable=AsyncMock,
            return_value=_parse_my_donations(LIST_PAYLOAD),
        ) as fetch:
            _events(MyDonationsState.load_page.fn(state))
        self.assertEqual(fetch.await_args.args[1:], (TOKEN, 1))
        self.assertEqual(state.view_state, "ready")
        self.assertEqual((state.first_name, state.initial), ("Ana", "A"))
        self.assertEqual((state.active_count, state.completed_count), (2, 1))
        self.assertEqual([item["id"] for item in state.items], [17, 12, 9])
        # O aviso da edição aparece uma vez.
        self.assertEqual(state.notice, SAVED_MESSAGE)
        self.assertEqual(state.flash, "")

    def test_load_page_errors(self) -> None:
        cases = (
            (MyDonationsRateLimitError(), RATE_LIMIT_MESSAGE),
            (MyDonationsServiceError(), LIST_ERROR_MESSAGE),
            (httpx.ConnectError("x"), LIST_ERROR_MESSAGE),
        )
        for error, message in cases:
            with self.subTest(error=type(error).__name__):
                state = _list_state(items=[{"id": 99}], first_name="Outra")
                with patch("doafacil.minhas_doacoes.fetch_my_donations", new_callable=AsyncMock, side_effect=error):
                    _events(MyDonationsState.load_page.fn(state))
                self.assertEqual(state.view_state, "error")
                self.assertEqual(state.load_error, message)
                self.assertEqual(state.items, [])
                self.assertEqual(state.first_name, "")

    def test_401_clears_session_and_redirects(self) -> None:
        state = _list_state()
        with (
            patch("doafacil.minhas_doacoes.rx.redirect", return_value="login"),
            patch("doafacil.minhas_doacoes.fetch_my_donations", new_callable=AsyncMock, side_effect=MyDonationsUnauthorizedError()),
        ):
            events = _events(MyDonationsState.load_page.fn(state))
        self.assertEqual(events, ["login"])
        self.assertEqual((state.auth_token, state.account_name), ("", ""))

    def test_go_to_page_requests_only_that_page(self) -> None:
        state = _ready_list_state()
        data = {**_parse_my_donations(LIST_PAYLOAD), "page": 2, "total": 13, "page_total": 3}
        with patch("doafacil.minhas_doacoes.fetch_my_donations", new_callable=AsyncMock, return_value=data) as fetch:
            _events(MyDonationsState.go_to_page.fn(state, 2))
        fetch.assert_awaited_once()
        self.assertEqual(fetch.await_args.args[1:], (TOKEN, 2))
        self.assertEqual(state.page, 2)
        self.assertFalse(state.page_loading)

    def test_go_to_page_ignores_invalid_or_busy(self) -> None:
        cases = {
            "0": (_ready_list_state(), 0),
            "além": (_ready_list_state(), 4),
            "atual": (_ready_list_state(), 1),
            "carregando": (_ready_list_state(page_loading=True), 2),
            "ação": (_ready_list_state(action_busy=True), 2),
        }
        for label, (state, page) in cases.items():
            with self.subTest(case=label):
                with patch("doafacil.minhas_doacoes.fetch_my_donations", new_callable=AsyncMock) as fetch:
                    _events(MyDonationsState.go_to_page.fn(state, page))
                fetch.assert_not_called()

    def test_go_to_page_error_keeps_previous_page(self) -> None:
        state = _ready_list_state()
        with patch("doafacil.minhas_doacoes.fetch_my_donations", new_callable=AsyncMock, side_effect=MyDonationsServiceError()):
            _events(MyDonationsState.go_to_page.fn(state, 2))
        self.assertEqual((state.page, state.items), (1, [{"id": 1}]))
        self.assertEqual(state.page_error, PAGE_ERROR_MESSAGE)
        self.assertFalse(state.page_loading)

    def test_reserve_and_make_available_run_without_confirmation(self) -> None:
        for kind, status in ((ACTION_RESERVE, "reservada"), (ACTION_MAKE_AVAILABLE, "disponível")):
            with self.subTest(kind=kind):
                state = _ready_list_state()
                with (
                    patch("doafacil.minhas_doacoes.change_status", new_callable=AsyncMock, return_value=status) as change,
                    patch("doafacil.minhas_doacoes.fetch_my_donations", new_callable=AsyncMock, return_value=_parse_my_donations(LIST_PAYLOAD)) as fetch,
                ):
                    _events(MyDonationsState.request_action.fn(state, kind, 17, "Carrinho"))
                self.assertEqual(change.await_args.args[1:], (TOKEN, 17, status))
                fetch.assert_awaited_once()
                self.assertFalse(state.confirm_open)
                self.assertEqual(state.notice, ACTION_SUCCESS_MESSAGES[kind])
                self.assertFalse(state.notice_is_error)
                self.assertFalse(state.action_busy)
                # Contadores atualizados pela recarga.
                self.assertEqual((state.active_count, state.completed_count), (2, 1))

    def test_complete_and_delete_open_confirmation_without_request(self) -> None:
        for kind in (ACTION_COMPLETE, ACTION_DELETE):
            with self.subTest(kind=kind):
                state = _ready_list_state()
                with (
                    patch("doafacil.minhas_doacoes.change_status", new_callable=AsyncMock) as change,
                    patch("doafacil.minhas_doacoes.delete_donation", new_callable=AsyncMock) as delete,
                ):
                    _events(MyDonationsState.request_action.fn(state, kind, 17, "Carrinho"))
                change.assert_not_called()
                delete.assert_not_called()
                self.assertTrue(state.confirm_open)
                self.assertEqual((state.pending_kind, state.pending_id, state.pending_title), (kind, 17, "Carrinho"))

    def test_cancel_makes_no_request(self) -> None:
        for cancel in (
            lambda s: MyDonationsState.cancel_action.fn(s),
            lambda s: MyDonationsState.set_confirm_open.fn(s, False),
        ):
            state = _ready_list_state(confirm_open=True, pending_kind=ACTION_DELETE, pending_id=17, pending_title="Carrinho")
            with patch("doafacil.minhas_doacoes.delete_donation", new_callable=AsyncMock) as delete:
                cancel(state)
            delete.assert_not_called()
            self.assertFalse(state.confirm_open)
            self.assertEqual((state.pending_kind, state.pending_id), ("", 0))

    def test_confirm_complete_and_delete(self) -> None:
        state = _ready_list_state(confirm_open=True, pending_kind=ACTION_COMPLETE, pending_id=17, pending_title="Carrinho")
        with (
            patch("doafacil.minhas_doacoes.change_status", new_callable=AsyncMock, return_value="concluída") as change,
            patch("doafacil.minhas_doacoes.fetch_my_donations", new_callable=AsyncMock, return_value=_parse_my_donations(LIST_PAYLOAD)),
        ):
            _events(MyDonationsState.confirm_action.fn(state))
        self.assertEqual(change.await_args.args[1:], (TOKEN, 17, "concluída"))
        self.assertEqual(state.notice, ACTION_SUCCESS_MESSAGES[ACTION_COMPLETE])
        self.assertFalse(state.confirm_open)

        state = _ready_list_state(confirm_open=True, pending_kind=ACTION_DELETE, pending_id=17, pending_title="Carrinho")
        with (
            patch("doafacil.minhas_doacoes.delete_donation", new_callable=AsyncMock) as delete,
            patch("doafacil.minhas_doacoes.fetch_my_donations", new_callable=AsyncMock, return_value=_parse_my_donations(LIST_PAYLOAD)),
        ):
            _events(MyDonationsState.confirm_action.fn(state))
        self.assertEqual(delete.await_args.args[1:], (TOKEN, 17))
        self.assertEqual(state.notice, ACTION_SUCCESS_MESSAGES[ACTION_DELETE])

    def test_delete_of_last_item_on_page_goes_back_one_page(self) -> None:
        state = _ready_list_state(page=3, pending_kind=ACTION_DELETE, pending_id=17, confirm_open=True)
        empty_page = {**_parse_my_donations(LIST_PAYLOAD), "items": [], "page": 3, "total": 12, "page_total": 2}
        page_two = {**_parse_my_donations(LIST_PAYLOAD), "page": 2, "total": 12, "page_total": 2}
        with (
            patch("doafacil.minhas_doacoes.delete_donation", new_callable=AsyncMock),
            patch("doafacil.minhas_doacoes.fetch_my_donations", new_callable=AsyncMock, side_effect=[empty_page, page_two]) as fetch,
        ):
            _events(MyDonationsState.confirm_action.fn(state))
        self.assertEqual([call.args[2] for call in fetch.await_args_list], [3, 2])
        self.assertEqual((state.page, state.page_total), (2, 2))

    def test_action_errors_keep_grid(self) -> None:
        cases = (
            (MyDonationNotFoundError(), ACTION_NOT_FOUND_MESSAGE),
            (MyDonationRejectedError(), ACTION_REJECTED_MESSAGE),
            (MyDonationsRateLimitError(), RATE_LIMIT_MESSAGE),
            (MyDonationsServiceError(), "Não foi possível concluir a ação. Tente novamente."),
        )
        for error, message in cases:
            with self.subTest(error=type(error).__name__):
                state = _ready_list_state()
                with (
                    patch("doafacil.minhas_doacoes.change_status", new_callable=AsyncMock, side_effect=error),
                    patch("doafacil.minhas_doacoes.fetch_my_donations", new_callable=AsyncMock) as fetch,
                ):
                    _events(MyDonationsState.request_action.fn(state, ACTION_RESERVE, 17, "Carrinho"))
                fetch.assert_not_called()
                self.assertEqual(state.items, [{"id": 1}])
                self.assertEqual(state.notice, message)
                self.assertTrue(state.notice_is_error)
                self.assertFalse(state.action_busy)

    def test_action_401_redirects_to_login(self) -> None:
        state = _ready_list_state()
        with (
            patch("doafacil.minhas_doacoes.rx.redirect", return_value="login"),
            patch("doafacil.minhas_doacoes.change_status", new_callable=AsyncMock, side_effect=MyDonationsUnauthorizedError()),
        ):
            events = _events(MyDonationsState.request_action.fn(state, ACTION_RESERVE, 17, "Carrinho"))
        self.assertIn("login", events)
        self.assertEqual(state.auth_token, "")

    def test_no_new_action_while_one_is_running(self) -> None:
        state = _ready_list_state(action_busy=True)
        with patch("doafacil.minhas_doacoes.change_status", new_callable=AsyncMock) as change:
            _events(MyDonationsState.request_action.fn(state, ACTION_RESERVE, 17, "Carrinho"))
        change.assert_not_called()
        self.assertFalse(state.confirm_open)

    def test_confirmation_texts(self) -> None:
        delete = _list_state(pending_kind=ACTION_DELETE, pending_title="Carrinho")
        complete = _list_state(pending_kind=ACTION_COMPLETE, pending_title="Carrinho")
        self.assertEqual(_computed("confirm_heading", delete), "Apagar esta doação?")
        self.assertIn("conversas e mensagens", _computed("confirm_text", delete))
        self.assertIn("não tem volta", _computed("confirm_text", delete))
        self.assertIn("“Carrinho”", _computed("confirm_text", delete))
        self.assertEqual(_computed("confirm_heading", complete), "Marcar como concluída?")
        self.assertIn("não poderá voltar a outro status", _computed("confirm_text", complete))
        self.assertIn("somente para leitura", _computed("confirm_text", complete))

    def test_counter_labels(self) -> None:
        self.assertEqual(_computed("active_label", _list_state(active_count=1)), "Doação")
        self.assertEqual(_computed("active_label", _list_state(active_count=2)), "Doações")
        self.assertEqual(_computed("completed_label", _list_state(completed_count=1)), "Doação realizada")
        self.assertEqual(_computed("completed_label", _list_state(completed_count=0)), "Doações realizadas")


class MyDonationsPageTests(unittest.TestCase):
    def test_routes_and_on_load(self) -> None:
        page = app._unevaluated_pages["minhas-doacoes"]
        self.assertEqual(page.on_load.fn, MyDonationsState.load_page.fn)
        edit = app._unevaluated_pages["minhas-doacoes/[id]/editar"]
        self.assertEqual(edit.on_load.fn, EditDonationState.load_edit.fn)

    def test_header_and_title(self) -> None:
        page = my_donations_page()
        header = page.children[0]
        self.assertEqual(str(header), str(back_link_header("/", "Voltar ao início", "#007A42")))
        rendered = str(page)
        self.assertIn("Minhas doa\\u00e7\\u00f5es", rendered)
        self.assertIn('as:"h1"', rendered)
        self.assertIn('"#166B3B"', rendered)
        # Sem o botão flutuante do chat.
        self.assertNotIn("chat-fab", rendered)

    def test_owner_card_has_initial_name_and_counters_only(self) -> None:
        card = _owner_card()
        rendered = str(card)
        for var in ("initial", "first_name", "active_count", "completed_count", "active_label", "completed_label"):
            with self.subTest(var=var):
                self.assertIn(f"{var}_rx_state_", rendered)
        self.assertNotIn("Image", [type(n).__name__ for n in _nodes(card)])

    def test_out_of_scope_items_are_absent(self) -> None:
        page = my_donations_page()
        contents = _contents(page)
        rendered = str(page)
        for excluded in ("Sobre", "Compartilhar", "Editar perfil", "Avaliação", "Verificado", "Chat", "Email", "E-mail", "Em breve", "NOVO"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, contents)
        for excluded in ("email", "owner_id", "LucideMessageCircle"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, rendered)

    def test_card_has_badge_condition_menu_and_view_link_only_when_available(self) -> None:
        rendered = str(my_donation_card(MyDonationsState.items[0]))
        self.assertIn('"status_label"', rendered)
        self.assertIn('"condition_label"', rendered)
        self.assertIn("Ver an\\u00fancio", rendered)
        self.assertIn('"/doacao/"', rendered)
        self.assertIn('"dispon\\u00edvel"', rendered)
        self.assertNotIn("NOVO", rendered)
        self.assertIn("my-donation-menu", rendered)

    def test_menu_actions_by_status_and_accessible_label(self) -> None:
        menu = _actions_menu(MyDonationsState.items[0])
        rendered = str(menu)
        contents = _contents(menu)
        for label in ("Marcar como reservada", "Marcar como disponível", "Marcar como concluída", "Editar", "Apagar"):
            with self.subTest(label=label):
                self.assertIn(label, contents)
        # Disponível: reservar, concluir, editar, apagar; reservada: disponível,
        # concluir, editar, apagar; concluída: só apagar (o caso padrão).
        self.assertEqual(contents.count("Marcar como reservada"), 1)
        self.assertEqual(contents.count("Marcar como disponível"), 1)
        self.assertEqual(contents.count("Marcar como concluída"), 2)
        self.assertEqual(contents.count("Apagar"), 3)
        self.assertIn("A\\u00e7\\u00f5es da doa\\u00e7\\u00e3o ", rendered)
        self.assertIn('"aria-label"', rendered)
        self.assertIn('"44px"', rendered)
        self.assertIn("/minhas-doacoes/", rendered)
        self.assertIn("/editar", rendered)
        self.assertIn("request_action", rendered)

    def test_status_badges_have_aa_contrast(self) -> None:
        for status, (background, text) in STATUS_BADGE_COLORS.items():
            with self.subTest(status=status):
                self.assertGreaterEqual(_contrast(text, background), 4.5)

    def test_confirm_dialog(self) -> None:
        rendered = str(_confirm_dialog())
        self.assertIn("confirm_open_rx_state_", rendered)
        self.assertIn("confirm_text_rx_state_", rendered)
        self.assertIn("confirm_action", rendered)
        self.assertIn("set_confirm_open", rendered)
        self.assertIn("Cancelar", rendered)

    def test_pagination(self) -> None:
        pagination = _pagination()
        rendered = str(pagination).replace("?.", ".")
        contents = _contents(pagination)
        self.assertIn("page_total_rx_state_ > 1", rendered)
        for text in ("Anterior", "Próxima", "Página ", " de "):
            with self.subTest(text=text):
                self.assertIn(text, contents)
        self.assertIn('"aria-live":"polite"', rendered)
        self.assertIn("go_to_page", rendered)

    def test_grid_three_columns_on_large_one_on_mobile(self) -> None:
        rendered = str(my_donations_page())
        self.assertIn("repeat(3, minmax(0, 1fr))", rendered)
        self.assertIn('"minmax(0, 1fr)"', rendered)
        self.assertIn("24px 16px 48px", rendered)

    def test_empty_state(self) -> None:
        empty = _empty_state()
        contents = _contents(empty)
        rendered = str(empty)
        self.assertIn(EMPTY_TITLE, contents)
        self.assertIn("Quero Doar", contents)
        self.assertIn('to:"/cadastro-doacao"', rendered)
        self.assertNotIn("go_to_page", rendered)

    def test_states_notice_and_animation(self) -> None:
        page = my_donations_page()
        rendered = str(page)
        self.assertIn("Carregando suas doa\\u00e7\\u00f5es...", rendered)
        self.assertIn("load_error_rx_state_", rendered)
        self.assertIn("notice_rx_state_", rendered)
        self.assertIn('role:"status"', rendered)
        animated = [n for n in _nodes(page) if getattr(n, "class_name", None) == "page-fade-enter"]
        self.assertTrue(animated)
        self.assertTrue(all(type(n).__name__ in {"Box", "Heading"} for n in animated))
        styles = Path("assets/auth-card.css").read_text(encoding="utf-8")
        self.assertIn("@media (prefers-reduced-motion: reduce)", styles)


class HomeHeaderLinkTests(unittest.TestCase):
    def _header_cond(self):
        return next(
            node
            for node in _nodes(index())
            if type(node).__name__ == "Cond"
            and "auth_token" in str(getattr(node, "cond", ""))
            and "Sair" in str(node.children[0])
        )

    def test_link_only_in_authenticated_header(self) -> None:
        authenticated, visitor = (str(child) for child in self._header_cond().children)
        self.assertIn('to:"/minhas-doacoes"', authenticated)
        self.assertIn("Minhas doa\\u00e7\\u00f5es", authenticated)
        self.assertNotIn("/minhas-doacoes", visitor)
        for header in (authenticated, visitor):
            self.assertNotIn("Mensagens", header)

    def test_link_is_spaced_like_the_menu_items(self) -> None:
        authenticated = str(self._header_cond().children[0])
        # 12 px do gap do grupo + 20 px (a partir de 1280 px) = 32 px, o
        # espaçamento do menu nessa largura.
        self.assertIn('gap:"3"', authenticated)
        self.assertIn(
            '["@media screen and (min-width: 80em)"] : ({ ["marginRight"] : "20px" })',
            authenticated,
        )
        self.assertIn('["marginRight"] : "0px"', authenticated)
        # O menu da home: 12 px abaixo de 1280 px e 32 px a partir dele
        # (gap responsivo do Radix; o lg do Radix é 1280 px).
        rendered = str(index())
        self.assertIn('gap:({ ["initial"] : "3", ["lg"] : "6" })', rendered)

    def test_header_never_wraps_between_768_and_1512(self) -> None:
        authenticated = str(self._header_cond().children[0])
        start = authenticated.index('className:"home-greeting"')
        greeting_css = authenticated[start : authenticated.index("})},", start)]
        # “Olá, <nome>” sempre visível (spec user-account), numa linha só e
        # com reticências num nome longo.
        self.assertIn('["whiteSpace"] : "nowrap"', greeting_css)
        self.assertIn('["textOverflow"] : "ellipsis"', greeting_css)
        self.assertIn('["overflow"] : "hidden"', greeting_css)
        self.assertNotIn("overflowWrap", greeting_css)
        self.assertNotIn('"display"', greeting_css)
        self.assertIn('(min-width: 0px)"] : ({ ["maxWidth"] : "100px" })', greeting_css)
        self.assertIn('(min-width: 80em)"] : ({ ["maxWidth"] : "120px" })', greeting_css)

        # Entre 992 e 1279 px, o espaço sai do menu: fonte de 14 px e 12 px
        # entre os itens; a partir de 1280 px, 16 px e 32 px.
        rendered = str(index())
        nav_rule = (
            '["@media screen and (min-width: 0px)"] : ({ ["fontSize"] : "0.875rem" }), '
            '["@media screen and (min-width: 80em)"] : ({ ["fontSize"] : "1rem" })'
        )
        self.assertEqual(rendered.count(nav_rule), 3)
        self.assertIn('gap:({ ["initial"] : "3", ["lg"] : "6" })', rendered)
        # O texto do link “Minhas doações” só aparece a partir de 1280 px.
        self.assertIn(
            '["@media screen and (min-width: 80em)"] : ({ ["display"] : "inline" })',
            authenticated,
        )
        self.assertNotIn(
            '["@media screen and (min-width: 62em)"] : ({ ["display"] : "inline" })',
            authenticated,
        )

    def test_link_keeps_accessible_label_on_mobile(self) -> None:
        authenticated = str(self._header_cond().children[0])
        self.assertIn('"aria-label":"Minhas doa\\u00e7\\u00f5es"', authenticated)
        self.assertIn("LucidePackage", authenticated)
        self.assertIn('"minHeight"] : "44px"', authenticated)


class EditDonationStateTests(unittest.TestCase):
    def _load(self, state, categories=CATEGORIES, donation=None, error=None):
        donation = donation if donation is not None else _parse_my_donation(ITEM_PAYLOAD, 17)
        with (
            patch.dict("os.environ", {"XANO_API_URL": BASE_URL}),
            patch("doafacil.minhas_doacoes._fetch_categories", new_callable=AsyncMock, return_value=categories) as fetch_categories,
            patch("doafacil.minhas_doacoes.fetch_my_donation", new_callable=AsyncMock, return_value=donation, side_effect=error) as fetch,
            patch("doafacil.minhas_doacoes.rx.redirect", return_value="login"),
        ):
            events = _events(EditDonationState.load_edit.fn(state))
        return events, fetch_categories, fetch

    def test_without_token_redirects(self) -> None:
        state = _edit_state(auth_token="")
        events, categories, fetch = self._load(state)
        self.assertEqual(events, ["login"])
        categories.assert_not_called()
        fetch.assert_not_called()

    def test_invalid_id_shows_not_found_without_request(self) -> None:
        for route_id in ("abc", "0", "-1", ""):
            with self.subTest(route_id=route_id):
                state = _edit_state(route_id)
                _, categories, fetch = self._load(state)
                categories.assert_not_called()
                fetch.assert_not_called()
                self.assertEqual(state.view_state, "not_found")

    def test_not_found_and_errors(self) -> None:
        cases = (
            (MyDonationNotFoundError(), "not_found", ""),
            (MyDonationsRateLimitError(), "error", RATE_LIMIT_MESSAGE),
            (MyDonationsServiceError(), "error", EDIT_ERROR_MESSAGE),
        )
        for error, view_state, message in cases:
            with self.subTest(error=type(error).__name__):
                state = _edit_state()
                self._load(state, error=error)
                self.assertEqual(state.view_state, view_state)
                self.assertEqual(state.load_error, message)

    def test_completed_donation_has_no_form(self) -> None:
        state = _edit_state()
        self._load(state, donation={**_parse_my_donation(ITEM_PAYLOAD, 17), "status": "concluída"})
        self.assertEqual(state.view_state, "completed")
        self.assertEqual(state.title, "")

    def test_form_is_filled_with_current_values(self) -> None:
        state = _edit_state()
        _, categories, fetch = self._load(state)
        categories.assert_awaited_once()
        self.assertEqual(fetch.await_args.args[1:], (TOKEN, 17))
        self.assertEqual(state.view_state, "ready")
        self.assertEqual((state.title, state.description), ("Carrinho", "Em bom estado."))
        self.assertEqual((state.category_id, state.category_name), ("3", "Brinquedos"))
        self.assertEqual((state.condition, state.delivery_method, state.contact_preference), ("Bom", "A combinar", "E-mail"))

    def test_values_outside_options_start_empty(self) -> None:
        state = _edit_state()
        donation = {
            **_parse_my_donation(ITEM_PAYLOAD, 17),
            "category_id": 99,
            "delivery_method": "Entrega",
            "contact_preference": "WhatsApp",
        }
        self._load(state, donation=donation)
        self.assertEqual((state.category_id, state.category_name), ("", ""))
        self.assertEqual(state.delivery_method, "")
        self.assertEqual(state.contact_preference, "")

    def test_validation_messages_without_request(self) -> None:
        cases = {
            "título vazio": {"title": "  "},
            "título longo": {"title": "a" * 101},
            "descrição vazia": {"description": " "},
            "descrição longa": {"description": "a" * 2001},
            "categoria vazia": {"category_id": ""},
            "categoria fora": {"category_id": "99"},
            "condição": {"condition": ""},
            "entrega": {"delivery_method": "Entrega"},
            "contato": {"contact_preference": "WhatsApp"},
        }
        for label, change in cases.items():
            with self.subTest(case=label):
                state = _ready_edit_state(**change)
                with patch("doafacil.minhas_doacoes.update_donation", new_callable=AsyncMock) as update:
                    _events(EditDonationState.save.fn(state))
                update.assert_not_called()
                self.assertTrue(state.form_error)
                # Os valores digitados ficam.
                for key, value in change.items():
                    self.assertEqual(getattr(state, key), value)

    def test_validate_edit_accepts_valid_values(self) -> None:
        self.assertEqual(
            _validate_edit("Carrinho", "Bom", "3", "Bom", "A combinar", "Chat do DoaFácil", {3}),
            "",
        )

    def test_save_success_sets_notice_and_returns_to_list(self) -> None:
        state = _ready_edit_state(title="  Carrinho novo  ")
        with (
            patch("doafacil.minhas_doacoes.update_donation", new_callable=AsyncMock) as update,
            patch("doafacil.minhas_doacoes.rx.redirect", return_value="lista"),
            patch.object(MyDonationsState, "set_flash", return_value="flash") as set_flash,
        ):
            events = _events(EditDonationState.save.fn(state))
        fields = update.await_args.args[3]
        self.assertEqual(update.await_args.args[1:3], (TOKEN, 17))
        self.assertEqual(fields["title"], "Carrinho novo")
        self.assertEqual(fields["category_id"], 3)
        set_flash.assert_called_once_with(SAVED_MESSAGE)
        self.assertEqual(events[-2:], ["flash", "lista"])
        self.assertFalse(state.is_saving)

    def test_save_errors_keep_values(self) -> None:
        cases = (
            (MyDonationRejectedError(), SAVE_REJECTED_MESSAGE),
            (MyDonationNotFoundError(), SAVE_NOT_FOUND_MESSAGE),
            (MyDonationsRateLimitError(), RATE_LIMIT_MESSAGE),
            (MyDonationsServiceError(), SAVE_ERROR_MESSAGE),
            (httpx.ConnectError("x"), SAVE_ERROR_MESSAGE),
        )
        for error, message in cases:
            with self.subTest(error=type(error).__name__):
                state = _ready_edit_state(title="Novo título")
                with patch("doafacil.minhas_doacoes.update_donation", new_callable=AsyncMock, side_effect=error):
                    _events(EditDonationState.save.fn(state))
                self.assertEqual(state.form_error, message)
                self.assertEqual(state.title, "Novo título")
                self.assertFalse(state.is_saving)

    def test_save_401_redirects(self) -> None:
        state = _ready_edit_state()
        with (
            patch("doafacil.minhas_doacoes.update_donation", new_callable=AsyncMock, side_effect=MyDonationsUnauthorizedError()),
            patch("doafacil.minhas_doacoes.rx.redirect", return_value="login"),
        ):
            events = _events(EditDonationState.save.fn(state))
        self.assertIn("login", events)
        self.assertEqual(state.auth_token, "")


class EditDonationPageTests(unittest.TestCase):
    def test_form_fields_and_options(self) -> None:
        form = _edit_form()
        rendered = str(form)
        contents = _contents(form)
        for label in ("Nome do item", "Descrição", "Categoria", "Condição do item", "Forma de entrega", "Forma de contato", "Cancelar"):
            with self.subTest(label=label):
                self.assertIn(label, contents)
        for option in ("A combinar", "E-mail", "Chat do DoaF\\u00e1cil", "\\u00d3timo", "Bom", "Regular"):
            with self.subTest(option=option):
                self.assertIn(f'value:"{option}"', rendered)
        self.assertNotIn("WhatsApp", rendered)
        self.assertNotIn('value:"Entrega"', rendered)
        self.assertNotIn('value:"Retirada"', rendered)
        # Sem fotos, cidade ou UF.
        self.assertNotIn("upload", rendered.lower())
        self.assertNotIn("city", rendered)
        self.assertIn("maxLength:100,", rendered)
        self.assertIn("maxLength:2000,", rendered)
        self.assertIn("auth-card-enter", rendered)
        self.assertIn('role:"alert"', rendered)

    def test_selects_look_like_text_fields(self) -> None:
        rendered = str(_edit_form())
        for field_id in (
            "edit-donation-category",
            "edit-donation-condition",
            "edit-donation-delivery-method",
            "edit-donation-contact-preference",
        ):
            with self.subTest(field_id=field_id):
                self.assertIn(f'id:"{field_id}"', rendered)
        # O estilo fica no Trigger (o botão visível), não no Root.
        triggers = rendered.split("RadixThemesSelect.Trigger,")[1:]
        self.assertEqual(len(triggers), 4)
        for trigger in triggers:
            trigger_css = trigger.split("},", 1)[0]
            for expected in (
                '["background"] : "#FFFFFF"',
                '["color"] : "#1F1F1F"',
                '["border"] : "1px solid #C8C8C8"',
                '["height"] : "40px"',
                '["borderRadius"] : "8px"',
                '["&:focus-visible"]',
                "2px solid #007A42",
                "[data-placeholder] .rt-SelectTriggerInner",
            ):
                with self.subTest(expected=expected):
                    self.assertIn(expected, trigger)
        # Os ids do cadastro, que puxam #333333 do app.style, não são usados
        # nos selects da edição.
        self.assertNotIn('id:"donation-category"', rendered)
        self.assertNotIn('id:"donation-condition"', rendered)

    def test_page_header_and_states(self) -> None:
        page = edit_donation_page()
        header = page.children[0]
        self.assertEqual(
            str(header),
            str(back_link_header("/minhas-doacoes", "Voltar a Minhas doações", "#007A42")),
        )
        rendered = str(page)
        self.assertIn("Doa\\u00e7\\u00e3o n\\u00e3o encontrada", rendered)
        self.assertEqual(EDIT_COMPLETED_MESSAGE, "Esta doação foi concluída e não pode mais ser editada.")
        self.assertIn("foi conclu\\u00edda e n\\u00e3o pode mais ser editada.", rendered)
        self.assertNotIn("chat-fab", rendered)
        self.assertEqual(DONATION_NOT_FOUND_MESSAGE, "Doação não encontrada")


if __name__ == "__main__":
    unittest.main()
