import asyncio
import os
import re
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import httpx

from doafacil.doafacil import (
    COMPLETED_ERROR_MESSAGE,
    COUNT_ERROR_MESSAGE,
    FIELD_PLACEHOLDER_SELECTOR,
    FOOTER_LINK_GROUPS,
    FUTURE_ROUTES,
    INSTITUTIONAL_CARDS,
    HomeState,
    _fetch_donation_counts,
    _fetch_recent_donations,
    _is_new_donation,
    _load_count_result,
    _load_donations_result,
    _parse_donations,
    app,
    donation_count_view,
    index,
    institutional_section,
    public_home_footer,
    recent_donations_view,
    start_here_section,
    _xano_endpoints,
)
from doafacil.chat import ChatState
from doafacil.login import (
    ACCOUNT_FALLBACK_NAME,
    AuthAccountUnavailableError,
    LoginState,
)


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
        elif isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return contents


def _component_nodes(component: object) -> list[object]:
    nodes: list[object] = []

    def collect(value: object) -> None:
        if hasattr(value, "event_triggers"):
            nodes.append(value)
        if hasattr(value, "children"):
            collect(value.children)
        elif isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return nodes


def _all_component_nodes(component: object) -> list[object]:
    nodes: list[object] = []

    def collect(value: object) -> None:
        if hasattr(value, "tag") or hasattr(value, "component_name"):
            nodes.append(value)
        if hasattr(value, "children"):
            collect(value.children)
        elif isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return nodes


def _link_target(node: object) -> str:
    """Destino de um rx.link: o `to` do ReactRouterLink, ou o `href`."""
    match = re.search(r'(?:to|href):"([^"]*)"', str(node))
    return match.group(1) if match else ""


