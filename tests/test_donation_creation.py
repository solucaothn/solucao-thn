import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from doafacil.cadastro_doacao import (
    CONTACT_PREFERENCES,
    DELIVERY_METHODS,
    IMAGE_TYPES,
    PHOTO_UPLOAD_ID,
    DonationCreateState,
    DonationMissingPhotosError,
    DonationServiceError,
    DonationSessionExpiredError,
    _fetch_categories,
    _fetch_profile,
    _parse_categories,
    _publish_donation,
    _step_five,
    _step_four,
    _step_one,
    _step_two,
    _validate_step,
    donation_creation_page,
    _wizard_content,
)
from doafacil.doafacil import FIELD_PLACEHOLDER_SELECTOR, FIELD_TEXT_SELECTOR, app
from doafacil.fotos_doacao import FORMAT_MESSAGE, check_file

# Fotos já preparadas (change fotos-formulario-doacao): a lista da tela e as
# versões guardadas no servidor, na ordem escolhida.
READY_PHOTOS = [{"id": "b", "thumb": "data:image/png;base64,AA"}, {"id": "a", "thumb": "data:image/png;base64,AA"}]
READY_FILES = {"a": (b"bytes-a", "image/jpeg", "jpg"), "b": (b"bytes-b", "image/png", "png")}


