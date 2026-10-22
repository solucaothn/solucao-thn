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
    _validated_photos,
    donation_creation_page,
    _wizard_content,
)
from doafacil.doafacil import app


class DonationCreationTests(unittest.TestCase):
    def test_category_payload_requires_valid_category_ids_and_names(self) -> None:
        payload = [
            {"id": 3, "name": "Móveis"},
            {"id": 4, "name": "Livros"},
            {"id": 5, "name": "Alimentos"},
            {"id": 6, "name": "Brinquedos"},
        ]
        original_payload = [item.copy() for item in payload]
        self.assertEqual(
            _parse_categories(payload),
            [
                {"id": 4, "name": "Livros"},
                {"id": 6, "name": "Brinquedos"},
            ],
        )
        self.assertEqual(payload, original_payload)
        self.assertEqual(_parse_categories([]), [])
        self.assertEqual(
            _parse_categories(
                [
                    {"id": 7, "name": "Alimentos"},
                    {"id": 8, "name": "Móveis"},
                ]
            ),
            [],
        )
        with self.assertRaises(DonationServiceError):
            _parse_categories([{"id": "3", "name": "Móveis"}])

    def test_hidden_categories_are_not_valid_options(self) -> None:
        categories = _parse_categories(
            [
                {"id": 3, "name": "Alimentos"},
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
        DonationCreateState.advance.fn(state, [])
        self.assertEqual(state.current_step, 1)
        self.assertIn("nome", state.donation_error_message)

        state.title = "Mesa"
        state.donation_error_message = ""
        DonationCreateState.advance.fn(state, [])
        self.assertEqual(state.current_step, 2)
        self.assertEqual(state.title, "Mesa")
        DonationCreateState.go_back.fn(state)
        self.assertEqual(state.current_step, 1)
        self.assertEqual(state.title, "Mesa")

    def test_photo_step_requires_at_least_one_selected_file(self) -> None:
        state = SimpleNamespace(
            is_loading_data=False,
            is_publishing=False,
            published=False,
            current_step=3,
            donation_error_message="",
        )

        DonationCreateState.advance.fn(state, [])

        self.assertEqual(state.current_step, 3)
        self.assertEqual(
            state.donation_error_message,
            "Adicione pelo menos uma foto para continuar.",
        )

        selected_photo = SimpleNamespace(
            name="brinquedo.jpg",
            content_type="image/jpeg",
        )
        DonationCreateState.advance.fn(state, [selected_photo])

        self.assertEqual(state.current_step, 4)
        self.assertEqual(state.donation_error_message, "")

        continue_button = next(
            node
            for node in _component_nodes(_wizard_content())
            if type(node).__name__ == "Button"
            and _component_text(node.children) == ["Continuar"]
        )
        continue_event = continue_button.event_triggers["on_click"].events[0]
        self.assertEqual(continue_event.client_handler_name, "uploadFiles")
        self.assertIn(PHOTO_UPLOAD_ID, str(continue_event.args))

    def test_upload_validation_accepts_images_and_rejects_invalid_files(self) -> None:
        image = SimpleNamespace(
            name="mesa.webp",
            content_type="image/webp",
        )
        self.assertEqual(
            _validated_photos([image]),
            [("mesa.webp", b"", IMAGE_TYPES[".webp"])],
        )
        for invalid in (
            SimpleNamespace(name="documento.pdf", content_type="application/pdf"),
            SimpleNamespace(name="mesa.jpg", content_type="image/png"),
        ):
            with self.subTest(filename=invalid.name):
                with self.assertRaises(DonationServiceError):
                    _validated_photos([invalid])
        with self.assertRaises(DonationServiceError):
            _validated_photos(
                [
                    SimpleNamespace(name=f"{index}.jpg", content_type="image/jpeg")
                    for index in range(6)
                ]
            )

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

        self.assertEqual(
            asyncio.run(fetch()),
            [{"id": 3, "name": "Livros"}],
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

    def test_category_load_failure_is_reported_without_clearing_form(self) -> None:
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
        self.assertEqual(state.title, "Mesa")
        self.assertFalse(state.is_loading_data)

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

    def test_publication_sends_multipart_without_photos(self) -> None:
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
                200,
                json={"donation": {"id": 23, "status": "disponível"}},
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
                        "contact_preference": "Chat do DoaFácil",
                    },
                    [],
                )

        self.assertEqual(
            asyncio.run(publish()),
            {"id": 23, "status": "disponível"},
        )

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
        state = SimpleNamespace(
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
            success_message="",
            upload_progress="",
        )

        async def publish() -> list[object]:
            events = []
            async for event in DonationCreateState.publish.fn(state, []):
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
        self.assertEqual(state.success_message, "")
        self.assertIn("mantidos", state.donation_error_message)

    def test_upload_read_failure_keeps_form_available_for_retry(self) -> None:
        class UnreadablePhoto:
            name = "mesa.jpg"
            content_type = "image/jpeg"

            async def read(self) -> bytes:
                raise OSError("file read failed")

        state = SimpleNamespace(
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
            success_message="",
            upload_progress="",
        )

        async def publish(files: list[object]) -> list[object]:
            events = []
            async for event in DonationCreateState.publish.fn(state, files):
                events.append(event)
            return events

        asyncio.run(publish([UnreadablePhoto()]))

        self.assertFalse(state.published)
        self.assertFalse(state.is_publishing)
        self.assertEqual(state.title, "Mesa")
        self.assertEqual(state.upload_progress, "")
        self.assertEqual(state.success_message, "")
        self.assertIn("uma das imagens", state.donation_error_message)

        async def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "donation": {
                        "id": 12,
                        "status": "disponível",
                    }
                },
                request=request,
            )

        client = httpx.AsyncClient(
            transport=httpx.MockTransport(respond)
        )
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
            asyncio.run(publish([]))

        self.assertTrue(state.published)
        self.assertIn("publicada", state.success_message)

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
                self.assertEqual(
                    app.style[f"#{field_id}::placeholder"],
                    {"color": "#333333", "opacity": "1"},
                )

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
        self.assertTrue(all(node.color == "#333333" for node in select_roots))
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


if __name__ == "__main__":
    unittest.main()