class PublicHomeTests(unittest.TestCase):
    @staticmethod
    def _value(value: object) -> object:
        return getattr(value, "_var_value", value)

    def test_endpoint_urls_use_xano_api_url_environment_variable(self) -> None:
        with patch.dict(
            os.environ,
            {"XANO_API_URL": "https://xano.example/api:catalog/"},
        ):
            self.assertEqual(
                _xano_endpoints(),
                (
                    "https://xano.example/api:catalog/catalog/donations/recent",
                    "https://xano.example/api:catalog/catalog/donations/count",
                ),
            )

    def test_new_badge_includes_exact_seven_day_boundary(self) -> None:
        now = datetime(2026, 1, 8, tzinfo=timezone.utc)
        exactly_seven_days_ago = (now - timedelta(days=7)).isoformat()
        older_than_seven_days = (now - timedelta(days=7, seconds=1)).isoformat()
        future_date = (now + timedelta(seconds=1)).isoformat()

        self.assertTrue(_is_new_donation(exactly_seven_days_ago, now))
        self.assertFalse(_is_new_donation(older_than_seven_days, now))
        self.assertFalse(_is_new_donation(future_date, now))

    def test_optional_card_data_uses_required_fallbacks(self) -> None:
        now = datetime(2026, 1, 8, tzinfo=timezone.utc)
        donations = _parse_donations(
            [
                {
                    "id": 1,
                    "created_at": now.isoformat(),
                    "title": "Cadeira",
                    "photo": None,
                    "condition": None,
                }
            ],
            now,
        )

        self.assertEqual(donations[0]["photo"], "/doacao-generica.svg")
        self.assertEqual(
            donations[0]["condition_label"], "Condição não informada"
        )
        self.assertTrue(donations[0]["is_new"])

    def test_empty_recent_response_stays_empty(self) -> None:
        self.assertEqual(_parse_donations([]), [])

    def test_recent_response_skips_invalid_items_and_keeps_valid_ones(self) -> None:
        valid_item = {
            "id": 12,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "title": "Cadeira",
            "photo": None,
            "condition": None,
        }
        donations = _parse_donations(
            [
                {"id": 11, "created_at": valid_item["created_at"]},
                valid_item,
                "item inválido",
            ]
        )

        self.assertEqual(len(donations), 1)
        self.assertEqual(donations[0]["id"], 12)
        self.assertEqual(donations[0]["title"], "Cadeira")

    def test_recent_response_with_no_valid_items_is_reported_as_failure(self) -> None:
        with self.assertRaisesRegex(ValueError, "nenhum"):
            _parse_donations([{"id": 1, "title": ""}])

    def test_recent_endpoint_payload_maps_card_fields(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("/catalog/donations/recent"))
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 2,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "title": "Mesa",
                        "photo": "https://images.example/mesa.jpg",
                        "condition": "Bom",
                    }
                ],
            )

        async def fetch() -> list[dict[str, str | int | bool]]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_recent_donations(
                    client,
                    "https://xano.example/api:catalog/catalog/donations/recent",
                )

        donations = asyncio.run(fetch())
        self.assertEqual(donations[0]["title"], "Mesa")
        self.assertEqual(donations[0]["photo"], "https://images.example/mesa.jpg")
        self.assertEqual(donations[0]["condition_label"], "Condição: Bom")

    def test_recent_endpoint_accepts_xano_epoch_milliseconds(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("/catalog/donations/recent"))
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 4,
                        "created_at": 1790134916685,
                        "title": "aaaaa",
                        "photo": None,
                        "condition": None,
                    },
                    {
                        "id": 3,
                        "created_at": 1790040131218,
                        "title": "iphone 6",
                        "photo": None,
                        "condition": None,
                    },
                ],
            )

        async def fetch() -> list[dict[str, str | int | bool]]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_recent_donations(
                    client,
                    "https://xano.example/api:catalog/catalog/donations/recent",
                )

        donations = asyncio.run(fetch())

        self.assertEqual([donation["id"] for donation in donations], [4, 3])
        self.assertEqual([donation["title"] for donation in donations], ["aaaaa", "iphone 6"])
        self.assertTrue(
            all(
                donation["photo"] == "/doacao-generica.svg"
                and donation["condition_label"] == "Condição não informada"
                for donation in donations
            )
        )

    @staticmethod
    def _fetch_counts(payload: object) -> tuple[int, int | None]:
        async def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=payload)

        async def fetch() -> tuple[int, int | None]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_donation_counts(
                    client,
                    "https://xano.example/api:catalog/catalog/donations/count",
                )

        return asyncio.run(fetch())

    def test_count_endpoint_returns_available_and_completed(self) -> None:
        self.assertEqual(self._fetch_counts({"count": 3, "completed": 2}), (3, 2))
        self.assertEqual(self._fetch_counts({"count": 0, "completed": 0}), (0, 0))

    def test_invalid_completed_only_invalidates_that_statistic(self) -> None:
        for completed in (None, "2", -1, True, 1.5):
            with self.subTest(completed=completed):
                payload = {"count": 3}
                if completed is not None:
                    payload["completed"] = completed
                self.assertEqual(self._fetch_counts(payload), (3, None))

    def test_invalid_count_is_reported(self) -> None:
        for payload in ({"count": "3", "completed": 1}, {"completed": 1}, [], {"count": -1}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    self._fetch_counts(payload)

    def _load_home(self, count_payload: object, count_status: int = 200) -> object:
        class State:
            donation_count = 0
            completed_count = 0
            count_loading = True
            count_error = ""
            completed_error = ""
            donations: list = []
            donations_loading = True
            donations_error = ""
            categories: list = []

        async def respond(request: httpx.Request) -> httpx.Response:
            path = request.url.path
            if path.endswith("/count"):
                return httpx.Response(count_status, json=count_payload)
            if path.endswith("/categories"):
                return httpx.Response(200, json=[{"id": 4, "name": "Livros"}])
            return httpx.Response(200, json=[])

        real_client = httpx.AsyncClient
        state = State()
        with (
            patch.dict(os.environ, {"XANO_API_URL": "https://xano.example/api:catalog"}),
            patch(
                "doafacil.doafacil.httpx.AsyncClient",
                side_effect=lambda *a, **k: real_client(transport=httpx.MockTransport(respond)),
            ),
            patch(
                "doafacil.explorar.httpx.AsyncClient",
                side_effect=lambda *a, **k: real_client(transport=httpx.MockTransport(respond)),
            ),
        ):
            asyncio.run(HomeState.load_home_data.fn(state))
        return state

    def test_home_shows_both_statistics_from_the_backend(self) -> None:
        state = self._load_home({"count": 8, "completed": 5})
        self.assertEqual((state.donation_count, state.completed_count), (8, 5))
        self.assertEqual((state.count_error, state.completed_error), ("", ""))
        self.assertEqual(state.categories, [{"id": "4", "name": "Livros"}])

    def test_completed_error_keeps_the_available_count(self) -> None:
        state = self._load_home({"count": 8})
        self.assertEqual(state.donation_count, 8)
        self.assertEqual(state.count_error, "")
        self.assertEqual(state.completed_error, COMPLETED_ERROR_MESSAGE)

    def test_count_failure_shows_both_errors_without_fake_numbers(self) -> None:
        state = self._load_home({}, count_status=503)
        self.assertEqual(state.count_error, COUNT_ERROR_MESSAGE)
        self.assertEqual(state.completed_error, COMPLETED_ERROR_MESSAGE)
        self.assertEqual((state.donation_count, state.completed_count), (0, 0))

    def test_endpoint_failures_are_independent(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/count"):
                return httpx.Response(503)
            return httpx.Response(200, json=[])

        async def fetch() -> tuple[int | Exception, object]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await asyncio.gather(
                    _load_count_result(client, "https://xano.example/count"),
                    _load_donations_result(
                        client, "https://xano.example/recent"
                    ),
                )

        count_result, donations_result = asyncio.run(fetch())

        self.assertIsInstance(count_result, httpx.HTTPStatusError)
        self.assertEqual(donations_result, [])

    def test_home_loads_account_independently_from_public_data(self) -> None:
        on_load = app._unevaluated_pages["index"].on_load
        self.assertEqual(
            [handler.fn for handler in on_load],
            [
                HomeState.load_home_data.fn,
                LoginState.load_account.fn,
                ChatState.load_unread_total.fn,
            ],
        )

        class AccountState:
            auth_token = "temporary-token"
            account_name = ""

        account_state = AccountState()
        with (
            patch(
                "doafacil.login.auth_me_endpoint",
                return_value="https://auth.example/auth/me",
            ),
            patch(
                "doafacil.login.request_authenticated_name",
                new_callable=AsyncMock,
                side_effect=AuthAccountUnavailableError(),
            ),
        ):
            asyncio.run(LoginState.load_account.fn(account_state))

        self.assertEqual(account_state.account_name, ACCOUNT_FALLBACK_NAME)
        page_text = _component_contents(index())
        self.assertIn("Doações em circulação!", page_text)
        self.assertIn("Pessoas alcançadas", page_text)
        self.assertIn("Doações mais recentes:", page_text)

    def test_start_here_section_content_and_controls(self) -> None:
        section = start_here_section()
        contents = _component_contents(section)

        for text in (
            "COMECE POR AQUI",
            "Quer criar uma doação?",
            "Leva só alguns minutos: conte o que você quer doar e a gente conecta você a quem precisa.",
            "Para você mesmo",
            "Escolha um item disponível e receba de alguém que está desapegando.",
            "Ajude quem precisa",
            "Cadastre um objeto que você não usa mais e encontre quem precisa.",
            "Desapego em grupo",
            "Para família ou uma empresa que quer doar vários itens de uma vez.",
            "Em breve",
            "Buscar doações",
            "Categoria",
            "Todas as categorias",
            "Localização",
            "Todas as localizações",
            "Buscar",
        ):
            with self.subTest(text=text):
                self.assertIn(text, contents)

        self.assertEqual(contents.count("→"), 2)
        nodes = _component_nodes(section)
        placeholders = [
            getattr(node, "placeholder", None)
            for node in nodes
        ]
        self.assertTrue(
            any(
                getattr(value, "_var_value", value)
                == "O que você está procurando?"
                for value in placeholders
            )
        )
        form_nodes = _all_component_nodes(section)
        search_input = next(
            node
            for node in form_nodes
            if getattr(
                getattr(node, "placeholder", None), "_var_value", None
            )
            == "O que você está procurando?"
        )
        self.assertEqual(search_input.background, "white")
        self.assertEqual(search_input.id, "public-home-search")
        self.assertEqual(search_input.color, "#333333")
        self.assertEqual(search_input.border, "1px solid #C8C8C8")
        self.assertEqual(
            search_input._placeholder,
            {"color": "#6b6b6b", "opacity": 1},
        )
        # O placeholder da busca vem da regra global dos campos.
        self.assertNotIn("#public-home-search::placeholder", app.style)
        self.assertEqual(
            app.style[FIELD_PLACEHOLDER_SELECTOR]["color"],
            "#6B6B6B !important",
        )
        search_selects = [
            node
            for node in form_nodes
            if type(node).__name__ == "SelectRoot"
        ]
        self.assertEqual(len(search_selects), 2)
        self.assertTrue(
            all(
                select.children[0].background == "white"
                and select.children[0].color == "#6B6B6B"
                and select.children[0].border == "1px solid #C8C8C8"
                for select in search_selects
            )
        )
        self.assertEqual(
            [self._value(select.name) for select in search_selects],
            ["categoria", "uf"],
        )
        self.assertEqual(self._value(search_input.name), "q")
        rendered = str(section)
        # Categorias do backend, não mais a lista fixa antiga.
        self.assertIn("home_state.categories", rendered)
        for old in ("Roupas", "Eletr\\u00f4nicos", "Brinquedos"):
            self.assertNotIn(old, rendered)
        for uf in ('"SP"', '"RJ"', '"TO"'):
            self.assertIn(uf, rendered)

        # Só os dois primeiros cartões navegam; a busca é um formulário.
        links = {
            _component_contents(node)[0]: _link_target(node)
            for node in form_nodes
            if type(node).__name__ == "Link"
        }
        self.assertEqual(links, {"Para você mesmo": "/explorar", "Ajude quem precisa": "/cadastro-doacao"})
        form = next(node for node in form_nodes if type(node).__name__ == "Form")
        self.assertIn("on_submit", form.event_triggers)
        self.assertIn("search", str(form.event_triggers["on_submit"]))
        submit = next(node for node in form_nodes if type(node).__name__ == "Button")
        self.assertEqual(self._value(submit.type), "submit")
        group_card = next(
            node
            for node in nodes
            if "Em breve" in _component_contents(node)
            and getattr(node, "padding", None) == "2rem"
        )
        self.assertFalse(getattr(group_card, "href", None))

    def test_search_builds_explore_url_with_chosen_filters(self) -> None:
        cases = (
            ({}, "/explorar"),
            ({"q": "   ", "categoria": "todas", "uf": "todas"}, "/explorar"),
            ({"q": "  cadeira azul "}, "/explorar?q=cadeira+azul"),
            ({"uf": "sp"}, "/explorar?uf=SP"),
            ({"q": "mesa", "categoria": "4", "uf": "RJ"}, "/explorar?q=mesa&categoria=4&uf=RJ"),
            ({"categoria": "abc", "uf": "XX"}, "/explorar"),
        )
        for form_data, expected in cases:
            with self.subTest(form_data=form_data):
                with patch("doafacil.doafacil.rx.redirect", side_effect=lambda url: url):
                    self.assertEqual(HomeState.search.fn(None, form_data), expected)

    def test_institutional_section_content_and_controls(self) -> None:
        section = institutional_section()
        contents = _component_contents(section)

        for text in (
            "Doar no DoaFácil é simples e seguro.",
            "Doações já circularam por aqui, conectando quem tem com quem precisa. "
            "Transparência em cada etapa, do anúncio à entrega.",
            "Solidariedade",
            "Histórias que continuam",
            "Segurança",
            "Você no controle",
            "Nossa missão",
            "Nada se perde",
            "Passo a passo",
            "Doar leva minutos",
        ):
            with self.subTest(text=text):
                self.assertIn(text, contents)

        self.assertNotIn("Saiba mais", contents)
        nodes = _component_nodes(section)
        # Placeholder em degradê: nenhuma foto (as do Figma têm marca d'água).
        self.assertTrue(all(card["image"] is None for card in INSTITUTIONAL_CARDS))
        cards = [
            node
            for node in nodes
            if getattr(node, "class_name", None) == "home-institutional-card"
        ]
        self.assertEqual(len(cards), 4)
        for card in cards:
            self.assertTrue(str(card.background).startswith("linear-gradient"))
            self.assertEqual(self._value(card.aspect_ratio), "1")
        rendered = str(section)
        self.assertNotIn("url(", rendered)
        self.assertNotIn("shutterstock", rendered.lower())
        for node in nodes:
            self.assertFalse(getattr(node, "href", None))
            self.assertFalse(getattr(node, "event_triggers", {}))
            self.assertFalse(getattr(node, "src", None))

    def test_footer_content_and_links(self) -> None:
        footer = public_home_footer()
        contents = _component_contents(footer)

        for text in (
            "Fale conosco",
            "Clique aqui para falar conosco",
            "Links rápidos",
            "Quem somos",
            "Doações",
            "Criar doações",
            "Doações mais recentes",
            "Política de privacidade",
            "Termos de uso",
            "Dúvidas frequentes",
            "Segurança e transparência",
            "Projeto acadêmico DoaFácil",
        ):
            with self.subTest(text=text):
                self.assertIn(text, contents)

        for excluded in (
            "Selo de segurança",
            "CNPJ",
            "cidade",
            "horário de atendimento",
            "E-mail",
            "Telefone",
            "Busca por recibo",
            "Verificação de links",
        ):
            self.assertNotIn(excluded, contents)

        nodes = _component_nodes(footer)
        footer_directions = [
            {
                breakpoint: getattr(value, "_var_value", value)
                for breakpoint, value in node.style["flexDirection"].items()
            }
            for node in nodes
            if "flexDirection" in getattr(node, "style", {})
        ]
        self.assertEqual(footer_directions, [{"0px": "column", "62em": "row"}])

        footer_logo = next(
            node
            for node in nodes
            if getattr(getattr(node, "src", None), "_var_value", None)
            == "/logo.svg"
        )
        self.assertFalse(getattr(footer_logo, "filter", None))
        self.assertEqual(footer_logo.width, "160px")
        self.assertEqual(footer_logo.height, "58px")
        text_nodes = {
            contents[0]: node
            for node in _all_component_nodes(footer)
            if type(node).__name__ == "Text"
            and (contents := _component_contents(node))
        }
        self.assertEqual(text_nodes["Fale conosco"].font_size, "15px")
        self.assertEqual(
            text_nodes["Links rápidos"].font_size,
            "15px",
        )
        self.assertEqual(
            text_nodes["Projeto acadêmico DoaFácil"].font_size,
            "12px",
        )
        link_nodes = {
            contents[0]: node
            for node in _all_component_nodes(footer)
            if type(node).__name__ == "Link"
            and (contents := _component_contents(node))
        }
        expected_links = {
            "Clique aqui para falar conosco": "/contato",
            "Quem somos": "/quem-somos",
            "Doações": "/explorar",
            "Criar doações": "/cadastro-doacao",
            "Doações mais recentes": "/#doacoes-recentes",
            "Política de privacidade": "/privacidade",
            "Termos de uso": "/termos",
            "Dúvidas frequentes": "/duvidas",
            "Segurança e transparência": "/seguranca",
        }
        self.assertEqual({label: _link_target(node) for label, node in link_nodes.items()}, expected_links)
        for label, node in link_nodes.items():
            with self.subTest(link=label):
                self.assertEqual(node.font_size, "13px")
                self.assertIn("&:focus-visible", str(node))
        self.assertEqual(
            {href for group in FOOTER_LINK_GROUPS for _, href in group} - {"/explorar", "/cadastro-doacao", "/#doacoes-recentes"},
            {FUTURE_ROUTES[key] for key in ("quem_somos", "privacidade", "termos", "duvidas", "seguranca")},
        )
        link_stacks = [
            node
            for node in _all_component_nodes(footer)
            if getattr(
                getattr(node, "style", {}).get("rowGap"),
                "_var_value",
                getattr(node, "style", {}).get("rowGap"),
            )
            == "6px"
        ]
        self.assertEqual(len(link_stacks), 4)
        for node in nodes:
            self.assertFalse(getattr(node, "event_triggers", {}))

    def test_start_here_spacing_and_card_alignment(self) -> None:
        section = start_here_section()
        container = section.children[0]
        self.assertEqual(container.padding, "2.5rem 24px 5rem")
        self.assertEqual(self._value(container.spacing), "0")

        contents = container.children
        self.assertEqual(contents[0].margin_bottom, "1rem")
        self.assertEqual(contents[1].margin_bottom, "1.5rem")
        self.assertEqual(contents[1].line_height, "1.2")
        self.assertEqual(contents[2].margin_bottom, "3rem")
        self.assertEqual(contents[2].line_height, "1.4")
        self.assertEqual(contents[3].margin_bottom, "3rem")
        self.assertEqual(contents[3].gap, "1.5rem")

        cards = [
            node
            for node in _component_nodes(section)
            if getattr(node, "padding", None) == "2rem"
        ]
        self.assertEqual(len(cards), 3)
        for card in cards:
            self.assertEqual(card.padding, "2rem")
            self.assertEqual(self._value(card.justify), "between")
            self.assertEqual(len(card.children), 2)
            self.assertEqual(self._value(card.children[0].align), "center")
            self.assertEqual(self._value(card.children[0].justify), "start")
        # A coluna responsiva fica no link (cartões que navegam) ou no próprio
        # cartão (“Desapego em grupo”); dentro do link, o cartão ocupa 100%.
        columns = [
            node
            for node in _all_component_nodes(section)
            if isinstance(getattr(node, "style", {}).get("width"), dict)
            and "62em" in node.style["width"]
        ]
        self.assertEqual(len(columns), 3 + 4)  # 3 cartões + 4 campos da busca
        self.assertEqual(
            sorted(self._value(node.style["width"]["62em"]) for node in columns),
            ["calc((100% - 48px) / 3)"] * 3 + ["calc((100% - 48px) / 4)"] * 4,
        )
        linked_cards = [card for card in cards if "Em breve" not in _component_contents(card)]
        self.assertTrue(all(self._value(card.style["width"]) == "100%" for card in linked_cards))

    def test_recent_donations_use_a_single_line_horizontal_carousel(self) -> None:
        recent_view = recent_donations_view()
        carousel = next(
            node
            for node in _all_component_nodes(recent_view)
            if getattr(node, "class_name", None)
            == "recent-donations-carousel"
        )
        self.assertEqual(self._value(carousel.wrap), "nowrap")
        self.assertEqual(self._value(carousel.overflow_x), "auto")
        self.assertEqual(self._value(carousel.gap), "20px")
        self.assertEqual(
            self._value(carousel.style["scrollSnapType"]),
            "x mandatory",
        )

        count_view = donation_count_view()
        self.assertEqual(self._value(count_view.flex_shrink), "0")
        self.assertEqual(
            self._value(count_view.style["minWidth"]["62em"]),
            "11rem",
        )
        self.assertEqual(
            self._value(count_view.style["width"]["62em"]),
            "11rem",
        )
        labels = [
            text
            for text in _component_contents(count_view)
            if text in {"Doações em circulação!", "Pessoas alcançadas"}
        ]
        self.assertEqual(labels, ["Doações em circulação!", "Pessoas alcançadas"])
        for label in labels:
            label_node = next(
                node
                for node in _all_component_nodes(count_view)
                if type(node).__name__ == "Text"
                and label in _component_contents(node)
            )
            self.assertEqual(self._value(label_node.white_space), "normal")
            self.assertEqual(self._value(label_node.color), "#005723")
            self.assertEqual(self._value(label_node.font_size), "1rem")
        rendered = str(count_view)
        self.assertIn("completed_count", rendered)
        self.assertIn("completed_error", rendered)
        self.assertEqual(self._value(recent_view.min_width), "0")

    def test_recent_section_has_anchor_title_and_see_more(self) -> None:
        recent_view = recent_donations_view()
        self.assertEqual(self._value(recent_view.id), "doacoes-recentes")
        self.assertIn("Doações mais recentes:", _component_contents(recent_view))
        see_more = next(
            node
            for node in _all_component_nodes(recent_view)
            if type(node).__name__ == "Link"
            and _component_contents(node) == ["Ver mais..."]
        )
        self.assertEqual(_link_target(see_more), "/explorar")
        # Fora dos rx.cond de carregando/erro/vazio: sempre visível.
        conds = [
            node for node in _all_component_nodes(recent_view) if type(node).__name__ == "Cond"
        ]
        inside_conds = {id(node) for cond in conds for node in _all_component_nodes(cond)}
        self.assertNotIn(id(see_more), inside_conds)

    def test_first_viewport_contains_header_content_and_illustration(self) -> None:
        page = index()
        first_view = page.children[0]
        self.assertEqual(first_view.min_height, "100vh")
        self.assertEqual(self._value(first_view.spacing), "0")
        self.assertEqual(len(first_view.children), 3)

        header, main_content, illustration = first_view.children
        self.assertEqual(header.background, "white")
        self.assertEqual(main_content.flex, "1")
        self.assertEqual(
            getattr(illustration.src, "_var_value", None),
            "/ilustracao-rodape.png",
        )
        self.assertEqual(illustration.width, "100%")
        self.assertEqual(illustration.display, "block")
        self.assertEqual(illustration.margin_top, "0")
        self.assertEqual(illustration.margin_bottom, "0")
        first_view_content = _component_contents(first_view)
        self.assertIn("Doar é fácil.", first_view_content)
        self.assertIn("Doações mais recentes:", first_view_content)
        self.assertNotIn("COMECE POR AQUI", first_view_content)
        self.assertEqual(
            _component_contents(page.children[1])[0],
            "COMECE POR AQUI",
        )

    def test_card_sections_stack_on_narrow_screens(self) -> None:
        for section, expected_breakpoint in (
            (start_here_section(), {"0px": "column", "62em": "row"}),
            (institutional_section(), {"0px": "column", "48em": "row"}),
        ):
            with self.subTest(breakpoint=expected_breakpoint):
                directions = [
                    {
                        breakpoint: getattr(value, "_var_value", value)
                        for breakpoint, value in node.style["flexDirection"].items()
                    }
                    for node in _component_nodes(section)
                    if "flexDirection" in getattr(node, "style", {})
                ]
                self.assertEqual(
                    directions,
                    [expected_breakpoint]
                    * (2 if "62em" in expected_breakpoint else 1),
                )

                # Em tela estreita, cada cartão (ou o link em volta dele)
                # ocupa a largura toda.
                columns = [
                    node
                    for node in _all_component_nodes(section)
                    if isinstance(getattr(node, "style", {}).get("width"), dict)
                    and "0px" in node.style["width"]
                    and type(node).__name__ != "Button"
                ]
                card_columns = (
                    columns[:3] if "62em" in expected_breakpoint else columns
                )
                self.assertEqual(len(card_columns), 3 if "62em" in expected_breakpoint else 4)
                self.assertTrue(
                    all(
                        self._value(node.style["width"]["0px"]) == "100%"
                        for node in columns
                    )
                )

    def test_texts_on_cream_and_cards_meet_aa_contrast(self) -> None:
        def luminance(color: str) -> float:
            channels = [int(color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
            linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        def ratio(a: str, b: str) -> float:
            high, low = sorted((luminance(a), luminance(b)), reverse=True)
            return (high + 0.05) / (low + 0.05)

        cream = "#FFF6E8"
        # Etiqueta, “Ver mais...”, números e texto institucional.
        self.assertIn('"#166B3B"', str(start_here_section()).split("COMECE POR AQUI")[0])
        self.assertIn('className:"home-see-more",css:({ ["color"] : "#166B3B"', str(recent_donations_view()))
        self.assertGreaterEqual(ratio("#166B3B", cream), 4.5)
        # Números e rótulos (#005723) e título (#2A2A2A) do Figma.
        self.assertGreaterEqual(ratio("#005723", cream), 4.5)
        self.assertGreaterEqual(ratio("#2A2A2A", cream), 4.5)
        # Branco sobre o degradê de cada cartão institucional (as duas pontas).
        for card in INSTITUTIONAL_CARDS:
            for color in re.findall(r"#[0-9A-Fa-f]{6}", card["placeholder"]):
                with self.subTest(card=card["title"], color=color):
                    self.assertGreaterEqual(ratio("#FFFFFF", color), 4.5)
        # Links do rodapé sobre o fundo escuro.
        self.assertGreaterEqual(ratio("#F5F5F5", "#252525"), 4.5)

    def test_hero_title_and_statistics_follow_figma(self) -> None:
        page = index()
        first_view = page.children[0]
        title = next(
            node
            for node in _all_component_nodes(first_view)
            if getattr(node, "class_name", None) == "home-hero-title"
        )
        rendered = str(title)
        # Nó 615:2345: LINE Seed JP Bold 36 px, altura normal, #2A2A2A,
        # centralizado, 1376 px de largura; menor proporcionalmente até 24 px.
        self.assertIn('["fontSize"] : "clamp(1.5rem, 2.4vw, 2.25rem)"', rendered)
        self.assertIn('["width"] : "min(1376px, 100%)"', rendered)
        self.assertIn('["lineHeight"] : "normal"', rendered)
        self.assertIn('["color"] : "#2A2A2A"', rendered)
        self.assertIn('["textAlign"] : "center"', rendered)
        self.assertIn("LINE Seed JP", rendered)
        self.assertNotIn("maxWidth", rendered)
        # Sem rolagem horizontal em 360 px: padding lateral e nada fixo largo.
        hero_box = first_view.children[1].children[0]
        self.assertEqual(hero_box.padding_x, "16px")
        # Os números ficam centralizados na altura dos cartões (pedido do
        # grupo, diferente do Figma).
        stats_row = first_view.children[1].children[1]
        self.assertEqual(self._value(stats_row.align), "center")
        # Mesmas bordas do conteúdo do cabeçalho: largura máxima e margens.
        header_row = page.children[0].children[0].children[0]
        self.assertEqual(stats_row.max_width, header_row.max_width)
        self.assertEqual(stats_row.max_width, "1200px")
        # Margens iguais às do cabeçalho: 16 px no celular e 24 px a partir de
        # 62em (o cabeçalho usa "12px 16px" e "12px 24px").
        rendered_row = str(stats_row)
        self.assertIn('["paddingInlineStart"] : "16px", ["paddingInlineEnd"] : "16px"', rendered_row)
        self.assertIn('["paddingInlineStart"] : "24px", ["paddingInlineEnd"] : "24px"', rendered_row)
        rendered_header = str(header_row)
        self.assertIn('["padding"] : "12px 16px"', rendered_header)
        self.assertIn('["padding"] : "12px 24px"', rendered_header)
        # Em 1512 px: 1200 - 2×24 (margens) - 176 (11rem) - 32 (gap) = 944 px
        # para o carrossel, o bastante para 4 cartões de 220 px + 3×20 px.
        self.assertGreaterEqual(1200 - 48 - 176 - 32, 4 * 220 + 3 * 20)

    def test_recent_cards_are_medium_squares(self) -> None:
        from doafacil.cartoes_doacao import RECENT_CARD_SIZE

        size = "clamp(220px, calc((100% - 60px) / 4), 260px)"
        self.assertEqual(RECENT_CARD_SIZE, size)
        card = str(recent_donations_view())
        # Entre 220 e 260 px, dividindo o carrossel em 4; quadrado, com o
        # carrossel rolando quando não couber.
        for prop in ("width", "minWidth", "maxWidth"):
            self.assertIn(f'["{prop}"] : "{size}"', card)
        self.assertIn('["aspectRatio"] : "1 / 1"', card)
        self.assertNotIn('"280px"', card)
        self.assertIn('["overflowX"] : "auto"', card)
        # Textos do cartão continuam legíveis.
        self.assertIn('["fontSize"] : "1.1rem"', card)
        self.assertIn('["fontSize"] : "0.85rem"', card)

    def test_institutional_cards_fit_360_px(self) -> None:
        rendered = str(institutional_section())
        # Quadrados de no máximo 320 px no celular, sem largura fixa maior.
        self.assertIn('(min-width: 0px)"] : ({ ["width"] : "100%", ["maxWidth"] : "320px" })', rendered)
        self.assertIn('["aspectRatio"] : "1"', rendered)
        self.assertNotRegex(rendered, r'\["width"\] : "(3[7-9]\d|[4-9]\d\d)px"')

    def test_home_places_illustration_and_sections_in_requested_order(self) -> None:
        page = index()
        content = page.children

        self.assertIn(
            "Doações mais recentes:",
            _component_contents(content[0]),
        )
        self.assertEqual(
            getattr(content[0].children[2].src, "_var_value", None),
            "/ilustracao-rodape.png",
        )
        self.assertEqual(content[0].min_height, "100vh")
        self.assertEqual(self._value(content[0].spacing), "0")
        self.assertEqual(content[0].children[2].width, "100%")
        self.assertEqual(content[0].children[2].display, "block")
        self.assertEqual(content[0].children[2].margin_top, "0")
        self.assertEqual(content[0].children[2].margin_bottom, "0")
        self.assertIn("COMECE POR AQUI", _component_contents(content[1]))
        self.assertIn(
            "Doar no DoaFácil é simples e seguro.",
            _component_contents(content[2]),
        )
        self.assertIn(
            "Links rápidos",
            _component_contents(content[3]),
        )

        enter_button = next(
            node
            for node in _component_nodes(page)
            if type(node).__name__ == "Button"
            and _component_contents(node) == ["Entrar"]
        )
        self.assertIn("on_click", enter_button.event_triggers)
        # Change landing-nova: o “Sair” é item do menu da conta.
        logout_item = next(
            node
            for node in _component_nodes(page)
            if type(node).__name__ == "DropdownMenuItem"
            and "Sair" in _component_contents(node)
        )
        self.assertIn("on_select", logout_item.event_triggers)
        donate_link = next(
            node
            for node in _component_nodes(page)
            if type(node).__name__ == "Link"
            and _component_contents(node) == ["Quero Doar"]
        )
        self.assertIn('/cadastro-doacao', str(donate_link))
        # A entrada no chat é o botão flutuante, último filho da página.
        messages_link = content[-1]
        self.assertEqual(type(messages_link).__name__, "Link")
        self.assertIn("chat-fab", str(messages_link.class_name))
        self.assertIn('"/chat"', str(messages_link))
        self.assertIn('"/login"', str(messages_link))

        detail_links = [
            node
            for node in _all_component_nodes(page)
            if type(node).__name__ == "Link"
            and "Acessar" in _component_contents(node)
        ]
        self.assertTrue(detail_links)
        self.assertIn("/doacao/", str(page))

        # Links do menu principal (change landing-nova).
        nav_links = {
            _component_contents(node)[0]: _link_target(node)
            for node in _all_component_nodes(page.children[0].children[0])
            if type(node).__name__ == "Link"
            and _component_contents(node)
            and _component_contents(node)[0] in {"Explorar Doações", "Como funciona", "Categorias"}
        }
        self.assertEqual(
            nav_links,
            {
                "Explorar Doações": "/explorar",
                "Como funciona": FUTURE_ROUTES["como_funciona"],
                "Categorias": FUTURE_ROUTES["categorias"],
            },
        )

        # Eventos só no “Entrar”, nos itens do menu da conta e na busca.
        for node in _component_nodes(page):
            if node is not enter_button and type(node).__name__ not in {"DropdownMenuItem", "Form"}:
                self.assertFalse(getattr(node, "event_triggers", {}))

    def test_header_fits_360_px(self) -> None:
        header = str(index().children[0].children[0])
        # Padding de 16 px no celular e 44 px nos controles.
        self.assertIn('(min-width: 0px)"] : ({ ["padding"] : "12px 16px" })', header)
        self.assertIn('className:"home-account-menu"', header)
        self.assertGreaterEqual(header.count('["minHeight"] : "44px"'), 2)
        # O nome some abaixo de 768 px (fica a inicial).
        start = header.index('className:"home-account-name"')
        self.assertIn('["display"] : "none"', header[start : header.index("})},", start)])


if __name__ == "__main__":
    unittest.main()
