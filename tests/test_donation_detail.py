import asyncio
import unittest
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from doafacil.login import LoginState
from doafacil.detalhe_doacao import (
    CHAT_NOT_AVAILABLE_FOR_DONATION_MESSAGE,
    CHAT_START_ERROR_MESSAGE,
    DONATION_DETAIL_ERROR_MESSAGE,
    DONATION_NOT_FOUND_MESSAGE,
    DONOR_CHAT_PREFERENCE_MESSAGE,
    DONOR_CONTACT_ERROR_MESSAGE,
    DONOR_OWN_DONATION_MESSAGE,
    GENERIC_DETAIL_IMAGE,
    DonorOwnDonationError,
    DonationNotFoundError,
    DonationDetailState,
    _donor_contact_email_endpoint,
    _donation_detail_endpoint,
    _fetch_donor_email,
    _fetch_donation_detail,
    _mailto_url,
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
    "donor_email_verified": True,
    "donor_counts": {"active": 3, "completed": 1},
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
    def setUp(self) -> None:
        # Cache dos dados públicos (change navegacao-celular): validade zero,
        # para cada chamada destes testes ir ao cliente falso.
        from unittest.mock import patch as _patch

        from doafacil import cache_publico

        cache_publico.clear()
        no_cache = _patch("doafacil.cache_publico.PUBLIC_CACHE_SECONDS", 0.0)
        no_cache.start()
        self.addCleanup(no_cache.stop)

    def test_endpoint_uses_xano_base_and_donation_id(self) -> None:
        self.assertEqual(
            _donation_detail_endpoint(
                "https://xano.example/api:catalog/",
                42,
            ),
            "https://xano.example/api:catalog/catalog/donations/detail"
            "?donation_id=42",
        )

    def test_contact_endpoint_uses_xano_base_and_donation_id(self) -> None:
        self.assertEqual(
            _donor_contact_email_endpoint(
                "https://xano.example/api:catalog/",
                42,
            ),
            "https://xano.example/api:catalog"
            "/catalog/donations/contact-email?donation_id=42",
        )

    def test_mailto_encodes_recipient_and_subject(self) -> None:
        self.assertEqual(
            _mailto_url(
                "donor+tag@example.test",
                "Carrinho & brinquedo",
            ),
            "mailto:donor%2Btag@example.test"
            "?subject=Sobre%20a%20doa%C3%A7%C3%A3o%3A%20"
            "Carrinho%20%26%20brinquedo",
        )

    def test_fetch_donor_email_sends_bearer_token_and_returns_only_email(
        self,
    ) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                request.url.path,
                "/api:catalog/catalog/donations/contact-email",
            )
            self.assertEqual(request.url.params.get("donation_id"), "42")
            self.assertEqual(
                request.headers.get("Authorization"),
                "Bearer private-token",
            )
            return httpx.Response(
                200,
                json={"email": "donor@example.test"},
            )

        async def fetch() -> str:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_donor_email(
                    client,
                    "https://xano.example/api:catalog",
                    42,
                    "private-token",
                )

        self.assertEqual(asyncio.run(fetch()), "donor@example.test")

    def test_fetch_donor_email_maps_403_and_rejects_other_responses(self) -> None:
        async def forbidden(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"message": "Own donation"})

        async def fetch_with(
            handler: Callable[[httpx.Request], httpx.Response],
        ) -> str:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                return await _fetch_donor_email(
                    client,
                    "https://xano.example",
                    42,
                    "private-token",
                )

        with self.assertRaises(DonorOwnDonationError):
            asyncio.run(fetch_with(forbidden))

        for status_code in (401, 404):
            async def respond(
                request: httpx.Request,
                status_code: int = status_code,
            ) -> httpx.Response:
                return httpx.Response(status_code)

            with self.subTest(status_code=status_code):
                with self.assertRaises(httpx.HTTPStatusError):
                    asyncio.run(fetch_with(respond))

        async def extra_fields(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "email": "donor@example.test",
                    "owner_id": 42,
                },
            )

        with self.assertRaises(ValueError):
            asyncio.run(fetch_with(extra_fields))

    def test_contact_flow_redirects_unauthenticated_and_skips_chat_endpoint(
        self,
    ) -> None:
        unauthenticated_state = _contact_state(auth_token="")
        with (
            patch(
                "doafacil.detalhe_doacao.rx.redirect",
                return_value="login-redirect",
            ) as redirect,
            patch("doafacil.detalhe_doacao.httpx.AsyncClient") as async_client,
        ):
            result = asyncio.run(
                DonationDetailState.request_donor_contact.fn(
                    unauthenticated_state
                )
            )

        redirect.assert_called_once_with("/login")
        async_client.assert_not_called()
        self.assertEqual(result, "login-redirect")

        chat_state = _contact_state(
            auth_token="private-token",
            contact_preference="Chat do DoaFácil",
        )
        with patch(
            "doafacil.detalhe_doacao.httpx.AsyncClient"
        ) as async_client:
            asyncio.run(
                DonationDetailState.request_donor_contact.fn(chat_state)
            )

        async_client.assert_not_called()
        self.assertEqual(
            chat_state.contact_message,
            DONOR_CHAT_PREFERENCE_MESSAGE,
        )

    def test_contact_flow_opens_mailto_and_handles_simulated_responses(
        self,
    ) -> None:
        async def success(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                request.headers.get("Authorization"),
                "Bearer private-token",
            )
            return httpx.Response(
                200,
                json={"email": "donor+tag@example.test"},
            )

        async def run_contact(
            handler: Callable[[httpx.Request], httpx.Response],
        ) -> tuple[SimpleNamespace, object, object]:
            state = _contact_state(auth_token="private-token")
            client = httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
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
                patch(
                    "doafacil.detalhe_doacao.rx.call_script",
                    return_value="mailto-navigation",
                ) as call_script,
            ):
                result = await DonationDetailState.request_donor_contact.fn(
                    state
                )
            return state, result, call_script

        async def run(
            handler: Callable[[httpx.Request], httpx.Response],
        ) -> tuple[SimpleNamespace, object, object]:
            return await run_contact(handler)

        state, result, call_script = asyncio.run(run(success))
        self.assertEqual(result, "mailto-navigation")
        call_script.assert_called_once_with(
            "window.location.href = "
            '"mailto:donor%2Btag@example.test?subject=Sobre%20a%20doa'
            '%C3%A7%C3%A3o%3A%20Carrinho%20de%20brinquedo";'
        )
        self.assertEqual(state.contact_message, "")
        self.assertFalse(hasattr(state, "email"))
        self.assertFalse(hasattr(state, "owner_id"))

        async def forbidden(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"message": "Own donation"})

        async def not_found(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404)

        async def unauthorized(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401)

        async def network_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("offline", request=request)

        for handler, expected_message in (
            (forbidden, DONOR_OWN_DONATION_MESSAGE),
            (not_found, DONOR_CONTACT_ERROR_MESSAGE),
            (unauthorized, DONOR_CONTACT_ERROR_MESSAGE),
            (network_error, DONOR_CONTACT_ERROR_MESSAGE),
        ):
            with self.subTest(expected_message=expected_message):
                state, result, call_script = asyncio.run(run(handler))
                self.assertIsNone(result)
                call_script.assert_not_called()
                self.assertEqual(state.contact_message, expected_message)
                self.assertFalse(hasattr(state, "email"))
                self.assertFalse(hasattr(state, "owner_id"))

    def test_chat_button_without_session_redirects_without_request(self) -> None:
        state = _chat_state(auth_token="")
        with (
            patch("doafacil.detalhe_doacao.rx.redirect", return_value="login-redirect") as redirect,
            patch("doafacil.detalhe_doacao.httpx.AsyncClient") as async_client,
        ):
            result = _run_start_chat(state)
        self.assertEqual(result, "login-redirect")
        redirect.assert_called_once_with("/login")
        async_client.assert_not_called()

    def test_chat_button_starts_conversation_and_opens_chat(self) -> None:
        requests: list[httpx.Request] = []

        def respond(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "conversation_id": 77,
                    "donation_id": 42,
                    "last_message_at": 1762800000000,
                    "other_user_first_name": "Ana",
                    "donation_title": "Carrinho de brinquedo",
                    "donation_status": "disponível",
                },
                request=request,
            )

        state = _chat_state(auth_token="private-token")
        client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api:catalog"}),
            patch("doafacil.detalhe_doacao.httpx.AsyncClient", return_value=client),
            patch("doafacil.detalhe_doacao.rx.redirect", return_value="chat-redirect") as redirect,
        ):
            result = _run_start_chat(state)

        self.assertEqual(result, "chat-redirect")
        redirect.assert_called_once_with("/chat?conversa=77")
        self.assertEqual(requests[0].url.path, "/api:catalog/catalog/chat/conversations/start")
        self.assertEqual(requests[0].headers["Authorization"], "Bearer private-token")
        self.assertEqual(requests[0].read(), b'{"donation_id":42}')
        self.assertFalse(state.is_starting_chat)

    def test_chat_button_errors_show_messages_without_navigation(self) -> None:
        cases = [
            (404, {"code": "ERROR_CODE_NOT_FOUND", "message": "Conversa não encontrada."}, CHAT_NOT_AVAILABLE_FOR_DONATION_MESSAGE, False),
            (500, {"message": "x"}, CHAT_START_ERROR_MESSAGE, True),
        ]
        for status, body, expected, is_error in cases:
            with self.subTest(status=status):
                state = _chat_state(auth_token="private-token")
                client = httpx.AsyncClient(
                    transport=httpx.MockTransport(
                        lambda request, s=status, b=body: httpx.Response(s, json=b, request=request)
                    )
                )
                with (
                    patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api:catalog"}),
                    patch("doafacil.detalhe_doacao.httpx.AsyncClient", return_value=client),
                    patch("doafacil.detalhe_doacao.rx.redirect") as redirect,
                ):
                    result = _run_start_chat(state)
                self.assertIsNone(result)
                redirect.assert_not_called()
                self.assertEqual(state.contact_message, expected)
                self.assertIs(state.contact_message_is_error, is_error)

    def test_chat_button_network_error_and_401(self) -> None:
        def fail(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("sem rede", request=request)

        state = _chat_state(auth_token="private-token")
        client = httpx.AsyncClient(transport=httpx.MockTransport(fail))
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api:catalog"}),
            patch("doafacil.detalhe_doacao.httpx.AsyncClient", return_value=client),
        ):
            result = _run_start_chat(state)
        self.assertIsNone(result)
        self.assertEqual(state.contact_message, CHAT_START_ERROR_MESSAGE)

        state = _chat_state(auth_token="expired-token")
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(401, json={"message": "x"}, request=request)
            )
        )
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api:catalog"}),
            patch("doafacil.detalhe_doacao.httpx.AsyncClient", return_value=client),
            patch("doafacil.detalhe_doacao.rx.redirect", return_value="login-redirect"),
        ):
            result = _run_start_chat(state)
        self.assertEqual(result, "login-redirect")
        self.assertEqual(state.auth_token, "")
        self.assertEqual(state.account_name, "")

    def test_chat_button_is_wired_and_disabled_while_starting(self) -> None:
        rendered = str(donation_detail_page())
        self.assertIn("start_chat", rendered)
        self.assertIn("is_starting_chat", rendered)
        self.assertNotIn("show_chat_unavailable", rendered)

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
                "donor_photo",
                "donor_email_verified",
                "donor_active",
                "donor_completed",
                "photos",
            },
        )
        self.assertIs(detail["donor_email_verified"], True)
        self.assertEqual((detail["donor_active"], detail["donor_completed"]), (3, 1))
        self.assertNotIn("email", detail)
        self.assertNotIn("private@example.com", repr(detail))
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
            # Selo e contadores de quem doa (change perfil-credibilidade).
            {k: v for k, v in DETAIL_PAYLOAD.items() if k != "donor_email_verified"},
            {**DETAIL_PAYLOAD, "donor_email_verified": None},
            {**DETAIL_PAYLOAD, "donor_email_verified": "true"},
            {k: v for k, v in DETAIL_PAYLOAD.items() if k != "donor_counts"},
            {**DETAIL_PAYLOAD, "donor_counts": [1, 2]},
            {**DETAIL_PAYLOAD, "donor_counts": {"active": -1, "completed": 0}},
            {**DETAIL_PAYLOAD, "donor_counts": {"active": 1.5, "completed": 0}},
            {**DETAIL_PAYLOAD, "donor_counts": {"active": True, "completed": 0}},
            {**DETAIL_PAYLOAD, "donor_counts": {"active": 1}},
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
        self.assertIs(state.donor_email_verified, True)
        self.assertEqual((state.donor_active, state.donor_completed), (3, 1))
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
        self.assertEqual([h.fn for h in page.on_load], [DonationDetailState.load_donation.fn, LoginState.load_account.fn])  # + a conta, uma vez por sessão (change navegacao-celular)

    def test_detail_view_contains_approved_content_and_no_excluded_features(self) -> None:
        page = donation_detail_page()
        contents = _component_contents(page)

        for expected in (
            "Carregando doação...",
            DONATION_NOT_FOUND_MESSAGE,
            DONATION_DETAIL_ERROR_MESSAGE,
            "Detalhes",
            "Categoria",
            "Condição",
            "Localização",
            "Quem doa",
            "Condição: ",
            "Forma de entrega",
            "Preferência de contato",
        ):
            with self.subTest(text=expected):
                self.assertIn(expected, contents)

        for excluded in (
            "Acessar perfil do doador",
            "Em breve",
            "Online",
            "Conta verificada",
            "Avaliações",
            "Bairro",
            "CEP",
            "Cor",
            "Material",
            "Tipo",
            "NOVO",
            "Disponível",
        ):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, contents)

        self.assertIn("Outros meios de comunicação", contents)
        self.assertIn("Chat", contents)
        self.assertIn("LucideMessageCircle", str(page))

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

    def test_back_link_is_shared_accessible_and_returns_home_in_all_states(
        self,
    ) -> None:
        from doafacil.navegacao import back_home_header

        page = donation_detail_page()
        header, state_content = page.children
        rendered_header = str(header)

        # “Voltar ao início” na linha do logotipo, o mesmo cabeçalho do chat.
        self.assertEqual(type(header).__name__, "Box")  # faixa branca com a grade dentro (change navegacao-celular)
        self.assertEqual(type(header.children[0]).__name__, "Grid")
        self.assertEqual(rendered_header, str(back_home_header()))
        self.assertEqual(type(state_content).__name__, "Fragment")
        back_link = header.children[0].children[0]
        self.assertEqual(back_link.custom_attrs.get("aria-label"), "Voltar ao início")
        self.assertIn('"aria-label":"Voltar ao in\\u00edcio"', rendered_header)
        self.assertIn('to:"/"', rendered_header)
        self.assertIn("LucideChevronLeft", rendered_header)
        self.assertIn('"#166B3B"', rendered_header)
        self.assertIn("/logo.svg", rendered_header)
        # Área de toque confortável quando só a seta aparece.
        self.assertIn('"minHeight"] : "44px"', rendered_header)
        self.assertIn('"minWidth"] : "44px"', rendered_header)
        # Sem o link antigo abaixo do cabeçalho.
        self.assertNotIn('"aria-label":"Voltar"', str(page))

        contents = _component_contents(state_content)
        for state_message in (
            "Carregando doação...",
            "Detalhes",
            DONATION_NOT_FOUND_MESSAGE,
            DONATION_DETAIL_ERROR_MESSAGE,
        ):
            with self.subTest(state=state_message):
                self.assertIn(state_message, contents)

    def test_gallery_is_one_grid_with_up_to_five_photos(self) -> None:
        from doafacil.detalhe_doacao import MAX_GALLERY_PHOTOS, _gallery

        self.assertEqual(MAX_GALLERY_PHOTOS, 5)
        rendered = str(_gallery())
        # Um único foreach sobre as 5 primeiras fotos, filhas diretas da grade.
        self.assertEqual(rendered.count("Array.prototype.map.call"), 1)
        self.assertIn("photos_rx_state_.slice(0, 5)", rendered)
        self.assertNotIn("detail-gallery-thumbnails", rendered)
        # Capa com o título como texto alternativo; as demais, “Foto da doação”.
        self.assertIn("title_rx_state_", rendered)
        self.assertIn("Foto da doa\\u00e7\\u00e3o", rendered)
        # Área de cada foto pela posição.
        self.assertIn('["gridArea"] : ["a", "b", "c", "d", "e"]?.at?.(index_rx_state_)', rendered)
        # Altura de 470 px no computador; espaço de 16 px (8 px no celular).
        self.assertIn('["height"] : "470px"', rendered)
        self.assertIn('["gap"] : "16px"', rendered)
        self.assertIn('["gap"] : "8px"', rendered)

    def test_gallery_wide_layout_for_each_photo_count(self) -> None:
        from doafacil.detalhe_doacao import GALLERY_WIDE_LAYOUTS, _gallery

        self.assertEqual(
            GALLERY_WIDE_LAYOUTS,
            {
                1: ("minmax(0, 1fr)", "'a'"),
                2: ("minmax(0, 1fr) minmax(0, 1fr)", "'a b'"),
                3: ("minmax(0, 2fr) minmax(0, 1fr)", "'a b' 'a c'"),
                4: ("minmax(0, 1fr) minmax(0, 1fr)", "'a b' 'c d'"),
                5: ("repeat(4, minmax(0, 1fr))", "'a a b c' 'a a d e'"),
            },
        )
        rendered = str(_gallery())
        wide = rendered.split('"@media screen and (min-width: 62em)"', 1)[1]
        for size, (columns, areas) in GALLERY_WIDE_LAYOUTS.items():
            with self.subTest(size=size):
                self.assertIn(f'"{columns}"', wide)
                self.assertIn(f'"{areas}"', wide)
        # Até 2 fotos, uma linha; com 3 ou mais, duas linhas iguais.
        self.assertIn(
            'gallery_size_rx_state_ > 2) ? "minmax(0, 1fr) minmax(0, 1fr)" : "minmax(0, 1fr)"',
            wide,
        )

    def test_gallery_narrow_layout_has_cover_on_top_and_square_thumbnails(self) -> None:
        from doafacil.detalhe_doacao import _gallery

        rendered = str(_gallery())
        narrow = rendered.split('"@media screen and (min-width: 0px)"', 1)[1].split(
            '"@media screen and (min-width: 62em)"', 1
        )[0]
        self.assertIn('"repeat(4, minmax(0, 1fr))"', narrow)
        self.assertIn(
            "gallery_size_rx_state_ > 1) ? \"'a a a a' 'b c d e'\" : \"'a a a a'\"",
            narrow,
        )
        self.assertIn('gallery_size_rx_state_ > 1) ? "300px auto" : "300px"', narrow)
        # Miniaturas quadradas; a capa segue a linha de 300 px.
        self.assertIn('=== 0?.valueOf?.()) ? "auto" : "1 / 1"', rendered)

    def test_gallery_size_caps_at_five(self) -> None:
        for count, expected in ((0, 0), (1, 1), (3, 3), (5, 5), (7, 5)):
            with self.subTest(count=count):
                state = SimpleNamespace(photos=[f"https://images.example/{n}.jpg" for n in range(count)])
                self.assertEqual(DonationDetailState.gallery_size.fget(state), expected)

    def test_gallery_handles_one_and_five_photos_from_parser(self) -> None:
        one = _parse_donation_detail({**DETAIL_PAYLOAD, "photos": ["https://images.example/a.jpg"]}, 42)
        five_urls = [f"https://images.example/{n}.jpg" for n in range(5)]
        five = _parse_donation_detail({**DETAIL_PAYLOAD, "photos": five_urls}, 42)
        self.assertEqual(one["photos"][1:5], [])
        self.assertEqual(five["photos"][0], five_urls[0])
        self.assertEqual(five["photos"][1:5], five_urls[1:])

    def test_summary_card_has_title_condition_and_accessible_primary_button(self) -> None:
        from doafacil.detalhe_doacao import _summary_card

        card = _summary_card()
        rendered = str(card)
        contents = _component_contents(card)
        self.assertIn("title_rx_state_", rendered)
        self.assertIn("Condição: ", contents)
        self.assertIn("Outros meios de comunicação", contents)
        self.assertIn("Chat", contents)
        # Verde AA do projeto, e não o #00A859 (cerca de 2,9:1 com branco).
        self.assertIn('"#007A42"', rendered)
        self.assertNotIn("#00A859", rendered)
        self.assertIn('"1px solid #85858D"', rendered)
        self.assertIn("request_donor_contact", rendered)
        self.assertIn("start_chat", rendered)
        self.assertIn("contact_message", rendered)
        self.assertIn('role:"status"', rendered)
        self.assertIn("0 8px 13px rgba(0, 0, 0, 0.15)", rendered)

    def test_title_and_description_below_gallery_with_css_uppercase(self) -> None:
        from doafacil.detalhe_doacao import _title_and_description

        rendered = str(_title_and_description())
        self.assertIn('"textTransform"] : "uppercase"', rendered)
        # O texto lido continua o original (sem .toUpperCase no conteúdo).
        self.assertNotIn("toUpperCase", rendered)
        self.assertIn("description_rx_state_", rendered)
        self.assertIn('"whiteSpace"] : "pre-wrap"', rendered)

    def test_layout_order_desktop_and_mobile(self) -> None:
        from doafacil.detalhe_doacao import _donation_content

        rendered = str(_donation_content())
        # Celular: uma coluna nesta ordem; computador: duas colunas.
        self.assertIn(
            "\"'gallery' 'summary' 'title' 'details' 'location' 'donor'\"",
            rendered,
        )
        self.assertIn(
            "\"'gallery summary' 'title donor' 'details donor' 'location donor'\"",
            rendered,
        )
        # Nenhuma aspa dupla sem escape dentro do valor (JavaScript válido).
        self.assertNotIn('""gallery', rendered)
        self.assertIn("minmax(0, 2.6fr) minmax(280px, 1fr)", rendered)
        # Celular: 16 px de margem lateral, sem rolagem horizontal.
        # Contêiner de Minhas doações (change acabamento): 1200 px com as
        # margens do cabeçalho (16 px no celular, 24 px a partir de 992 px).
        self.assertIn('["maxWidth"] : "1200px"', rendered)
        # (no detalhe, o padding sai junto com as áreas da grade de cada faixa)
        self.assertIn('["paddingInlineStart"] : "16px", ["paddingInlineEnd"] : "16px"', rendered)
        self.assertIn('["paddingInlineStart"] : "24px", ["paddingInlineEnd"] : "24px"', rendered)

    def test_details_grid_has_four_items_with_icon_label_and_value(self) -> None:
        from doafacil.detalhe_doacao import _details_section

        section = _details_section()
        rendered = str(section)
        labels = [
            text
            for text in _component_contents(section)
            if text not in {"Detalhes"}
        ]
        self.assertEqual(
            labels,
            ["Categoria", "Condição", "Forma de entrega", "Preferência de contato"],
        )
        for state_var in ("category", "condition", "delivery_method", "contact_preference"):
            with self.subTest(value=state_var):
                self.assertIn(f"{state_var}_rx_state_", rendered)
        self.assertEqual(rendered.count("/detalhe-atributo.svg"), 4)
        self.assertEqual(rendered.count('"aria-hidden":"true"'), 4)
        self.assertIn('"fontSize"] : "0.75rem"', rendered)
        # 1 coluna no celular, 2 no sm e 4 no lg.
        self.assertIn("repeat(2, minmax(0, 1fr))", rendered)
        self.assertIn("repeat(4, minmax(0, 1fr))", rendered)
        for excluded in ("Cor", "Material", "Tipo"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, labels)

    def test_location_card_shows_only_city_and_state(self) -> None:
        from doafacil.detalhe_doacao import _location_card

        card = _location_card()
        rendered = str(card)
        self.assertEqual(_component_contents(card), ["Localização", ", "])
        self.assertIn("city_rx_state_", rendered)
        self.assertIn("state_rx_state_", rendered)
        self.assertIn("/detalhe-localizacao.svg", rendered)
        self.assertIn('"aria-hidden":"true"', rendered)
        for excluded in ("neighborhood", "zip_code", "bairro", "CEP", "Zona"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, rendered)

    def test_donor_card_has_sections_with_existing_data_only(self) -> None:
        from doafacil.detalhe_doacao import _donor_card

        card = _donor_card()
        rendered = str(card)
        # Textos fixos, na ordem: topo, botão, “Doações” e “Informações verificadas”.
        self.assertEqual(
            _component_contents(card),
            [
                "Quem doa",
                "No DoaFácil desde ",
                ", ",
                "Ver perfil de quem doa",
                "Doações",
                "Informações verificadas",
                "E-mail",
            ],
        )
        for var in (
            "donor_first_name",
            "donor_member_since",
            "city",
            "state",
            "donor_active",
            "donor_completed",
            "donor_email_verified",
        ):
            with self.subTest(var=var):
                self.assertIn(f"{var}_rx_state_", rendered)
        # Ícones decorativos: calendário, local, pacotes e o check verde.
        for icon in ("LucideCalendar", "LucideMapPin", "LucidePackage", "LucidePackageCheck", "LucideCircleCheck"):
            with self.subTest(icon=icon):
                self.assertIn(icon, rendered)
        self.assertNotIn('"aria-hidden":"false"', rendered)
        self.assertIn('"#166B3B"', rendered)
        # Dois divisores de 1 px entre as seções.
        self.assertEqual(rendered.count("detail-donor-divider"), 2)
        self.assertIn("1px solid #D9D9D9", rendered)
        # Nada que o site não tem, e nunca o e-mail.
        self.assertNotIn("@", rendered)
        self.assertNotIn("donor_email_rx_state_", rendered)
        contents = " ".join(_component_contents(card)).lower()
        for excluded in ("online", "avalia", "estrela", "cancelad", "cpf", "não verificado"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, contents)

    def test_donor_card_counts_use_profile_labels_with_singular(self) -> None:
        from doafacil.detalhe_doacao import _donor_card

        rendered = str(_donor_card())
        # Os mesmos rótulos do perfil público e de Minhas doações.
        self.assertIn(
            'donor_active_rx_state_?.valueOf?.() === 1?.valueOf?.()) ? "Doa\\u00e7\\u00e3o" : "Doa\\u00e7\\u00f5es"',
            rendered,
        )
        self.assertIn(
            'donor_completed_rx_state_?.valueOf?.() === 1?.valueOf?.()) ? "Doa\\u00e7\\u00e3o realizada" : "Doa\\u00e7\\u00f5es realizadas"',
            rendered,
        )
        for old_label in ("Dispon", "Conclu"):
            with self.subTest(old_label=old_label):
                self.assertNotIn(old_label, rendered)

    def test_donor_card_optional_parts_depend_on_data(self) -> None:
        from doafacil.detalhe_doacao import _donor_card

        rendered = str(_donor_card())
        # “Desde” só com o texto lido do perfil público.
        self.assertIn(
            '(!((reflex___state____state__doafacil___login____login_state__doafacil___detalhe_doacao____donation_detail_state.donor_member_since_rx_state_?.valueOf?.() === ""?.valueOf?.()))?',
            rendered,
        )
        # “Informações verificadas”, com o divisor, só com o e-mail verificado.
        verified_at = rendered.index("donor_email_verified_rx_state_?(")
        self.assertLess(verified_at, rendered.rindex("detail-donor-divider"))
        self.assertLess(verified_at, rendered.index("Informa\\u00e7\\u00f5es verificadas"))
        self.assertGreater(verified_at, rendered.index("detail-donor-divider"))

    def test_donor_card_is_not_a_link_and_button_goes_to_profile(self) -> None:
        from doafacil.detalhe_doacao import _donor_card

        card = _donor_card()
        rendered = str(card)
        # O cartão é uma caixa; o único link é o botão, com o id da doação.
        self.assertNotEqual(type(card).__name__, "Link")
        links = [n for n in _all_component_nodes(card) if type(n).__name__ == "Link"]
        self.assertEqual(len(links), 1)
        self.assertEqual(rendered.count("ReactRouterLink"), 1)
        self.assertIn('"/doacao/"+', rendered)
        self.assertIn("donation_id_rx_state_", rendered)
        self.assertIn('"/quem-doa"', rendered)
        self.assertNotIn("owner_id", rendered)
        self.assertNotIn("user_id", rendered)

    def test_profile_button_is_outlined_full_width_and_accessible(self) -> None:
        from doafacil.detalhe_doacao import _donor_profile_button

        rendered = str(_donor_profile_button())
        # Rótulo que começa pelo texto visível e diz de quem é o perfil.
        self.assertIn('"aria-label":("Ver perfil de quem doa, "+', rendered)
        self.assertIn("donor_first_name_rx_state_", rendered)
        self.assertIn('["width"] : "100%"', rendered)
        self.assertIn('["minHeight"] : "44px"', rendered)
        self.assertIn('["border"] : "1px solid #007A42"', rendered)
        self.assertIn('["color"] : "#007A42"', rendered)
        self.assertIn("&:hover", rendered)
        self.assertIn("&:focus-visible", rendered)
        self.assertIn("2px solid #007A42", rendered)

    def test_detail_has_no_other_profile_buttons(self) -> None:
        contents = _component_contents(donation_detail_page())
        # O perfil só se abre pelo botão do cartão “Quem doa”.
        self.assertEqual(contents.count("Ver perfil de quem doa"), 1)
        for excluded in ("Acessar perfil do doador", "Ver perfil completo", "Ver perfil", "Perfil"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, contents)

    def test_figma_icons_exist_with_root_size(self) -> None:
        for name, size in (("detalhe-atributo.svg", "18"), ("detalhe-localizacao.svg", "56")):
            with self.subTest(icon=name):
                svg = Path("assets", name).read_text(encoding="utf-8")
                self.assertTrue(svg.startswith("<svg"))
                self.assertIn(f'width="{size}"', svg.split(">", 1)[0])
                self.assertIn(f'height="{size}"', svg.split(">", 1)[0])

    # Foto única e visualizador -------------------------------------------

    def test_single_photo_is_whole_and_two_to_five_use_cover(self) -> None:
        from doafacil.detalhe_doacao import _gallery

        rendered = str(_gallery())
        # Uma foto só: inteira (contain); de 2 a 5: cover.
        self.assertIn(
            '["objectFit"] : ((reflex___state____state__doafacil___login____login_state__doafacil___detalhe_doacao____donation_detail_state.gallery_size_rx_state_ > 1) ? "cover" : "contain")',
            rendered,
        )
        self.assertIn('["objectPosition"] : "center"', rendered)
        self.assertIn('["background"] : "#EEEEEE"', rendered)
        self.assertIn('["borderRadius"] : "8px"', rendered)
        # Mesmas alturas de antes: 300 px no celular e 470 px no computador.
        self.assertIn('"300px"', rendered)
        self.assertIn('["height"] : "470px"', rendered)

    def test_gallery_photos_are_buttons_that_open_the_viewer(self) -> None:
        from doafacil.detalhe_doacao import _gallery

        rendered = str(_gallery())
        # Um botão só, gerado para cada foto, abrindo o visualizador nela.
        self.assertEqual(rendered.count('type:"button"'), 1)
        self.assertEqual(rendered.count("open_viewer"), 1)
        self.assertIn("(index_rx_state_ + 1)", rendered)
        self.assertIn('"Ampliar foto "+', rendered)
        self.assertIn('" de "', rendered)
        self.assertIn('"cursor"] : "zoom-in"', rendered)

    def _viewer_state(self, photos: int = 5, **overrides: object) -> SimpleNamespace:
        values = {
            "photos": [f"https://images.example/{n}.jpg" for n in range(photos)],
            "viewer_open": False,
            "viewer_index": 0,
            "viewer_zoomed": False,
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_viewer_opens_on_chosen_photo_and_closes(self) -> None:
        state = self._viewer_state(viewer_zoomed=True)
        DonationDetailState.open_viewer.fn(state, 3)
        self.assertEqual((state.viewer_open, state.viewer_index, state.viewer_zoomed), (True, 3, False))
        DonationDetailState.open_viewer.fn(state, 99)
        self.assertEqual(state.viewer_index, 4)
        DonationDetailState.toggle_zoom.fn(state)
        DonationDetailState.set_viewer_open.fn(state, False)
        self.assertEqual((state.viewer_open, state.viewer_zoomed), (False, False))
        DonationDetailState.open_viewer.fn(state, 0)
        DonationDetailState.set_viewer_open.fn(state, True)
        self.assertTrue(state.viewer_open)
        DonationDetailState.close_viewer.fn(state)
        self.assertFalse(state.viewer_open)
        empty = self._viewer_state(photos=0)
        DonationDetailState.open_viewer.fn(empty, 0)
        self.assertFalse(empty.viewer_open)

    def test_viewer_navigation_wraps_and_resets_zoom(self) -> None:
        state = self._viewer_state(viewer_open=True, viewer_index=4, viewer_zoomed=True)
        DonationDetailState.next_photo.fn(state)
        self.assertEqual((state.viewer_index, state.viewer_zoomed), (0, False))
        DonationDetailState.prev_photo.fn(state)
        self.assertEqual(state.viewer_index, 4)
        DonationDetailState.viewer_key_down.fn(state, "ArrowLeft")
        self.assertEqual(state.viewer_index, 3)
        DonationDetailState.viewer_key_down.fn(state, "ArrowRight")
        self.assertEqual(state.viewer_index, 4)
        DonationDetailState.viewer_key_down.fn(state, "a")
        self.assertEqual(state.viewer_index, 4)
        DonationDetailState.toggle_zoom.fn(state)
        self.assertTrue(state.viewer_zoomed)
        DonationDetailState.toggle_zoom.fn(state)
        self.assertFalse(state.viewer_zoomed)

    def test_viewer_with_one_photo_does_not_navigate(self) -> None:
        state = self._viewer_state(photos=1, viewer_open=True)
        for step in (
            lambda: DonationDetailState.next_photo.fn(state),
            lambda: DonationDetailState.prev_photo.fn(state),
            lambda: DonationDetailState.viewer_key_down.fn(state, "ArrowRight"),
            lambda: DonationDetailState.viewer_key_down.fn(state, "ArrowLeft"),
        ):
            step()
            self.assertEqual(state.viewer_index, 0)

    def test_viewer_component_modal_controls_and_accessibility(self) -> None:
        from doafacil.detalhe_doacao import _photo_viewer

        viewer = _photo_viewer()
        rendered = str(viewer)
        # Diálogo do Radix: foco preso, Esc e devolução do foco.
        self.assertIn("RadixThemesDialog.Root", rendered)
        self.assertIn("onOpenChange", rendered)
        self.assertIn("set_viewer_open", rendered)
        self.assertIn("viewer_open_rx_state_", rendered)
        self.assertIn("RadixThemesDialog.Title", rendered)
        # Contador “N de M”.
        self.assertIn("viewer_index_rx_state_ + 1", rendered)
        self.assertIn('" de "', rendered)
        # Tela cheia; clique no fundo fecha.
        self.assertIn('"position"] : "fixed"', rendered)
        self.assertIn('"inset"] : "0"', rendered)
        self.assertIn("close_viewer", rendered)
        # Foto inteira (contain) e zoom 1x/2x com rolagem e pinça.
        self.assertIn('"objectFit"] : "contain"', rendered)
        self.assertIn("toggle_zoom", rendered)
        self.assertIn('"calc(200vw - 64px)"', rendered)
        self.assertIn('"calc(200vw - 320px)"', rendered)
        self.assertIn('"overflow"] : "auto"', rendered)
        self.assertIn("pinch-zoom", rendered)
        self.assertIn('"Ampliar foto"', rendered)
        self.assertIn('"Reduzir foto"', rendered)
        # Botões com rótulo e 48 px; cliques não chegam ao fundo.
        for label in ('"aria-label":"Fechar"', '"aria-label":"Foto anterior"', '"aria-label":"Pr\\u00f3xima foto"'):
            with self.subTest(label=label):
                self.assertIn(label, rendered)
        self.assertGreaterEqual(rendered.count('"minWidth"] : "48px"'), 4)
        self.assertGreaterEqual(rendered.count('"minHeight"] : "48px"'), 4)
        self.assertIn("stopPropagation", rendered)
        # ‹ e › só com mais de uma foto.
        arrows = [
            n
            for n in _all_component_nodes(viewer)
            if type(n).__name__ == "Cond" and "Foto anterior" in str(n)
        ]
        self.assertTrue(arrows)
        self.assertIn("photos_rx_state_.length > 1", str(arrows[0].cond).replace("?.", "."))
        self.assertNotIn("Foto anterior", str(arrows[0].children[1]))

    def test_viewer_cream_backdrop_fit_and_controls_inside_the_screen(self) -> None:
        from doafacil.detalhe_doacao import _photo_viewer

        viewer = _photo_viewer()
        rendered = str(viewer)
        # 1. Fundo creme semitransparente com desfoque, sem o véu escuro do
        # Radix; textos e ícones em #1F1F1F; botões brancos com sombra.
        self.assertIn('"rgba(255, 246, 232, 0.85)"', rendered)
        self.assertIn('"backdropFilter"] : "blur(6px)"', rendered)
        self.assertIn('"WebkitBackdropFilter"] : "blur(6px)"', rendered)
        self.assertNotIn("rgba(0, 0, 0, 0.92)", rendered)
        styles = [n for n in _all_component_nodes(viewer) if type(n).__name__ == "StyleEl"]
        self.assertEqual(len(styles), 1)
        css = str(styles[0].children[0])
        self.assertIn(".rt-BaseDialogOverlay:has(.detail-viewer)::before", css)
        self.assertIn("background-color:transparent", css)
        self.assertGreaterEqual(rendered.count('"color"] : "#1F1F1F"'), 4)
        self.assertNotIn('"color"] : "white"', rendered)
        self.assertGreaterEqual(rendered.count('"background"] : "#FFFFFF"'), 3)
        self.assertGreaterEqual(rendered.count('"0 2px 8px rgba(0, 0, 0, 0.18)"'), 3)
        # 2. Em 1x a foto cabe inteira abaixo do cabeçalho de 80 px.
        self.assertIn('"height"] : "80px"', rendered)
        self.assertIn('"calc(100dvh - 80px - 16px)"', rendered)
        self.assertIn('"calc(100vw - 32px)"', rendered)
        self.assertIn('"calc(100vw - 160px)"', rendered)
        # 3. X e setas a 16 px das bordas, no viewport (fixed + inset 0,
        # 100% em vez de 100vw, que soma a barra de rolagem).
        self.assertNotIn('"100vw"', rendered)
        self.assertIn('"padding"] : "0 16px"', rendered)
        self.assertIn('"left"] : "16px"', rendered)
        self.assertIn('"right"] : "16px"', rendered)
        self.assertIn('"calc(50% + 40px)"', rendered)

    def test_viewer_listens_to_arrow_keys_only_inside_the_dialog(self) -> None:
        from doafacil.detalhe_doacao import _photo_viewer

        nodes = _all_component_nodes(_photo_viewer())
        listeners = [n for n in nodes if type(n).__name__ == "WindowEventListener"]
        self.assertEqual(len(listeners), 1)
        # O evento vira um hook do React; o nome aparece no código do hook.
        self.assertIn("on_key_down", listeners[0].event_triggers)
        self.assertTrue(any("viewer_key_down" in hook for hook in listeners[0]._get_all_hooks()))
        contents = [n for n in nodes if type(n).__name__ == "DialogContent"]
        self.assertEqual(len(contents), 1)
        self.assertIn(listeners[0], contents[0].children)

    def test_load_donation_closes_the_viewer(self) -> None:
        state = SimpleNamespace(
            router=SimpleNamespace(url=SimpleNamespace(path="/doacao/abc", query_parameters={})),
            viewer_open=True,
            viewer_index=3,
            viewer_zoomed=True,
            published_notice_id=0,
        )
        asyncio.run(DonationDetailState.load_donation.fn(state))
        self.assertEqual((state.viewer_open, state.viewer_index, state.viewer_zoomed), (False, 0, False))

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
            url=SimpleNamespace(path=f"/doacao/{route_id}", query_parameters={})
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
        auth_token="",
        contact_message="",
        contact_message_is_error=False,
        published_notice_id=0,
        show_published_notice=False,
    )


