import asyncio
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx

from doafacil.chat import back_home_header, back_link_header
from doafacil.detalhe_doacao import DONATION_NOT_FOUND_MESSAGE
from doafacil.doafacil import app
from doafacil.perfil_doador import (
    BACK_TO_DONATION_LABEL,
    CARDS_GRID_COLUMNS,
    DONATIONS_TITLE,
    EMPTY_TITLE,
    EXPLORE_LINK_LABEL,
    PROFILE_ERROR_MESSAGE,
    PROFILE_LOADING_MESSAGE,
    PROFILE_PAGE_ERROR_MESSAGE,
    PROFILE_RATE_LIMIT_MESSAGE,
    DonorProfileNotFoundError,
    DonorProfileRateLimitError,
    DonorProfileServiceError,
    DonorProfileState,
    _donor_profile_endpoint,
    _empty_state,
    _identity_card,
    _pagination,
    _parse_donor_profile,
    donor_profile_page,
    fetch_donor_profile,
    items_count_label,
    location_label,
    member_since_label,
)


NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)
RECENT_MS = int(datetime(2026, 11, 10, tzinfo=timezone.utc).timestamp() * 1000)
OLD_MS = int(datetime(2026, 1, 10, tzinfo=timezone.utc).timestamp() * 1000)
BASE_URL = "https://xano.example/api:catalog"

PROFILE_PAYLOAD = {
    "donor": {
        "first_name": "Ana",
        "city": "Campinas",
        "state": "SP",
        "member_since": "2020-10",
    },
    "items": [
        {
            "id": 17,
            "created_at": RECENT_MS,
            "title": "Carrinho de brinquedo",
            "photo": "https://images.example/a.jpg",
            "condition": "Bom",
        },
        {
            "id": 9,
            "created_at": OLD_MS,
            "title": "Livro",
            "photo": None,
            "condition": "Ótimo",
        },
    ],
    "page": 1,
    "per_page": 12,
    "total": 2,
    "page_total": 1,
}


def _profile(**changes: object) -> dict:
    return {**PROFILE_PAYLOAD, **changes}