def _publish_state(**overrides) -> SimpleNamespace:
    base = dict(
        is_publishing=False,
        published=False,
        auth_token="test-token",
        current_step=5,
        title="Mesa",
        description="Em bom estado",
        category_id="3",
        condition="Bom",
        delivery_method="A combinar",
        contact_preference="E-mail",
        categories=[{"id": 3, "name": "Livros"}],
        city="Recife",
        state="PE",
        donation_error_message="",
        upload_progress="",
        photos=list(READY_PHOTOS),
        photos_busy=False,
        photo_notice="",
        _photo_files=dict(READY_FILES),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class DonationCreationTests(unittest.TestCase):
    def setUp(self) -> None:
        # Cache de categorias do processo (change navegacao-celular).
        from doafacil.cadastro_doacao import clear_category_cache

        clear_category_cache()

    def test_category_payload_requires_valid_category_ids_and_names(self) -> None:
        # Change correcoes-finais: sem exclusão por nome; “Móveis” é uma
        # categoria como as outras.
        payload = [
            {"id": 3, "name": "Móveis"},
            {"id": 4, "name": " Livros "},
            {"id": "5", "name": "Ferramentas"},
            {"id": 6, "name": ""},
            {"id": True, "name": "Roupas"},
            {"name": "Sem id"},
            "lixo",
            {"id": 7, "name": "Brinquedos"},
        ]
        original_payload = [item.copy() if isinstance(item, dict) else item for item in payload]
        self.assertEqual(
            _parse_categories(payload),
            [
                {"id": 3, "name": "Móveis"},
                {"id": 4, "name": "Livros"},
                {"id": 7, "name": "Brinquedos"},
            ],
        )
        self.assertEqual(payload, original_payload)
        self.assertEqual(_parse_categories([]), [])
        with self.assertRaises(DonationServiceError):
            _parse_categories([{"id": "3", "name": "Móveis"}])
        with self.assertRaises(DonationServiceError):
            _parse_categories({"id": 3, "name": "Móveis"})

    def test_furniture_is_a_valid_option(self) -> None:
        categories = _parse_categories(
            [
                {"id": 4, "name": "Móveis"},
                {"id": 5, "name": "Livros"},
            ]
        )
        state = SimpleNamespace(
            categories=categories,
            category_id="",
            category_name="",
        )

        DonationCreateState.set_category.fn(state, "Móveis")
        self.assertEqual(state.category_id, "4")
        self.assertEqual(state.category_name, "Móveis")

    def test_missing_category_is_not_a_valid_option(self) -> None:
        # Uma categoria apagada do Xano (como “Alimentos”) não vem na lista e
        # não pode ser escolhida.
        categories = _parse_categories([{"id": 5, "name": "Livros"}])
        state = SimpleNamespace(
            categories=categories,
            category_id="",
            category_name="",
        )

        DonationCreateState.set_category.fn(state, "Alimentos")
        self.assertEqual(state.category_id, "")
        self.assertEqual(state.category_name, "")
        self.assertEqual(
            _validate_step(
                2,
                "Mesa",
                "Em bom estado",
                "4",
                "Bom",
                "A combinar",
                "E-mail",
                {category["id"] for category in categories},
                "Recife",
                "PE",
            ),
            "Selecione uma categoria válida para continuar.",
        )

    def test_step_validation_requires_fields_at_their_step(self) -> None:
        categories = {3}
        args = (
            "Mesa",
            "Em bom estado",
            "3",
            "Bom",
            "A combinar",
            "E-mail",
            categories,
            "Recife",
            "PE",
        )

        self.assertIn("nome", _validate_step(1, "", *args[1:]))
        self.assertIn(
            "Descreva",
            _validate_step(2, args[0], "", *args[2:]),
        )
        self.assertIn(
            "categoria",
            _validate_step(
                2,
                args[0],
                args[1],
                "",
                args[3],
                *args[4:],
            ),
        )
        self.assertIn(
            "condição",
            _validate_step(
                2,
                args[0],
                args[1],
                args[2],
                "",
                *args[4:],
            ),
        )
        self.assertIn(
            "entrega",
            _validate_step(
                4,
                *args[:4],
                "",
                args[5],
                *args[6:],
            ),
        )
        self.assertIn(
            "contato",
            _validate_step(
                5,
                *args[:5],
                "",
                *args[6:],
            ),
        )
        self.assertIn(
            "perfil",
            _validate_step(
                4,
                *args[:5],
                args[5],
                args[6],
                "",
                "",
            ),
        )
        self.assertEqual(
            _validate_step(5, *args),
            "",
        )
        self.assertEqual(
            CONTACT_PREFERENCES,
            ("E-mail", "Chat do DoaFácil"),
        )
        contact_options = [
            _literal(node.value)
            for node in _component_nodes(_step_five())
            if type(node).__name__ == "SelectItem"
        ]
        self.assertEqual(contact_options, list(CONTACT_PREFERENCES))
        for preference in CONTACT_PREFERENCES:
            with self.subTest(contact_preference=preference):
                self.assertEqual(
                    _validate_step(
                        5,
                        *args[:5],
                        preference,
                        *args[6:],
                    ),
                    "",
                )
        self.assertIn(
            "contato",
            _validate_step(
                5,
                *args[:5],
                "WhatsApp",
                *args[6:],
            ),
        )
        self.assertEqual(DELIVERY_METHODS, ("A combinar",))
        for unavailable_method in ("Retirada", "Entrega"):
            with self.subTest(delivery_method=unavailable_method):
                self.assertIn(
                    "entrega",
                    _validate_step(
                        4,
                        *args[:4],
                        unavailable_method,
                        *args[5:],
                    ),
                )

    def test_navigation_preserves_fields_and_blocks_missing_title(self) -> None:
        state = SimpleNamespace(
            is_loading_data=False,
            is_publishing=False,
            published=False,
            current_step=1,
            title="",
            description="",
            category_id="",
            condition="",
            delivery_method="",
            contact_preference="",
            categories=[],
            city="",
            state="",
            donation_error_message="",
        )
        DonationCreateState.advance.fn(state)
        self.assertEqual(state.current_step, 1)
        self.assertIn("nome", state.donation_error_message)

        state.title = "Mesa"
        state.donation_error_message = ""
        DonationCreateState.advance.fn(state)
        self.assertEqual(state.current_step, 2)
        self.assertEqual(state.title, "Mesa")
        DonationCreateState.go_back.fn(state)
        self.assertEqual(state.current_step, 1)
        self.assertEqual(state.title, "Mesa")

    def test_photo_step_requires_at_least_one_photo(self) -> None:
        state = SimpleNamespace(
            is_loading_data=False,
            is_publishing=False,
            published=False,
            current_step=3,
            donation_error_message="",
            photos=[],
            photos_busy=False,
        )

        DonationCreateState.advance.fn(state)

        self.assertEqual(state.current_step, 3)
        self.assertEqual(
            state.donation_error_message,
            "Adicione pelo menos uma foto para continuar.",
        )

        # Enquanto as fotos são preparadas, “Continuar” não avança.
        state.photos = list(READY_PHOTOS)
        state.photos_busy = True
        DonationCreateState.advance.fn(state)
        self.assertEqual(state.current_step, 3)

        state.photos_busy = False
        DonationCreateState.advance.fn(state)
        self.assertEqual(state.current_step, 4)
        self.assertEqual(state.donation_error_message, "")

        # “Continuar” não envia arquivos: as fotos já estão no servidor.
        continue_button = next(
            node
            for node in _component_nodes(_wizard_content())
            if type(node).__name__ == "Button"
            and _component_text(node.children) == ["Continuar"]
        )
        rendered = str(continue_button)
        self.assertNotIn("uploadFiles", rendered)
        self.assertIn("advance", rendered)
        self.assertIn("photos_busy_rx_state_", rendered)

    def test_upload_validation_accepts_images_and_rejects_invalid_files(self) -> None:
        self.assertEqual(check_file("mesa.webp", IMAGE_TYPES[".webp"], 10), "")
        for name, mime in (("documento.pdf", "application/pdf"), ("mesa.jpg", "image/png")):
            with self.subTest(filename=name):
                self.assertEqual(check_file(name, mime, 10), FORMAT_MESSAGE)

    def test_category_request_parses_returned_options(self) -> None:
        payload = [
            {"id": 1, "name": "Alimentos"},
            {"id": 2, "name": "Móveis"},
            {"id": 3, "name": "Livros"},
        ]

        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("/catalog/categories"))
            return httpx.Response(200, json=payload)

        async def fetch() -> list[dict[str, object]]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_categories(
                    client,
                    "https://xano.example/api:catalog/catalog/categories",
                )

        # Sem exclusão por nome: o que o Xano devolver aparece.
        self.assertEqual(
            asyncio.run(fetch()),
            [
                {"id": 1, "name": "Alimentos"},
                {"id": 2, "name": "Móveis"},
                {"id": 3, "name": "Livros"},
            ],
        )
        self.assertEqual(
            payload,
            [
                {"id": 1, "name": "Alimentos"},
                {"id": 2, "name": "Móveis"},
                {"id": 3, "name": "Livros"},
            ],
        )

    def test_category_request_reports_backend_failure(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, request=request)

        async def fetch() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await _fetch_categories(
                    client,
                    "https://xano.example/api:catalog/catalog/categories",
                )

        with self.assertRaises(DonationServiceError):
            asyncio.run(fetch())

    def test_category_load_failure_is_reported_after_form_reset(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/catalog/categories"):
                return httpx.Response(503, request=request)
            return httpx.Response(
                200,
                json={"city": "Recife", "state": "PE"},
                request=request,
            )

        client = httpx.AsyncClient(
            transport=httpx.MockTransport(respond)
        )
        state = SimpleNamespace(
            auth_token="test-token",
            is_loading_data=False,
            data_load_failed=False,
            donation_error_message="",
            categories=[],
            city="",
            state="",
            title="Mesa",
        )

        async def load() -> list[object]:
            events = []
            async for event in DonationCreateState.load_initial_data.fn(
                state
            ):
                events.append(event)
            return events

        with (
            patch.dict(
                "os.environ",
                {
                    "XANO_API_URL": "https://xano.example/api:catalog",
                    "XANO_AUTH_API_URL": "https://xano.example/api:auth",
                },
            ),
            patch(
                "doafacil.cadastro_doacao.httpx.AsyncClient",
                return_value=client,
            ),
        ):
            asyncio.run(load())

        self.assertTrue(state.data_load_failed)
        self.assertIn("categorias", state.donation_error_message)
        self.assertEqual(state.title, "")
        self.assertEqual(state.current_step, 1)
        self.assertFalse(state.is_loading_data)

    def test_reentering_after_publication_resets_form_and_reloads_account_data(
        self,
    ) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/catalog/categories"):
                return httpx.Response(
                    200,
                    json=[{"id": 3, "name": "Livros"}],
                    request=request,
                )
            self.assertTrue(request.url.path.endswith("/auth/profile"))
            return httpx.Response(
                200,
                json={"city": "Recife", "state": "PE"},
                request=request,
            )

        client = httpx.AsyncClient(
            transport=httpx.MockTransport(respond)
        )
        state = SimpleNamespace(
            auth_token="test-token",
            current_step=5,
            title="Doação anterior",
            description="Descrição anterior",
            category_id="3",
            category_name="Livros",
            condition="Bom",
            delivery_method="A combinar",
            contact_preference="E-mail",
            categories=[{"id": 3, "name": "Livros"}],
            city="Cidade antiga",
            state="UF",
            is_loading_data=False,
            data_load_failed=False,
            is_publishing=False,
            published=True,
            donation_error_message="Erro anterior",
            upload_progress="Upload anterior",
            photos=list(READY_PHOTOS),
            photos_busy=True,
            photo_notice="Foto removida.",
            _photo_files=dict(READY_FILES),
        )

        async def load() -> list[object]:
            events = []
            async for event in DonationCreateState.load_initial_data.fn(state):
                events.append(event)
            return events

        with (
            patch.dict(
                "os.environ",
                {
                    "XANO_API_URL": "https://xano.example/api:catalog",
                    "XANO_AUTH_API_URL": "https://xano.example/api:auth",
                },
            ),
            patch(
                "doafacil.cadastro_doacao.httpx.AsyncClient",
                return_value=client,
            ),
        ):
            events = asyncio.run(load())

        self.assertEqual(state.current_step, 1)
        self.assertEqual(state.title, "")
        self.assertEqual(state.description, "")
        self.assertEqual(state.category_id, "")
        self.assertEqual(state.category_name, "")
        self.assertEqual(state.condition, "")
        self.assertEqual(state.delivery_method, "")
        self.assertEqual(state.contact_preference, "")
        self.assertEqual(state.donation_error_message, "")
        self.assertEqual(state.upload_progress, "")
        # Reinício: as fotos guardadas no servidor e as miniaturas são apagadas.
        self.assertEqual(state.photos, [])
        self.assertEqual(state._photo_files, {})
        self.assertFalse(state.photos_busy)
        self.assertEqual(state.photo_notice, "")
        self.assertFalse(state.published)
        self.assertFalse(state.is_publishing)
        self.assertFalse(state.is_loading_data)
        self.assertFalse(state.data_load_failed)
        self.assertEqual(state.categories, [{"id": 3, "name": "Livros"}])
        self.assertEqual((state.city, state.state), ("Recife", "PE"))
        # Sem limpar o upload ao entrar (change navegacao-celular): o
        # clear_selected_files quebrava no navegador e não havia o que limpar.
        self.assertEqual(events, [])

        DonationCreateState.advance.fn(state)
        self.assertEqual(state.current_step, 1)
        self.assertIn("nome", state.donation_error_message)

        state.current_step = 3
        state.donation_error_message = ""
        DonationCreateState.advance.fn(state)
        self.assertEqual(state.current_step, 3)
        self.assertEqual(
            state.donation_error_message,
            "Adicione pelo menos uma foto para continuar.",
        )

    def test_profile_request_sends_auth_and_returns_city_and_state(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                request.headers["Authorization"],
                "Bearer test-token",
            )
            self.assertTrue(request.url.path.endswith("/auth/profile"))
            return httpx.Response(
                200,
                json={"city": "Recife", "state": "PE"},
            )

        async def fetch() -> tuple[str, str]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_profile(
                    client,
                    "https://xano.example/api:auth/auth/profile",
                    "test-token",
                )

        self.assertEqual(asyncio.run(fetch()), ("Recife", "PE"))

    def test_profile_request_distinguishes_expired_session(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, request=request)

        async def fetch() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await _fetch_profile(
                    client,
                    "https://xano.example/api:auth/auth/profile",
                    "expired-token",
                )

        with self.assertRaises(DonationSessionExpiredError):
            asyncio.run(fetch())

    def test_page_load_redirects_when_session_is_missing(self) -> None:
        state = SimpleNamespace(auth_token="")

        async def load() -> list[object]:
            events = []
            async for event in DonationCreateState.load_initial_data.fn(state):
                events.append(event)
            return events

        events = asyncio.run(load())

        self.assertEqual(len(events), 1)

    def test_publication_sends_multipart_images_and_requires_persisted_status(
        self,
    ) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                request.headers["Authorization"],
                "Bearer test-token",
            )
            self.assertIn("multipart/form-data", request.headers["content-type"])
            body = await request.aread()
            self.assertIn(b'filename="mesa.jpg"', body)
            self.assertIn(b'name="photos[]"', body)
            self.assertIn(b'name="category_id"', body)
            self.assertIn(b'name="delivery_method"', body)
            self.assertIn(b"A combinar", body)
            self.assertNotIn(b'name="owner_id"', body)
            self.assertNotIn(b'name="city"', body)
            self.assertNotIn(b'name="state"', body)
            return httpx.Response(
                200,
                json={"donation": {"id": 22, "status": "disponível"}},
                request=request,
            )

        async def publish() -> dict[str, object]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _publish_donation(
                    client,
                    "https://xano.example/api:catalog/catalog/donations/publish",
                    "test-token",
                    {
                        "category_id": 3,
                        "title": "Mesa",
                        "description": "Em bom estado",
                        "condition": "Bom",
                        "delivery_method": "A combinar",
                        "contact_preference": "E-mail",
                    },
                    [("mesa.jpg", b"image-bytes", "image/jpeg")],
                )

        self.assertEqual(
            asyncio.run(publish()),
            {"id": 22, "status": "disponível"},
        )

    def test_publication_rejects_missing_photos_response(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertIn(
                "multipart/form-data",
                request.headers["content-type"],
            )
            body = await request.aread()
            self.assertIn(b'name="category_id"', body)
            self.assertIn(b'name="title"', body)
            self.assertNotIn(b'name="photos[]"', body)
            return httpx.Response(
                400,
                json={
                    "error": {
                        "details": [
                            {
                                "reason": (
                                    "Adicione pelo menos uma foto para "
                                    "continuar."
                                )
                            }
                        ]
                    }
                },
                request=request,
            )

        async def publish() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await _publish_donation(
                    client,
                    "https://xano.example/api:catalog/catalog/donations/publish",
                    "test-token",
                    {
                        "category_id": 3,
                        "title": "Mesa",
                        "description": "Em bom estado",
                        "condition": "Bom",
                        "delivery_method": "A combinar",
                        "contact_preference": "Chat do DoaFácil",
                    },
                    [],
                )

        with self.assertRaises(DonationMissingPhotosError):
            asyncio.run(publish())

    def test_missing_photos_response_keeps_form_and_shows_specific_message(
        self,
    ) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                400,
                json={
                    "details": [
                        {
                            "arbitrary_text_field": (
                                "Adicione pelo menos uma foto para continuar."
                            )
                        }
                    ]
                },
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        state = _publish_state()

        async def publish() -> list[object]:
            events = []
            async for event in DonationCreateState.publish.fn(state):
                events.append(event)
            return events

        with (
            patch.dict(
                "os.environ",
                {"XANO_API_URL": "https://xano.example/api:catalog"},
            ),
            patch(
                "doafacil.cadastro_doacao.httpx.AsyncClient",
                return_value=client,
            ),
        ):
            asyncio.run(publish())

        self.assertEqual(state.current_step, 5)
        self.assertEqual(state.title, "Mesa")
        self.assertEqual(state.description, "Em bom estado")
        self.assertEqual(state.category_id, "3")
        self.assertEqual(state.condition, "Bom")
        self.assertEqual(state.delivery_method, "A combinar")
        self.assertEqual(state.contact_preference, "E-mail")
        self.assertEqual(state.city, "Recife")
        self.assertEqual(state.state, "PE")
        self.assertEqual(
            state.donation_error_message,
            "Adicione pelo menos uma foto para continuar.",
        )
        self.assertFalse(state.published)
        self.assertFalse(state.is_publishing)
        self.assertEqual(state.upload_progress, "")
        # As fotos e a ordem ficam para uma nova tentativa.
        self.assertEqual(state.photos, READY_PHOTOS)
        self.assertEqual(state._photo_files, READY_FILES)

    def test_publication_rejects_success_response_without_valid_donation(
        self,
    ) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"donation": {"id": 22, "status": "reservada"}},
                request=request,
            )

        async def publish() -> None:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                await _publish_donation(
                    client,
                    "https://xano.example/api:catalog/catalog/donations/publish",
                    "test-token",
                    {"category_id": 3},
                    [],
                )

        with self.assertRaises(DonationServiceError):
            asyncio.run(publish())

    def test_failed_state_publication_keeps_form_values_and_shows_no_success(
        self,
    ) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, request=request)

        client = httpx.AsyncClient(
            transport=httpx.MockTransport(respond)
        )
        state = _publish_state()

        async def publish() -> list[object]:
            events = []
            async for event in DonationCreateState.publish.fn(state):
                events.append(event)
            return events

        with (
            patch.dict(
                "os.environ",
                {"XANO_API_URL": "https://xano.example/api:catalog"},
            ),
            patch(
                "doafacil.cadastro_doacao.httpx.AsyncClient",
                return_value=client,
            ),
        ):
            asyncio.run(publish())

        self.assertEqual(state.title, "Mesa")
        self.assertEqual(state.description, "Em bom estado")
        self.assertEqual(state.category_id, "3")
        self.assertFalse(state.published)
        self.assertIn("mantidos", state.donation_error_message)
        self.assertEqual(state.photos, READY_PHOTOS)
        self.assertEqual(state._photo_files, READY_FILES)

    def test_publish_without_photos_or_with_missing_file_does_not_send(self) -> None:
        async def publish(state) -> list[object]:
            return [event async for event in DonationCreateState.publish.fn(state)]

        with patch("doafacil.cadastro_doacao.httpx.AsyncClient") as client:
            empty = _publish_state(photos=[], _photo_files={})
            asyncio.run(publish(empty))
            self.assertEqual(empty.donation_error_message, "Adicione pelo menos uma foto para continuar.")
            missing = _publish_state(_photo_files={"a": READY_FILES["a"]})
            asyncio.run(publish(missing))
            self.assertIn("uma das imagens", missing.donation_error_message)
        client.assert_not_called()
        self.assertFalse(empty.published or missing.published)

    def test_successful_publication_sends_in_order_clears_photos_and_goes_to_detail(self) -> None:
        bodies: list[bytes] = []

        async def respond(request: httpx.Request) -> httpx.Response:
            bodies.append(await request.aread())
            return httpx.Response(
                200,
                json={"donation": {"id": 12, "status": "disponível"}},
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        state = _publish_state()

        async def publish() -> list[object]:
            return [event async for event in DonationCreateState.publish.fn(state)]

        with (
            patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api:catalog"}),
            patch("doafacil.cadastro_doacao.httpx.AsyncClient", return_value=client),
            patch("doafacil.cadastro_doacao.rx.redirect", side_effect=lambda path: f"redirect:{path}"),
        ):
            events = asyncio.run(publish())

        body = bodies[0]
        # A ordem da tela (b, depois a) é a ordem das partes photos[], com os
        # nomes foto-1.<ext> e foto-2.<ext> e os bytes preparados.
        first = body.index(b'filename="foto-1.png"')
        second = body.index(b'filename="foto-2.jpg"')
        self.assertLess(first, second)
        self.assertLess(body.index(b"bytes-b"), body.index(b"bytes-a"))
        self.assertEqual(body.count(b'name="photos[]"'), 2)
        # Publicada: as fotos guardadas são apagadas e a página vai ao detalhe
        # com o aviso.
        self.assertTrue(state.published)
        self.assertFalse(state.is_publishing)
        self.assertEqual((state.photos, state._photo_files), ([], {}))
        self.assertEqual(events[-1], "redirect:/doacao/12")
        self.assertIn("set_published_notice", repr(events[-2]))
        self.assertIn("12", repr(events[-2]))

        # Um segundo clique não publica de novo.
        with patch("doafacil.cadastro_doacao.httpx.AsyncClient") as again:
            asyncio.run(publish())
        again.assert_not_called()

    def test_form_page_is_registered_with_animation_and_five_step_indicator(
        self,
    ) -> None:
        self.assertIn("cadastro-doacao", app._unevaluated_pages)
        self.assertEqual(
            app._unevaluated_pages["cadastro-doacao"].route,
            "cadastro-doacao",
        )
        page = donation_creation_page()
        self.assertIn(
            "Passo ",
            [str(value) for value in _component_text(page)],
        )
        self.assertIn("auth-card-enter", str(page))

    def test_back_link_in_the_header_line_like_other_pages(self) -> None:
        # Change navegacao-celular: a seta fica na linha do logotipo, à
        # esquerda, no mesmo cabeçalho das outras páginas, sem “Quero Doar”.
        from doafacil.navegacao import back_link_header

        page = donation_creation_page()
        header = page.children[0]
        self.assertEqual(
            str(header),
            str(back_link_header("/", "Voltar ao início", "#166B3B", show_donate=False)),
        )
        back = header.children[0].children[0]
        self.assertEqual(back.custom_attrs["aria-label"], "Voltar ao início")
        self.assertIn('to:"/"', str(back))
        # Sem a faixa solta abaixo do cabeçalho.
        self.assertEqual(str(page).count('"aria-label":"Voltar ao in\\u00edcio"'), 1)

    def test_email_visibility_notice_is_conditional_on_preference(self) -> None:
        step = _step_five()
        notice = (
            "Seu e-mail ficará disponível para pessoas logadas que "
            "quiserem falar com você."
        )
        content = _component_text(step)

        self.assertIn(notice, content)
        self.assertIn("contact_preference", str(step))
        self.assertIn("E-mail", str(step))
        rendered_step = str(step)
        for personal_field in ("Telefone", "WhatsApp", "Endereço"):
            with self.subTest(personal_field=personal_field):
                self.assertNotIn(personal_field, rendered_step)

    def test_placeholders_and_select_texts_use_dark_colors(self) -> None:
        step_components = (
            _step_one(),
            _step_two(),
            _step_four(),
            _step_five(),
        )
        nodes = [
            node
            for component in step_components
            for node in _component_nodes(component)
        ]
        fields = {
            _literal(node.id): node
            for node in nodes
            if type(node).__name__ == "DebounceInput"
        }
        self.assertEqual(
            set(fields),
            {"donation-title", "donation-description"},
        )
        expected_placeholders = {
            "donation-title": "Ex.: Carrinho de brinquedo",
            "donation-description": "Conte detalhes importantes sobre o objeto.",
        }
        for field_id, field in fields.items():
            with self.subTest(field_id=field_id):
                self.assertEqual(
                    _literal(field.custom_attrs["placeholder"]),
                    expected_placeholders[field_id],
                )
                self.assertEqual(
                    _literal(field.style["color"]),
                    "#333333",
                )
                # Placeholder e texto digitado vêm das regras globais dos
                # campos (texto #1F1F1F e exemplo #6B6B6B, opacos).
                self.assertNotIn(f"#{field_id}::placeholder", app.style)

        self.assertEqual(
            app.style[FIELD_PLACEHOLDER_SELECTOR],
            {
                "color": "#6B6B6B !important",
                "WebkitTextFillColor": "#6B6B6B !important",
                "opacity": "1 !important",
            },
        )
        self.assertEqual(
            app.style[FIELD_TEXT_SELECTOR],
            {
                "color": "#1F1F1F !important",
                "WebkitTextFillColor": "#1F1F1F !important",
                "opacity": "1 !important",
            },
        )
        self.assertNotIn("#donation-title, #donation-description", app.style)

        select_triggers = {
            _literal(node.id): node
            for node in nodes
            if type(node).__name__ == "SelectTrigger"
        }
        expected_prompts = {
            "donation-category": "Selecione uma categoria",
            "donation-condition": "Selecione a condição",
            "donation-delivery-method": "Selecione uma forma de entrega",
            "donation-contact-preference": "Selecione uma forma de contato",
        }
        self.assertEqual(set(select_triggers), set(expected_prompts))
        for field_id, placeholder in expected_prompts.items():
            with self.subTest(field_id=field_id):
                self.assertEqual(
                    _literal(select_triggers[field_id].placeholder),
                    placeholder,
                )
                self.assertEqual(
                    app.style[
                        "#donation-category, "
                        "#donation-condition, "
                        "#donation-delivery-method, "
                        "#donation-contact-preference"
                    ]["color"],
                    "#333333",
                )

        placeholder_selector = (
            "#donation-category[data-placeholder] .rt-SelectTriggerInner, "
            "#donation-condition[data-placeholder] .rt-SelectTriggerInner, "
            "#donation-delivery-method[data-placeholder] "
            ".rt-SelectTriggerInner, "
            "#donation-contact-preference[data-placeholder] "
            ".rt-SelectTriggerInner"
        )
        self.assertEqual(
            app.style[placeholder_selector],
            {"color": "#333333"},
        )
        self.assertNotIn("background", app.style[placeholder_selector])
        self.assertNotIn("rt-SelectItem", placeholder_selector)

        select_roots = [
            node for node in nodes if type(node).__name__ == "SelectRoot"
        ]
        select_contents = [
            node for node in nodes if type(node).__name__ == "SelectContent"
        ]
        self.assertEqual(len(select_roots), 4)
        # Change fotos-formulario-doacao: o estilo fica no botão visível
        # (Trigger), com fundo branco, borda #C8C8C8, texto #1F1F1F e foco
        # verde, nos quatro selects; antes, no Root, o botão ficava cinza.
        for field_id, trigger in select_triggers.items():
            with self.subTest(trigger=field_id):
                rendered_trigger = str(trigger)
                self.assertIn('["background"] : "#FFFFFF"', rendered_trigger)
                self.assertIn('["border"] : "1px solid #C8C8C8"', rendered_trigger)
                self.assertIn('["color"] : "#1F1F1F"', rendered_trigger)
                self.assertIn("2px solid #007A42", rendered_trigger)
        self.assertEqual(len(select_contents), 4)
        self.assertTrue(
            all(_literal(node.high_contrast) is True for node in select_contents)
        )
        self.assertEqual(DELIVERY_METHODS, ("A combinar",))
        self.assertEqual(
            CONTACT_PREFERENCES,
            ("E-mail", "Chat do DoaFácil"),
        )


def _component_text(component: object) -> list[object]:
    contents: list[object] = []

    def collect(value: object) -> None:
        text = getattr(value, "contents", None)
        if text is not None:
            contents.append(getattr(text, "_var_value", text))
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
        if hasattr(value, "children"):
            nodes.append(value)
            collect(value.children)
        elif isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return nodes


def _literal(value: object) -> object:
    return getattr(value, "_var_value", value)


class WizardFocusTests(unittest.TestCase):
    """Foco verde dos botões do wizard (change fotos-formulario-doacao, decisão 5c)."""

    def test_back_continue_and_publish_have_green_focus(self) -> None:
        from doafacil.cadastro_doacao import WIZARD_FOCUS, _wizard_content

        rendered = str(_wizard_content())
        self.assertEqual(WIZARD_FOCUS["outline"], "2px solid #007A42")
        for label in ('"Voltar"', '"Continuar"', '"Publicar doa\\u00e7\\u00e3o"'):
            with self.subTest(button=label):
                self.assertIn(label, rendered)
        # Os três botões do wizard com o anel verde, sem o azul do tema.
        self.assertGreaterEqual(rendered.count('["&:focus-visible"] : ({ ["outline"] : "2px solid #007A42", ["outlineOffset"] : "2px", ["boxShadow"] : "none" })'), 3)


if __name__ == "__main__":
    unittest.main()