def _contact_state(
    *,
    auth_token: str,
    contact_preference: str = "E-mail",
) -> SimpleNamespace:
    return SimpleNamespace(
        donation_id=42,
        title="Carrinho de brinquedo",
        contact_preference=contact_preference,
        auth_token=auth_token,
        contact_message="",
        contact_message_is_error=False,
    )


def _chat_state(*, auth_token: str) -> SimpleNamespace:
    return SimpleNamespace(
        donation_id=42,
        auth_token=auth_token,
        account_name="Bia" if auth_token else "",
        contact_message="",
        contact_message_is_error=False,
        is_starting_chat=False,
    )


def _start_chat_events(state: SimpleNamespace) -> list:
    """Tudo o que o start_chat emite, em ordem (change chat-carregamento)."""

    async def collect() -> list:
        return [item async for item in DonationDetailState.start_chat.fn(state)]

    return asyncio.run(collect())


def _run_start_chat(state: SimpleNamespace):
    emitted = [item for item in _start_chat_events(state) if item is not None]
    return emitted[-1] if emitted else None


class ChatButtonLoadingTests(unittest.TestCase):
    """Change chat-carregamento: o botão “Chat” mostra o carregamento antes
    do POST, sem pedido a mais ao Xano."""

    def test_loading_is_sent_before_the_request(self) -> None:
        state = _chat_state(auth_token="private-token")
        seen: list[bool] = []

        def respond(request: httpx.Request) -> httpx.Response:
            seen.append(state.is_starting_chat)
            return httpx.Response(
                200,
                json={
                    "conversation_id": 77,
                    "donation_id": 42,
                    "last_message_at": 1762800000000,
                    "other_user_first_name": "Ana",
                    "donation_title": "Carrinho de brinquedo",
                    "donation_status": "disponível",
                },
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(respond))

        async def run() -> list:
            events = []
            generator = DonationDetailState.start_chat.fn(state)
            first = await generator.__anext__()
            # Primeiro envio: só o estado, com o carregamento ligado e nenhum
            # pedido feito ainda.
            events.append((first, state.is_starting_chat, list(seen)))
            async for item in generator:
                events.append((item, state.is_starting_chat, list(seen)))
            return events

        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api:catalog"}),
            patch("doafacil.detalhe_doacao.httpx.AsyncClient", return_value=client),
            patch("doafacil.detalhe_doacao.rx.redirect", return_value="chat-redirect"),
        ):
            events = asyncio.run(run())

        self.assertEqual(events[0], (None, True, []))
        self.assertEqual(events[-1], ("chat-redirect", False, [True]))
        self.assertEqual(len(seen), 1)

    def test_loading_turns_off_after_failure(self) -> None:
        state = _chat_state(auth_token="private-token")
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(500, json={"message": "x"}, request=request)
            )
        )
        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api:catalog"}),
            patch("doafacil.detalhe_doacao.httpx.AsyncClient", return_value=client),
        ):
            events = _start_chat_events(state)
        self.assertEqual(events, [None])
        self.assertFalse(state.is_starting_chat)

    def test_second_click_while_starting_does_nothing(self) -> None:
        state = _chat_state(auth_token="private-token")
        state.is_starting_chat = True
        with patch("doafacil.detalhe_doacao.httpx.AsyncClient") as async_client:
            self.assertEqual(_start_chat_events(state), [])
        async_client.assert_not_called()

    def test_chat_button_shows_loading(self) -> None:
        rendered = str(donation_detail_page())
        self.assertRegex(rendered, r"loading:[^,}]*is_starting_chat")


