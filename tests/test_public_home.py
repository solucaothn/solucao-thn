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


class PublicHomeTests(unittest.TestCase):
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
            "Para você mesmo",
            "Escolha um item disponível e receba de alguém que está desapegando.",
            "Ajude quem precisa",
            "Cadastre um objeto que você não usa mais e encontre quem precisa.",
            "Desapego em grupo",
            "Para família ou uma empresa que quer doar vários itens de uma vez.",
            "Em breve",
        ):
            with self.subTest(text=text):
                self.assertIn(text, contents)

        self.assertEqual(contents.count("→"), 2)
        self.assertNotIn("Buscar doações", contents)
        for node in _component_nodes(section):
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
            "Busca por recibo",
            "Verificação de links",
        ):
            self.assertNotIn(excluded, contents)

        nodes = _component_nodes(footer)
        footer_logo = next(
            node
            for node in nodes
            if getattr(getattr(node, "src", None), "_var_value", None)
            == "/logo.svg"
        )
        self.assertEqual(footer_logo.filter, "brightness(0) invert(1)")
        for node in nodes:
            self.assertFalse(getattr(node, "href", None))
            self.assertFalse(getattr(node, "event_triggers", {}))

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
                self.assertEqual(directions, [expected_breakpoint])

                cards = [
                    node
                    for node in _component_nodes(section)
                    if getattr(node, "min_height", None) is not None
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
            _component_contents(content[1]),
        )
        self.assertEqual(
            getattr(content[2].src, "_var_value", None),
            "/ilustracao-rodape.png",
        )
        self.assertIn("COMECE POR AQUI", _component_contents(content[3]))
        self.assertIn(
            "Doar no DoaFácil é simples e seguro.",
            _component_contents(content[4]),
        )
        self.assertIn(
            "Links rápidos",
            _component_contents(content[5]),
        )

        for node in _component_nodes(page):
            self.assertFalse(getattr(node, "href", None))
            self.assertFalse(getattr(node, "event_triggers", {}))


if __name__ == "__main__":
    unittest.main()
