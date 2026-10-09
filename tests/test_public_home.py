import asyncio
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import httpx

from doafacil.doafacil import (
    _fetch_donation_count,
    _fetch_recent_donations,
    _is_new_donation,
    _load_count_result,
    _load_donations_result,
    _parse_donations,
    app,
    index,
    institutional_section,
    public_home_footer,
    start_here_section,
    _xano_endpoints,
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

    def test_count_endpoint_returns_count(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("/catalog/donations/count"))
            return httpx.Response(200, json={"count": 3})

        async def fetch() -> int:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_donation_count(
                    client,
                    "https://xano.example/api:catalog/catalog/donations/count",
                )

        self.assertEqual(asyncio.run(fetch()), 3)

    def test_invalid_count_is_reported(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("/count"))
            return httpx.Response(200, json={"count": "3"})

        async def fetch() -> int:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_donation_count(client, "https://xano.example/count")

        with self.assertRaises(ValueError):
            asyncio.run(fetch())

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
        self.assertEqual(
            app.style["#public-home-search::placeholder"],
            {"color": "#6b6b6b", "opacity": "1"},
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
        for node in nodes:
            self.assertFalse(getattr(node, "href", None))
            self.assertFalse(getattr(node, "event_triggers", {}))

    def test_institutional_section_content_and_controls(self) -> None:
        section = institutional_section()
        contents = _component_contents(section)

        for text in (
            "Doar no DoaFácil é simples e seguro.",
            "Doações já circularam por aqui, conectando quem tem com quem precisa. "
            "Transparência em cada etapa, do anúncio à entrega.",
            "Solidariedade",
            "Conheça histórias de quem doou e quem recebeu",
            "Segurança",
            "Como funciona a autenticação e proteção dos seus dados",
            "Nossa missão",
            "Descubra por que criamos o DoaFácil",
            "Passo a passo",
            "Veja como criar sua doação em poucos minutos",
        ):
            with self.subTest(text=text):
                self.assertIn(text, contents)

        self.assertEqual(contents.count("Saiba mais"), 4)
        nodes = _component_nodes(section)
        gradient_cards = [
            node
            for node in nodes
            if str(getattr(node, "background", "")).startswith("linear-gradient")
        ]
        self.assertEqual(len(gradient_cards), 4)
        for node in nodes:
            self.assertFalse(getattr(node, "href", None))
            self.assertFalse(getattr(node, "event_triggers", {}))
            self.assertFalse(getattr(node, "src", None))

    def test_footer_content_and_non_navigating_controls(self) -> None:
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
            text_nodes["Clique aqui para falar conosco"].font_size,
            "13px",
        )
        self.assertEqual(
            text_nodes["Projeto acadêmico DoaFácil"].font_size,
            "12px",
        )
        link_labels = (
            "Quem somos",
            "Doações",
            "Criar doações",
            "Doações mais recentes",
            "Política de privacidade",
            "Termos de uso",
            "Dúvidas frequentes",
            "Segurança e transparência",
        )
        for label in link_labels:
            self.assertEqual(text_nodes[label].font_size, "13px")
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
            self.assertFalse(getattr(node, "href", None))
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
            self.assertEqual(
                self._value(card.style["width"]["62em"]),
                "calc((100% - 48px) / 3)",
            )
            self.assertEqual(self._value(card.children[0].align), "center")
            self.assertEqual(self._value(card.children[0].justify), "start")

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
        self.assertIn("Doações mais recentes", first_view_content)
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

                expected_padding = (
                    "2rem" if "62em" in expected_breakpoint else "24px"
                )
                cards = [
                    node
                    for node in _component_nodes(section)
                    if getattr(node, "padding", None) == expected_padding
                ]
                self.assertEqual(
                    len(cards),
                    3 if "62em" in expected_breakpoint else 4,
                )
                self.assertTrue(
                    all(
                        getattr(
                            card.style["width"]["0px"],
                            "_var_value",
                            card.style["width"]["0px"],
                        )
                        == "100%"
                        for card in cards
                    )
                )
    def test_home_places_illustration_and_sections_in_requested_order(self) -> None:
        page = index()
        content = page.children

        self.assertIn(
            "Doações mais recentes",
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

        for node in _component_nodes(page):
            self.assertFalse(getattr(node, "href", None))
            self.assertFalse(getattr(node, "event_triggers", {}))


if __name__ == "__main__":
    unittest.main()