if __name__ == "__main__":
    unittest.main()


class DetailRetryTests(unittest.TestCase):
    """Change navegacao-celular: a falha do detalhe oferece o botão de tentar
    de novo. Change correcoes-revisao: o texto é “Tentar de novo”, como nas
    outras páginas, e o botão mostra “Carregando doação...” na hora."""

    def test_error_state_has_retry_that_reloads(self) -> None:
        rendered = str(donation_detail_page())
        retry = rendered[rendered.index('className:"detail-retry"') :][:1500]
        self.assertIn('"Tentar de novo"', retry)
        self.assertNotIn("Tentar novamente", rendered)
        self.assertIn("retry_donation", retry)
        self.assertIn('["minHeight"] : "44px"', retry)
        # Logo depois da mensagem de falha, no ramo do estado de erro.
        import json

        from doafacil.detalhe_doacao import DONATION_DETAIL_ERROR_MESSAGE

        message_at = rendered.index(json.dumps(DONATION_DETAIL_ERROR_MESSAGE))
        retry_at = rendered.index('className:"detail-retry"')
        self.assertLess(message_at, retry_at)
        self.assertLess(retry_at - message_at, 1500)


DONOR_PROFILE_PAYLOAD = {
    "donor": {
        "first_name": "Ana",
        "city": "Campinas",
        "state": "SP",
        "member_since": "2020-10",
        "email_verified": True,
        "counts": {"active": 3, "completed": 4},
    },
    "items": [],
    "page": 1,
    "per_page": 12,
    "total": 0,
    "page_total": 0,
}


