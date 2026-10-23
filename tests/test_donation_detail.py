import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from doafacil.detalhe_doacao import (
    DONATION_DETAIL_ERROR_MESSAGE,
    DONATION_NOT_FOUND_MESSAGE,
    GENERIC_DETAIL_IMAGE,
    DonationNotFoundError,
    DonationDetailState,
    _donation_detail_endpoint,
    _fetch_donation_detail,
    _parse_donation_detail,
    donation_detail_page,
)
from doafacil.doafacil import app, recent_donations_view


DETAIL_PAYLOAD = {
    "id": 42,
    "title": "Carrinho de brinquedo",
    "condition": "Bom",
    "description": "Em bom estado.",
    "category": "Brinquedos",
    "city": "Campinas",
    "state": "SP",
    "delivery_method": "A combinar",
    "contact_preference": "E-mail",
    "donor_first_name": "Ana",
    "photos": [
        "https://images.example/capa.jpg",
        "https://images.example/capa.jpg",
        "https://images.example/segunda.jpg",
    ],
    "email": "private@example.com",
    "owner_id": 9,
    "address": "Rua privada, 1",
    "last_name": "Silva",
    "neighborhood": "Centro",
    "zip_code": "00000-000",
}


class DonationDetailTests(unittest.TestCase):
    def test_endpoint_uses_xano_base_and_donation_id(self) -> None:
        self.assertEqual(
            _donation_detail_endpoint(
                "https://xano.example/api:catalog/",
                42,
            ),
            "https://xano.example/api:catalog/catalog/donations/detail"
            "?donation_id=42",
        )

    def test_parser_keeps_only_public_fields_and_deduplicates_photos(self) -> None:
        detail = _parse_donation_detail(DETAIL_PAYLOAD, expected_id=42)

        self.assertEqual(
            detail["photos"],
            [
                "https://images.example/capa.jpg",
                "https://images.example/segunda.jpg",
            ],
        )
        self.assertEqual(
            set(detail),
            {
                "id",
                "title",
                "condition",
                "description",
                "category",
                "city",
                "state",
                "delivery_method",
                "contact_preference",
                "donor_first_name",
                "photos",
            },
        )
        self.assertNotIn("email", detail)
        self.assertNotIn("owner_id", detail)
        self.assertNotIn("address", detail)
        self.assertNotIn("last_name", detail)

    def test_empty_photo_list_uses_generic_donation_image(self) -> None:
        payload = {**DETAIL_PAYLOAD, "photos": []}

        self.assertEqual(
            _parse_donation_detail(payload, expected_id=42)["photos"],
            [GENERIC_DETAIL_IMAGE],
        )

    def test_malformed_detail_response_is_rejected(self) -> None:
        for payload in (
            [],
            {**DETAIL_PAYLOAD, "id": True},
            {**DETAIL_PAYLOAD, "id": 41},
            {**DETAIL_PAYLOAD, "title": ""},
            {**DETAIL_PAYLOAD, "condition": "Excelente"},
            {**DETAIL_PAYLOAD, "photos": ["", 3]},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    _parse_donation_detail(payload, expected_id=42)

    def test_invalid_route_ids_never_call_xano(self) -> None:
        async def check_invalid_id(value: str) -> None:
            called = False

            async def respond(request: httpx.Request) -> httpx.Response:
                nonlocal called
                called = True
                return httpx.Response(200, json=DETAIL_PAYLOAD)

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                with self.assertRaises(DonationNotFoundError):
                    await _fetch_donation_detail(
                        client,
                        "https://xano.example/api:catalog",
                        value,
                    )

            self.assertFalse(called)

        for value in ("abc", "0", "-1"):
            with self.subTest(route_id=value):
                asyncio.run(check_invalid_id(value))

    def test_valid_id_is_sent_as_query_parameter(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api:catalog/catalog/donations/detail")
            self.assertEqual(request.url.params.get("donation_id"), "42")
            return httpx.Response(200, json=DETAIL_PAYLOAD)

        async def fetch() -> dict[str, object]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_donation_detail(
                    client,
                    "https://xano.example/api:catalog",
                    "42",
                )

        self.assertEqual(asyncio.run(fetch())["id"], 42)

    def test_not_found_status_is_mapped_to_not_found_error(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.params.get("donation_id"), "999999")
            return httpx.Response(404, json={"message": "Doação não encontrada."})

        async def fetch() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await _fetch_donation_detail(
                    client,
                    "https://xano.example",
                    "999999",
                )

        with self.assertRaises(DonationNotFoundError):
            asyncio.run(fetch())

    def test_invalid_page_id_shows_not_found_without_creating_http_client(self) -> None:
        for route_id in ("abc", "0", "-1"):
            with self.subTest(route_id=route_id):
                state = _state_for_route_id(route_id)
                with patch(
                    "doafacil.detalhe_doacao.httpx.AsyncClient"
                ) as async_client:
                    asyncio.run(DonationDetailState.load_donation.fn(state))

                async_client.assert_not_called()
                self.assertEqual(state.view_state, "not_found")

    def test_page_state_maps_not_found_and_network_errors(self) -> None:
        async def not_found(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.params.get("donation_id"), "999999")
            return httpx.Response(404)

        async def network_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("offline", request=request)

        async def invalid_response(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"id": 999999})

        for transport_handler, route_id, expected_state in (
            (not_found, "999999", "not_found"),
            (network_error, "42", "error"),
            (invalid_response, "999999", "error"),
        ):
            with self.subTest(expected_state=expected_state):
                state = _state_for_route_id(route_id)
                client = httpx.AsyncClient(
                    transport=httpx.MockTransport(transport_handler)
                )
                with (
                    patch.dict(
                        "os.environ",
                        {"XANO_API_URL": "https://xano.example/api:catalog"},
                    ),
                    patch(
                        "doafacil.detalhe_doacao.httpx.AsyncClient",
                        return_value=client,
                    ),
                ):
                    asyncio.run(DonationDetailState.load_donation.fn(state))

                self.assertEqual(state.view_state, expected_state)

    def test_successful_page_state_stores_only_approved_data(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=DETAIL_PAYLOAD)

        state = _state_for_route_id("42")
        client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        with (
            patch.dict(
                "os.environ",
                {"XANO_API_URL": "https://xano.example/api:catalog"},
            ),
            patch(
                "doafacil.detalhe_doacao.httpx.AsyncClient",
                return_value=client,
            ),
        ):
            asyncio.run(DonationDetailState.load_donation.fn(state))

        self.assertEqual(state.view_state, "loaded")
        self.assertEqual(state.title, "Carrinho de brinquedo")
        self.assertEqual(state.donor_first_name, "Ana")
        self.assertEqual(state.photos, [
            "https://images.example/capa.jpg",
            "https://images.example/segunda.jpg",
        ])
        self.assertFalse(hasattr(state, "email"))

    def test_network_failure_is_not_converted_to_success(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("offline", request=request)

        async def fetch() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await _fetch_donation_detail(
                    client,
                    "https://xano.example",
                    "42",
                )

        with self.assertRaises(httpx.ConnectError):
            asyncio.run(fetch())

    def test_page_registers_dynamic_route_and_load_handler(self) -> None:
        page = app._unevaluated_pages["doacao/[id]"]
        self.assertEqual(page.route, "doacao/[id]")
        self.assertEqual(page.on_load.fn, DonationDetailState.load_donation.fn)

    def test_detail_view_contains_approved_content_and_no_excluded_features(self) -> None:
        page = donation_detail_page()
        contents = _component_contents(page)

        for expected in (
            "Carregando doação...",
            DONATION_NOT_FOUND_MESSAGE,
            DONATION_DETAIL_ERROR_MESSAGE,
            "Detalhes",
            "Descrição",
            "Categoria",
            "Localização",
            "Quem doa",
            "Condição: ",
            "Forma de entrega",
            "Preferência de contato",
        ):
            with self.subTest(text=expected):
                self.assertIn(expected, contents)

        for excluded in (
            "Chat",
            "Outros meios de comunicação",
            "Acessar perfil do doador",
            "Em breve",
            "Online",
            "Conta verificada",
            "Avaliações",
            "Bairro",
            "CEP",
        ):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, contents)

        nodes = _all_component_nodes(page)
        header = next(
            node
            for node in nodes
            if getattr(
                getattr(node, "src", None), "_var_value", getattr(node, "src", None)
            )
            == "/logo.svg"
        )
        self.assertFalse(getattr(header, "class_name", None))
        self.assertTrue(
            any(
                getattr(node, "class_name", None) == "page-fade-enter"
                for node in nodes
            )
        )
        animated_nodes = [
            node
            for node in nodes
            if getattr(node, "class_name", None) == "page-fade-enter"
        ]
        self.assertTrue(
            all(type(node).__name__ in {"Box", "Heading"} for node in animated_nodes)
        )
        animation_styles = Path("assets/auth-card.css").read_text(
            encoding="utf-8"
        )
        self.assertIn("@media (prefers-reduced-motion: reduce)", animation_styles)
        self.assertIn(".page-fade-enter", animation_styles)

    def test_recent_donation_cards_link_to_the_detail_route(self) -> None:
        page = recent_donations_view()
        component = str(page)
        self.assertIn("ReactRouterLink", component)
        self.assertIn('"/doacao/"+', component)
        self.assertIn('["id"]', component)


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


def _state_for_route_id(route_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        router=SimpleNamespace(
            page=SimpleNamespace(params={"id": route_id})
        ),
        donation_id=0,
        title="",
        condition="",
        description="",
        category="",
        city="",
        state="",
        delivery_method="",
        contact_preference="",
        donor_first_name="",
        photos=[],
        view_state="loading",
    )


if __name__ == "__main__":
    unittest.main()
