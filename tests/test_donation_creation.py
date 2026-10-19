import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from doafacil.cadastro_doacao import (
    IMAGE_TYPES,
    DonationCreateState,
    DonationServiceError,
    DonationSessionExpiredError,
    _fetch_categories,
    _fetch_profile,
    _parse_categories,
    _publish_donation,
    _validate_step,
    _validated_photos,
    donation_creation_page,
)
from doafacil.doafacil import app


class DonationCreationTests(unittest.TestCase):
    def test_category_payload_requires_valid_category_ids_and_names(self) -> None:
        self.assertEqual(
            _parse_categories(
                [{"id": 3, "name": "Móveis"}, {"id": 4, "name": "Livros"}]
            ),
            [
                {"id": 3, "name": "Móveis"},
                {"id": 4, "name": "Livros"},
            ],
        )
        self.assertEqual(_parse_categories([]), [])
        with self.assertRaises(DonationServiceError):
            _parse_categories([{"id": "3", "name": "Móveis"}])

    def test_step_validation_requires_fields_at_their_step(self) -> None:
        categories = {3}
        args = (
            "Mesa",
            "Em bom estado",
            "3",
            "Bom",
            "Retirada",
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
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("/catalog/categories"))
            return httpx.Response(
                200,
                json=[{"id": 9, "name": "Brinquedos"}],
            )

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
            [{"id": 9, "name": "Brinquedos"}],
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
                        "delivery_method": "Retirada",
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
                        "delivery_method": "Retirada",
                        "contact_preference": "E-mail",
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
            delivery_method="Retirada",
            contact_preference="E-mail",
            categories=[{"id": 3, "name": "Móveis"}],
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
            delivery_method="Retirada",
            contact_preference="E-mail",
            categories=[{"id": 3, "name": "Móveis"}],
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


if __name__ == "__main__":
    unittest.main()