class DonorMemberSinceTests(unittest.TestCase):
    """“No DoaFácil desde …” lido do perfil público (change quem-doa-completo)."""

    BASE_URL = "https://xano.example/api:catalog"

    def setUp(self) -> None:
        from doafacil import cache_publico

        cache_publico.clear()
        self.addCleanup(cache_publico.clear)

    def _fetch(self, handler: Callable[[httpx.Request], httpx.Response]) -> str:
        from doafacil.detalhe_doacao import _fetch_donor_member_since

        async def run() -> str:
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await _fetch_donor_member_since(client, self.BASE_URL, 42)

        return asyncio.run(run())

    def test_reads_member_since_from_profile_page_one(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api:catalog/catalog/donations/donor")
            self.assertEqual(request.url.params.get("donation_id"), "42")
            self.assertEqual(request.url.params.get("page"), "1")
            return httpx.Response(200, json=DONOR_PROFILE_PAYLOAD)

        self.assertEqual(self._fetch(respond), "outubro de 2020")

    def test_any_profile_failure_hides_the_line(self) -> None:
        def status(code: int) -> Callable[[httpx.Request], httpx.Response]:
            return lambda request: httpx.Response(code)

        def network_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("offline", request=request)

        bad = {**DONOR_PROFILE_PAYLOAD, "donor": {**DONOR_PROFILE_PAYLOAD["donor"], "member_since": "2020-13"}}
        for name, handler in (
            ("404", status(404)),
            ("429", status(429)),
            ("500", status(500)),
            ("rede", network_error),
            ("inválido", lambda request: httpx.Response(200, json=bad)),
            ("não JSON", lambda request: httpx.Response(200, text="oops")),
        ):
            with self.subTest(case=name):
                from doafacil import cache_publico

                cache_publico.clear()
                self.assertEqual(self._fetch(handler), "")

    def test_two_reads_within_60_seconds_make_one_request(self) -> None:
        calls: list[httpx.Request] = []

        def respond(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(200, json=DONOR_PROFILE_PAYLOAD)

        self.assertEqual(self._fetch(respond), "outubro de 2020")
        self.assertEqual(self._fetch(respond), "outubro de 2020")
        self.assertEqual(len(calls), 1)

    def test_load_donation_returns_the_since_event_only_when_loaded(self) -> None:
        async def ok(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=DETAIL_PAYLOAD)

        async def fail(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        for handler, expected in ((ok, DonationDetailState.load_donor_since), (fail, None)):
            with self.subTest(expected=expected):
                from doafacil import cache_publico

                cache_publico.clear()
                state = _state_for_route_id("42")
                state.donor_member_since = "março de 2019"
                client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
                with (
                    patch.dict("os.environ", {"XANO_API_URL": self.BASE_URL}),
                    patch("doafacil.detalhe_doacao.httpx.AsyncClient", return_value=client),
                ):
                    result = asyncio.run(DonationDetailState.load_donation.fn(state))
                self.assertIs(result, expected)
                # Zerado a cada carga: nunca sobra o “desde” de outra doação.
                self.assertEqual(state.donor_member_since, "")

    def _since_state(self, donation_id: int = 42) -> SimpleNamespace:
        return SimpleNamespace(donation_id=donation_id, donor_member_since="")

    def test_since_event_stores_the_label(self) -> None:
        state = self._since_state()

        async def fake(client: object, base_url: str, donation_id: int) -> str:
            self.assertEqual(donation_id, 42)
            return "outubro de 2020"

        with (
            patch.dict("os.environ", {"XANO_API_URL": self.BASE_URL}),
            patch("doafacil.detalhe_doacao._fetch_donor_member_since", side_effect=fake),
        ):
            asyncio.run(DonationDetailState.load_donor_since.fn(state))
        self.assertEqual(state.donor_member_since, "outubro de 2020")

    def test_since_event_ignores_answer_for_a_previous_donation(self) -> None:
        state = self._since_state()

        async def fake(client: object, base_url: str, donation_id: int) -> str:
            state.donation_id = 77  # outra doação foi aberta no meio
            return "outubro de 2020"

        with (
            patch.dict("os.environ", {"XANO_API_URL": self.BASE_URL}),
            patch("doafacil.detalhe_doacao._fetch_donor_member_since", side_effect=fake),
        ):
            asyncio.run(DonationDetailState.load_donor_since.fn(state))
        self.assertEqual(state.donor_member_since, "")

    def test_since_event_does_nothing_without_a_donation(self) -> None:
        state = self._since_state(donation_id=0)
        with patch("doafacil.detalhe_doacao._fetch_donor_member_since") as fetch:
            asyncio.run(DonationDetailState.load_donor_since.fn(state))
        fetch.assert_not_called()
        self.assertEqual(state.donor_member_since, "")

    def test_retry_shows_loading_and_reloads(self) -> None:
        state = SimpleNamespace(view_state="error")
        result = DonationDetailState.retry_donation.fn(state)
        self.assertEqual(state.view_state, "loading")
        self.assertIs(result, DonationDetailState.load_donation)