def _client_for(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _fetch(handler, donation_id: int = 17, page: int = 1) -> dict:
    async def run() -> dict:
        async with _client_for(handler) as client:
            return await fetch_donor_profile(client, BASE_URL, donation_id, page)

    return asyncio.run(run())


def _parsed(**changes: object) -> dict:
    return _parse_donor_profile(_profile(**changes), NOW)


def _state(route_id: str = "17", **fields: object) -> SimpleNamespace:
    base = dict(
        router=SimpleNamespace(page=SimpleNamespace(params={"id": route_id})),
        view_state="loading",
        error_message="",
        donation_id=0,
        back_href="/",
        first_name="",
        initial="",
        location="",
        member_since_label="",
        items=[],
        total=0,
        count_label="",
        page=1,
        page_total=0,
        page_loading=False,
        page_error="",
    )
    base.update(fields)
    return SimpleNamespace(**base)


def _ready_state(**fields: object) -> SimpleNamespace:
    ready = dict(
        view_state="ready",
        donation_id=17,
        back_href="/doacao/17",
        first_name="Ana",
        items=[{"id": 1}],
        total=30,
        count_label="30 itens",
        page=1,
        page_total=3,
    )
    ready.update(fields)
    return _state(**ready)


def _run_go_to_page(state: SimpleNamespace, page: object) -> None:
    async def run() -> None:
        async for _ in DonorProfileState.go_to_page.fn(state, page):
            pass

    asyncio.run(run())


def _component_contents(component: object) -> list[str]:
    contents: list[str] = []

    def collect(value: object) -> None:
        if hasattr(value, "contents"):
            text = value.contents
            if isinstance(text, str):
                contents.append(text)
            elif type(text).__name__ == "LiteralStringVar":
                contents.append(text._var_value)
        if hasattr(value, "children"):
            collect(value.children)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return contents


def _all_nodes(component: object) -> list[object]:
    nodes: list[object] = []

    def collect(value: object) -> None:
        if hasattr(value, "tag") or hasattr(value, "component_name"):
            nodes.append(value)
        if hasattr(value, "children"):
            collect(value.children)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return nodes


class DonorProfileClientTests(unittest.TestCase):
    def test_endpoint_uses_xano_base_donation_id_and_page(self) -> None:
        self.assertEqual(
            _donor_profile_endpoint(f"{BASE_URL}/", 17, 2),
            f"{BASE_URL}/catalog/donations/donor?donation_id=17&page=2",
        )
        with self.assertRaises(ValueError):
            _donor_profile_endpoint("xano.example", 17, 1)

    def test_fetch_sends_donation_id_and_page_without_auth(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api:catalog/catalog/donations/donor")
            self.assertEqual(request.url.params.get("donation_id"), "17")
            self.assertEqual(request.url.params.get("page"), "2")
            self.assertNotIn("Authorization", request.headers)
            return httpx.Response(200, json=_profile(page=2, total=13, page_total=2))

        profile = _fetch(handler, page=2)
        self.assertEqual(profile["page"], 2)
        self.assertEqual(profile["total"], 13)
        self.assertEqual(profile["page_total"], 2)

    def test_200_returns_identity_and_home_cards(self) -> None:
        profile = _parsed()
        self.assertEqual(profile["first_name"], "Ana")
        self.assertEqual(profile["city"], "Campinas")
        self.assertEqual(profile["state"], "SP")
        self.assertEqual(profile["member_since"], "2020-10")
        # Itens no formato do cartão da home: foto genérica, “Condição: …” e NOVO.
        first, second = profile["items"]
        self.assertEqual(first["condition_label"], "Condição: Bom")
        self.assertTrue(first["is_new"])
        self.assertFalse(second["is_new"])
        self.assertEqual(second["photo"], "/doacao-generica.svg")

    def test_404_raises_not_found(self) -> None:
        with self.assertRaises(DonorProfileNotFoundError):
            _fetch(lambda request: httpx.Response(404, json={"message": "Doação não encontrada."}))

    def test_429_raises_rate_limit(self) -> None:
        with self.assertRaises(DonorProfileRateLimitError):
            _fetch(lambda request: httpx.Response(429, json={"message": "Too many"}))

    def test_other_status_raises_service_error(self) -> None:
        with self.assertRaises(DonorProfileServiceError):
            _fetch(lambda request: httpx.Response(500, json={}))

    def test_invalid_responses_raise_value_error(self) -> None:
        invalid_payloads = {
            "não JSON": None,
            "lista": [],
            "sem donor": {key: value for key, value in PROFILE_PAYLOAD.items() if key != "donor"},
            "nome vazio": _profile(donor={**PROFILE_PAYLOAD["donor"], "first_name": "  "}),
            "cidade numérica": _profile(donor={**PROFILE_PAYLOAD["donor"], "city": 1}),
            "membro desde com dia": _profile(donor={**PROFILE_PAYLOAD["donor"], "member_since": "2020-10-05"}),
            "mês 13": _profile(donor={**PROFILE_PAYLOAD["donor"], "member_since": "2020-13"}),
            "página 0": _profile(page=0),
            "total texto": _profile(total="2"),
            "total booleano": _profile(total=True),
            "page_total negativo": _profile(page_total=-1),
            "items não lista": _profile(items={}),
            "itens todos inválidos": _profile(items=[{"id": "x"}]),
        }
        for label, payload in invalid_payloads.items():
            with self.subTest(case=label):
                if payload is None:
                    handler = lambda request: httpx.Response(200, text="<html>")
                else:
                    handler = lambda request, body=payload: httpx.Response(200, json=body)
                with self.assertRaises(ValueError):
                    _fetch(handler)

    def test_extra_fields_are_ignored(self) -> None:
        payload = _profile(
            email="private@example.com",
            owner_id=9,
            donor={
                **PROFILE_PAYLOAD["donor"],
                "email": "private@example.com",
                "last_name": "Silva",
                "user_id": 9,
            },
            items=[{**PROFILE_PAYLOAD["items"][0], "owner_id": 9, "email": "x@y.z"}],
        )
        profile = _parse_donor_profile(payload, NOW)
        self.assertEqual(
            set(profile),
            {"first_name", "city", "state", "member_since", "about", "photo", "items", "page", "total", "page_total"},
        )
        self.assertEqual(
            set(profile["items"][0]), {"id", "title", "photo", "condition_label", "is_new"}
        )
        self.assertNotIn("private@example.com", repr(profile))
        self.assertNotIn("Silva", repr(profile))


class DonorProfileLabelTests(unittest.TestCase):
    def test_member_since_label_in_portuguese(self) -> None:
        self.assertEqual(member_since_label("2020-10"), "outubro de 2020")
        self.assertEqual(member_since_label("2026-03"), "março de 2026")
        self.assertEqual(member_since_label("2019-01"), "janeiro de 2019")
        with self.assertRaises(ValueError):
            member_since_label("2020-1")

    def test_items_count_label(self) -> None:
        self.assertEqual(items_count_label(1), "1 item")
        self.assertEqual(items_count_label(0), "0 itens")
        self.assertEqual(items_count_label(4), "4 itens")

    def test_location_label(self) -> None:
        self.assertEqual(location_label("Campinas", "SP"), "Campinas, SP")
        self.assertEqual(location_label("Campinas", ""), "Campinas")


class DonorProfileStateTests(unittest.TestCase):
    def test_invalid_route_id_shows_not_found_without_request(self) -> None:
        for route_id in ("abc", "0", "-3", "", "1.5"):
            with self.subTest(route_id=route_id):
                state = _state(route_id)
                with (
                    patch("doafacil.perfil_doador.httpx.AsyncClient") as async_client,
                    patch("doafacil.perfil_doador.fetch_donor_profile", new_callable=AsyncMock) as fetch,
                ):
                    asyncio.run(DonorProfileState.load_profile.fn(state))
                async_client.assert_not_called()
                fetch.assert_not_called()
                self.assertEqual(state.view_state, "not_found")
                # Sem doação válida, o voltar leva ao início.
                self.assertEqual(state.back_href, "/")

    def test_load_profile_fills_identity_list_and_labels(self) -> None:
        state = _state("17")
        with (
            patch.dict("os.environ", {"XANO_API_URL": BASE_URL}),
            patch(
                "doafacil.perfil_doador.fetch_donor_profile",
                new_callable=AsyncMock,
                return_value=_parsed(),
            ) as fetch,
        ):
            asyncio.run(DonorProfileState.load_profile.fn(state))

        self.assertEqual(fetch.await_args.args[1:], (BASE_URL, 17, 1))
        self.assertEqual(state.view_state, "ready")
        self.assertEqual(state.donation_id, 17)
        self.assertEqual(state.back_href, "/doacao/17")
        self.assertEqual(state.first_name, "Ana")
        self.assertEqual(state.initial, "A")
        self.assertEqual(state.location, "Campinas, SP")
        self.assertEqual(state.member_since_label, "outubro de 2020")
        self.assertEqual(state.count_label, "2 itens")
        self.assertEqual([item["id"] for item in state.items], [17, 9])
        self.assertEqual((state.page, state.page_total, state.total), (1, 1, 2))

    def test_load_profile_with_one_item_uses_singular(self) -> None:
        state = _state("17")
        parsed = _parsed(items=PROFILE_PAYLOAD["items"][:1], total=1)
        with patch("doafacil.perfil_doador.fetch_donor_profile", new_callable=AsyncMock, return_value=parsed):
            asyncio.run(DonorProfileState.load_profile.fn(state))
        self.assertEqual(state.count_label, "1 item")

    def test_load_profile_not_found(self) -> None:
        state = _state("17")
        with patch(
            "doafacil.perfil_doador.fetch_donor_profile",
            new_callable=AsyncMock,
            side_effect=DonorProfileNotFoundError(),
        ):
            asyncio.run(DonorProfileState.load_profile.fn(state))
        self.assertEqual(state.view_state, "not_found")
        self.assertEqual(state.first_name, "")
        # O voltar continua levando à doação de origem.
        self.assertEqual(state.back_href, "/doacao/17")

    def test_load_profile_errors_show_simple_message_without_data(self) -> None:
        cases = (
            (DonorProfileRateLimitError(), PROFILE_RATE_LIMIT_MESSAGE),
            (DonorProfileServiceError(), PROFILE_ERROR_MESSAGE),
            (httpx.ConnectError("falhou"), PROFILE_ERROR_MESSAGE),
            (ValueError("inválido"), PROFILE_ERROR_MESSAGE),
        )
        for error, message in cases:
            with self.subTest(error=type(error).__name__):
                state = _state("17", first_name="Outra pessoa", items=[{"id": 99}])
                with patch(
                    "doafacil.perfil_doador.fetch_donor_profile",
                    new_callable=AsyncMock,
                    side_effect=error,
                ):
                    asyncio.run(DonorProfileState.load_profile.fn(state))
                self.assertEqual(state.view_state, "error")
                self.assertEqual(state.error_message, message)
                # Nada de dados parciais de outra pessoa.
                self.assertEqual(state.first_name, "")
                self.assertEqual(state.items, [])

    def test_load_profile_without_xano_url_shows_error(self) -> None:
        state = _state("17")
        with patch.dict("os.environ", {"XANO_API_URL": ""}):
            asyncio.run(DonorProfileState.load_profile.fn(state))
        self.assertEqual(state.view_state, "error")

    def test_go_to_page_requests_only_the_requested_page(self) -> None:
        state = _ready_state()
        parsed = _parsed(page=2, total=30, page_total=3)
        with (
            patch.dict("os.environ", {"XANO_API_URL": BASE_URL}),
            patch(
                "doafacil.perfil_doador.fetch_donor_profile",
                new_callable=AsyncMock,
                return_value=parsed,
            ) as fetch,
        ):
            _run_go_to_page(state, 2)
        fetch.assert_awaited_once()
        self.assertEqual(fetch.await_args.args[1:], (BASE_URL, 17, 2))
        self.assertEqual(state.page, 2)
        self.assertEqual([item["id"] for item in state.items], [17, 9])
        self.assertEqual(state.count_label, "30 itens")
        self.assertFalse(state.page_loading)
        self.assertEqual(state.page_error, "")

    def test_go_to_page_ignores_out_of_range_current_and_loading(self) -> None:
        cases = {
            "página 0": (_ready_state(), 0),
            "além da última": (_ready_state(), 4),
            "página atual": (_ready_state(), 1),
            "carregando": (_ready_state(page_loading=True), 2),
            "não pronto": (_ready_state(view_state="loading"), 2),
            "texto": (_ready_state(), "abc"),
        }
        for label, (state, page) in cases.items():
            with self.subTest(case=label):
                with patch(
                    "doafacil.perfil_doador.fetch_donor_profile", new_callable=AsyncMock
                ) as fetch:
                    _run_go_to_page(state, page)
                fetch.assert_not_called()
                self.assertEqual(state.page, 1)

    def test_go_to_page_error_keeps_previous_page_and_shows_message(self) -> None:
        cases = (
            (DonorProfileServiceError(), PROFILE_PAGE_ERROR_MESSAGE),
            (httpx.ReadTimeout("lento"), PROFILE_PAGE_ERROR_MESSAGE),
            (ValueError("inválido"), PROFILE_PAGE_ERROR_MESSAGE),
            (DonorProfileRateLimitError(), PROFILE_RATE_LIMIT_MESSAGE),
        )
        for error, message in cases:
            with self.subTest(error=type(error).__name__):
                state = _ready_state()
                with patch(
                    "doafacil.perfil_doador.fetch_donor_profile",
                    new_callable=AsyncMock,
                    side_effect=error,
                ):
                    _run_go_to_page(state, 2)
                self.assertEqual(state.view_state, "ready")
                self.assertEqual(state.page, 1)
                self.assertEqual(state.items, [{"id": 1}])
                self.assertEqual(state.page_error, message)
                self.assertFalse(state.page_loading)

    def test_go_to_page_not_found_shows_not_found(self) -> None:
        state = _ready_state()
        with patch(
            "doafacil.perfil_doador.fetch_donor_profile",
            new_callable=AsyncMock,
            side_effect=DonorProfileNotFoundError(),
        ):
            _run_go_to_page(state, 2)
        self.assertEqual(state.view_state, "not_found")
        self.assertEqual(state.items, [])
        self.assertFalse(state.page_loading)


class DonorProfilePageTests(unittest.TestCase):
    def test_route_and_on_load_are_registered(self) -> None:
        page = app._unevaluated_pages["doacao/[id]/quem-doa"]
        self.assertEqual(page.route, "doacao/[id]/quem-doa")
        self.assertEqual(page.on_load.fn, DonorProfileState.load_profile.fn)
        # O detalhe continua na sua rota.
        self.assertIn("doacao/[id]", app._unevaluated_pages)

    def test_back_link_header_back_to_donation_in_green(self) -> None:
        header = back_link_header("/doacao/17", BACK_TO_DONATION_LABEL, "#007A42")
        rendered = str(header)
        self.assertEqual(type(header).__name__, "Grid")
        self.assertEqual(header.children[0].custom_attrs.get("aria-label"), "Voltar à doação")
        self.assertIn('to:"/doacao/17"', rendered)
        self.assertIn('"#007A42"', rendered)
        self.assertIn("LucideChevronLeft", rendered)
        self.assertIn("/logo.svg", rendered)
        self.assertIn('"minHeight"] : "44px"', rendered)
        self.assertIn('"minWidth"] : "44px"', rendered)

    def test_back_home_header_is_a_case_of_back_link_header(self) -> None:
        self.assertEqual(
            str(back_home_header()),
            str(back_link_header("/", "Voltar ao início", "#166B3B")),
        )

    def test_page_header_uses_state_back_href_in_every_state(self) -> None:
        page = donor_profile_page()
        header, state_content = page.children
        rendered_header = str(header)
        self.assertEqual(type(header).__name__, "Grid")
        self.assertIn("back_href_rx_state_", rendered_header)
        self.assertIn("Voltar \\u00e0 doa\\u00e7\\u00e3o", rendered_header)
        self.assertIn('"#007A42"', rendered_header)
        self.assertFalse(getattr(header, "class_name", None))

        contents = _component_contents(state_content)
        for expected in (PROFILE_LOADING_MESSAGE, DONATION_NOT_FOUND_MESSAGE, DONATIONS_TITLE, EMPTY_TITLE):
            with self.subTest(text=expected):
                self.assertIn(expected, contents)
        self.assertIn("error_message_rx_state_", str(state_content))

    def test_identity_card_has_initial_name_location_and_member_since(self) -> None:
        card = _identity_card()
        rendered = str(card)
        self.assertEqual(_component_contents(card), ["No DoaFácil desde "])
        for state_var in ("initial", "first_name", "location", "member_since_label"):
            with self.subTest(var=state_var):
                self.assertIn(f"{state_var}_rx_state_", rendered)
        self.assertIn('as:"h1"', rendered)
        for color in ("#F2F2F2", "#555555", "#166B3B", "#2A2A2A", "#D9D9D9"):
            with self.subTest(color=color):
                self.assertIn(color, rendered)
        # Círculo de 72 px no celular e 120 px no computador; no celular, acima do texto.
        self.assertIn('"72px"', rendered)
        self.assertIn('"120px"', rendered)
        self.assertIn('"column"', rendered)
        self.assertIn('"row"', rendered)
        # Sem foto de perfil.
        self.assertNotIn("Image", [type(node).__name__ for node in _all_nodes(card)])

    def test_donations_list_title_count_grid_and_home_cards(self) -> None:
        rendered = str(donor_profile_page())
        self.assertIn("count_label_rx_state_", rendered)
        self.assertIn(CARDS_GRID_COLUMNS, rendered)
        self.assertEqual(CARDS_GRID_COLUMNS, "repeat(auto-fill, minmax(220px, 1fr))")
        # O cartão da home: NOVO, condição, “Acessar” com link para o detalhe.
        self.assertIn("NOVO", rendered)
        self.assertIn('"condition_label"', rendered)
        self.assertIn("Acessar", rendered)
        self.assertIn('"/doacao/"+', rendered)
        # Largura fluida na grade, e não os 280 px do carrossel da home.
        self.assertIn('"width"] : "100%"', rendered)

    def test_pagination_only_with_more_than_one_page(self) -> None:
        pagination = _pagination()
        rendered = str(pagination).replace("?.", ".")
        contents = _component_contents(pagination)
        self.assertIn("page_total_rx_state_ > 1", rendered)
        for text in ("Anterior", "Próxima", "Página ", " de "):
            with self.subTest(text=text):
                self.assertIn(text, contents)
        self.assertIn('"aria-live":"polite"', rendered)
        self.assertIn("go_to_page", rendered)
        self.assertIn("page_loading_rx_state_", rendered)
        self.assertIn("page_error_rx_state_", rendered)
        self.assertIn('role:"alert"', rendered)

    def test_empty_state_has_message_first_name_and_explore_link(self) -> None:
        empty = _empty_state()
        rendered = str(empty)
        contents = _component_contents(empty)
        self.assertIn(EMPTY_TITLE, contents)
        self.assertIn("Quando ", contents)
        self.assertIn(" publicar uma nova doação, ela aparece aqui.", contents)
        self.assertIn(EXPLORE_LINK_LABEL, contents)
        self.assertIn("first_name_rx_state_", rendered)
        self.assertIn('to:"/"', rendered)
        self.assertIn('"#007A42"', rendered)
        # Sem contador nem paginação no estado vazio.
        self.assertNotIn("count_label_rx_state_", rendered)
        self.assertNotIn("go_to_page", rendered)

    def test_out_of_scope_items_are_absent(self) -> None:
        page = donor_profile_page()
        contents = _component_contents(page)
        rendered = str(page)
        for excluded in (
            "E-mail verificado",
            "Chat",
            "Avaliações",
            "Em breve",
            "Online",
            "Sobrenome",
            "e-mail",
            "E-mail",
        ):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, contents)
        for excluded in ("email", "owner_id", "user_id", "last_name", "LucideMessageCircle", "chat-fab"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, rendered)
        # A única imagem fora dos cartões é o logotipo (sem foto de perfil).
        identity_images = [
            node for node in _all_nodes(_identity_card()) if type(node).__name__ == "Image"
        ]
        self.assertEqual(identity_images, [])

    def test_entry_animation_only_on_static_content(self) -> None:
        page = donor_profile_page()
        nodes = _all_nodes(page)
        animated = [node for node in nodes if getattr(node, "class_name", None) == "page-fade-enter"]
        self.assertTrue(animated)
        self.assertTrue(all(type(node).__name__ in {"Box", "Heading"} for node in animated))
        # Os dados do Xano (cartão de identificação e grade) não animam.
        for node in nodes:
            if getattr(node, "class_name", None) in {"donor-profile-identity", "donor-profile-grid"}:
                self.assertNotEqual(node.class_name, "page-fade-enter")
        styles = Path("assets/auth-card.css").read_text(encoding="utf-8")
        self.assertIn("@media (prefers-reduced-motion: reduce)", styles)
        self.assertIn(".page-fade-enter", styles)

    def test_mobile_layout_has_16px_gutter(self) -> None:
        rendered = str(donor_profile_page())
        self.assertIn("24px 16px 48px", rendered)
        self.assertIn('"1396px"', rendered)


class DonorProfileAboutTests(unittest.TestCase):
    """Sobre de quem doa (change editar-perfil)."""

    def test_about_is_read_trimmed_and_null_becomes_empty(self) -> None:
        with_about = _parse_donor_profile(
            _profile(donor={**PROFILE_PAYLOAD["donor"], "about": "  Gosto de doar.\nAté breve.  "}),
            NOW,
        )
        self.assertEqual(with_about["about"], "Gosto de doar.\nAté breve.")
        null_about = _parse_donor_profile(_profile(donor={**PROFILE_PAYLOAD["donor"], "about": None}), NOW)
        self.assertEqual(null_about["about"], "")
        missing = _parse_donor_profile(_profile(), NOW)
        self.assertEqual(missing["about"], "")
        with self.assertRaises(ValueError):
            _parse_donor_profile(_profile(donor={**PROFILE_PAYLOAD["donor"], "about": 5}), NOW)

    def test_load_profile_sets_about(self) -> None:
        state = _state("17", about="")
        parsed = _parse_donor_profile(
            _profile(donor={**PROFILE_PAYLOAD["donor"], "about": "Gosto de doar."}), NOW
        )
        with patch("doafacil.perfil_doador.fetch_donor_profile", new_callable=AsyncMock, return_value=parsed):
            asyncio.run(DonorProfileState.load_profile.fn(state))
        self.assertEqual(state.about, "Gosto de doar.")

    def test_identity_card_shows_about_as_plain_text_only_when_filled(self) -> None:
        rendered = str(_identity_card()).replace("?.", ".")
        self.assertIn("about_rx_state_", rendered)
        self.assertIn('["whiteSpace"] : "pre-wrap"', rendered)
        # Vazio: nada no lugar (o texto fica dentro de um cond com fragmento vazio).
        self.assertIn("about_rx_state_.valueOf", rendered)
        self.assertIn('=== ""', rendered)
        self.assertIn("(jsx(Fragment,{},))", rendered)
        self.assertNotIn("dangerouslySetInnerHTML", rendered)
        self.assertNotIn("Sobre", _component_contents(_identity_card()))


if __name__ == "__main__":
    unittest.main()
