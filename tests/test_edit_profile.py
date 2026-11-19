import asyncio
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from PIL import Image

from doafacil.login import LoginState
from doafacil.navegacao import back_link_header
from doafacil.doafacil import app
from doafacil.editar_perfil import (
    ABOUT_HINT,
    CROP_DIALOG_WIDTH,
    CROP_HELP,
    CROP_TITLE,
    EMAIL_HELP,
    LOAD_ERROR_MESSAGE,
    NAME_HELP,
    PHOTO_ERROR_MESSAGE,
    PHOTO_FORMAT_MESSAGE,
    PHOTO_FORMATS_TEXT,
    PHOTO_MAX_BYTES,
    PHOTO_MISSING_MESSAGE,
    PHOTO_PUBLIC_NOTICE,
    PHOTO_REMOVED_MESSAGE,
    PHOTO_SAVED_MESSAGE,
    PHOTO_SIZE_MESSAGE,
    PHOTO_UPLOAD_ID,
    RATE_LIMIT_MESSAGE,
    SAVE_ERROR_MESSAGE,
    SAVE_REJECTED_MESSAGE,
    VISIBILITY_TEXT,
    VISIBILITY_TITLE,
    EditProfileState,
    ProfilePhotoRejectedError,
    ProfileRateLimitError,
    ProfileRejectedError,
    ProfileServiceError,
    ProfileUnauthorizedError,
    _crop_dialog,
    _form,
    _parse_profile,
    _parse_profile_credibility,
    _photo_section,
    _preview,
    edit_profile_page,
    fetch_profile,
    first_name_of,
    rejection_message,
    remove_profile_photo,
    update_profile,
    upload_profile_photo,
    validate_photo_file,
    validate_profile,
)
from doafacil.minhas_doacoes import SAVED_MESSAGE, MyDonationsState
from doafacil.perfil_publico import about_text, parse_about


AUTH_URL = "https://xano.example/api:auth"
TOKEN = "token-de-teste"
PROFILE_PAYLOAD = {
    "id": 9,
    "created_at": 1_600_000_000_000,
    "name": "Ana Beatriz Lima",
    "email": "ana@example.test",
    "city": "Campinas",
    "state": "SP",
    "about": "Gosto de doar.\nAté breve.",
}
# Só o GET traz o selo e os contadores (change perfil-credibilidade).
GET_PAYLOAD = {**PROFILE_PAYLOAD, "email_verified": True, "counts": {"active": 2, "completed": 5}}
PHOTO_URL = "https://xano.example/vault/abc/foto.png"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 64  # cabeçalho de PNG, conteúdo ilegível


def _quadrants_png() -> bytes:
    """PNG 400x300 de verdade, com quatro quadrantes (o sup. dir. é verde)."""
    image = Image.new("RGB", (400, 300))
    for color, box in (
        ((220, 20, 20), (0, 0, 200, 150)),
        ((20, 160, 60), (200, 0, 400, 150)),
        ((20, 40, 220), (0, 150, 200, 300)),
        ((240, 220, 20), (200, 150, 400, 300)),
    ):
        image.paste(color, box)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


QUADRANTS_PNG = _quadrants_png()


class _FakeUpload:
    """Arquivo como o Reflex entrega ao evento de upload."""

    def __init__(self, name: str, content_type: str, contents: bytes) -> None:
        self.name = name
        self.content_type = content_type
        self._contents = contents

    async def read(self) -> bytes:
        return self._contents


def _call(handler, function, *args):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await function(client, TOKEN, *args)

    with patch.dict("os.environ", {"XANO_AUTH_API_URL": AUTH_URL}):
        return asyncio.run(run())


def _loaded(**changes) -> dict:
    """O que o fetch_profile devolve para um GET com estas mudanças."""
    payload = {**GET_PAYLOAD, **changes}
    return {**_parse_profile(payload), **_parse_profile_credibility(payload)}


def _events(generator) -> list:
    async def run():
        return [event async for event in generator]

    return asyncio.run(run())


def _state(**fields) -> SimpleNamespace:
    base = dict(
        auth_token=TOKEN,
        account_name="Ana",
        view_state="loading",
        load_error="",
        name="",
        email="",
        city="",
        uf="",
        about="",
        photo="",
        photo_busy=False,
        photo_notice="",
        photo_error="",
        form_error="",
        is_saving=False,
        crop_open=False,
        crop_preview="",
        crop_area={},
        _crop_source=b"",
        _crop_preview_size=(0, 0),
    )
    base.update(fields)
    return SimpleNamespace(**base)


def _ready_state(**fields) -> SimpleNamespace:
    ready = dict(
        view_state="ready",
        name="Ana Beatriz Lima",
        email="ana@example.test",
        city="Campinas",
        uf="SP",
        about="Gosto de doar.",
    )
    ready.update(fields)
    return _state(**ready)


def _computed(name: str, state: SimpleNamespace):
    return EditProfileState.computed_vars[name].fget(state)


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


def _luminance(color: str) -> float:
    channels = [int(color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground: str, background: str) -> float:
    a, b = _luminance(foreground), _luminance(background)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


class AboutHelperTests(unittest.TestCase):
    def test_parse_about(self) -> None:
        self.assertEqual(parse_about(None), "")
        self.assertEqual(parse_about("  Oi.\nTchau.  "), "Oi.\nTchau.")
        with self.assertRaises(ValueError):
            parse_about(3)

    def test_about_text_is_plain_text_with_line_breaks(self) -> None:
        rendered = str(about_text(EditProfileState.preview_about))
        self.assertIn('["whiteSpace"] : "pre-wrap"', rendered)
        self.assertIn("(jsx(Fragment,{},))", rendered)
        self.assertNotIn("dangerouslySetInnerHTML", rendered)


class EditProfileClientTests(unittest.TestCase):
    def test_fetch_profile_sends_token(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/api:auth/auth/profile")
            self.assertEqual(request.headers.get("Authorization"), f"Bearer {TOKEN}")
            return httpx.Response(200, json=GET_PAYLOAD)

        profile = _call(handler, fetch_profile)
        self.assertEqual(profile["name"], "Ana Beatriz Lima")
        self.assertEqual(profile["state"], "SP")
        self.assertEqual(profile["about"], "Gosto de doar.\nAté breve.")
        self.assertIs(profile["email_verified"], True)
        self.assertEqual((profile["active"], profile["completed"]), (2, 5))

    def test_get_requires_badge_and_counters(self) -> None:
        for label, payload in {
            "sem selo": PROFILE_PAYLOAD,
            "selo nulo": {**GET_PAYLOAD, "email_verified": None},
            "selo texto": {**GET_PAYLOAD, "email_verified": "false"},
            "sem contadores": {k: v for k, v in GET_PAYLOAD.items() if k != "counts"},
            "contador negativo": {**GET_PAYLOAD, "counts": {"active": -1, "completed": 0}},
            "contador decimal": {**GET_PAYLOAD, "counts": {"active": 1, "completed": 0.5}},
            "contador booleano": {**GET_PAYLOAD, "counts": {"active": False, "completed": 0}},
        }.items():
            with self.subTest(case=label):
                with self.assertRaises(ProfileServiceError):
                    _call(lambda r, body=payload: httpx.Response(200, json=body), fetch_profile)
        # Selo falso é válido.
        profile = _call(
            lambda r: httpx.Response(200, json={**GET_PAYLOAD, "email_verified": False}), fetch_profile
        )
        self.assertIs(profile["email_verified"], False)

    def test_patch_response_does_not_need_badge_or_counters(self) -> None:
        fields = {"name": "Ana Lima", "city": "Santos", "state": "SP", "about": ""}
        profile = _call(lambda r: httpx.Response(200, json=PROFILE_PAYLOAD), update_profile, fields)
        self.assertNotIn("email_verified", profile)
        self.assertNotIn("active", profile)

    def test_null_about_becomes_empty_and_extra_fields_are_ignored(self) -> None:
        profile = _parse_profile({**PROFILE_PAYLOAD, "about": None, "role": "admin", "password": "x"})
        self.assertEqual(profile["about"], "")
        self.assertEqual(set(profile), {"name", "email", "city", "state", "about", "photo"})
        profile = _parse_profile({k: v for k, v in PROFILE_PAYLOAD.items() if k != "about"})
        self.assertEqual(profile["about"], "")
        # A resposta do PATCH não traz a foto: ausente ou nula → "".
        self.assertEqual(profile["photo"], "")
        self.assertEqual(_parse_profile({**PROFILE_PAYLOAD, "photo": None})["photo"], "")
        self.assertEqual(
            _parse_profile({**PROFILE_PAYLOAD, "photo": PHOTO_URL})["photo"], PHOTO_URL
        )

    def test_invalid_responses(self) -> None:
        for label, payload in {
            "lista": [],
            "nome nulo": {**PROFILE_PAYLOAD, "name": None},
            "cidade número": {**PROFILE_PAYLOAD, "city": 1},
            "about número": {**PROFILE_PAYLOAD, "about": 2},
            "foto número": {**PROFILE_PAYLOAD, "photo": 3},
            "foto sem http": {**PROFILE_PAYLOAD, "photo": "javascript:alert(1)"},
        }.items():
            with self.subTest(case=label):
                with self.assertRaises(ProfileServiceError):
                    _parse_profile(payload)
        with self.assertRaises(ProfileServiceError):
            _call(lambda r: httpx.Response(200, text="<html>"), fetch_profile)

    def test_status_codes(self) -> None:
        cases = {
            401: ProfileUnauthorizedError,
            400: ProfileRejectedError,
            429: ProfileRateLimitError,
            500: ProfileServiceError,
        }
        for status, error in cases.items():
            with self.subTest(status=status):
                with self.assertRaises(error):
                    _call(lambda r, s=status: httpx.Response(s, json={}), fetch_profile)

    def test_update_profile_sends_patch_with_whole_form(self) -> None:
        fields = {"name": "Ana Lima", "city": "Santos", "state": "SP", "about": ""}

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "PATCH")
            self.assertEqual(request.url.path, "/api:auth/auth/profile")
            self.assertEqual(request.headers.get("Authorization"), f"Bearer {TOKEN}")
            body = request.read().decode("utf-8")
            for key in ("name", "city", "state", "about"):
                self.assertIn(f'"{key}"', body)
            return httpx.Response(200, json={**PROFILE_PAYLOAD, "name": "Ana Lima", "about": ""})

        profile = _call(handler, update_profile, fields)
        self.assertEqual(profile["name"], "Ana Lima")

    def test_missing_auth_url_is_service_error(self) -> None:
        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200))) as client:
                await fetch_profile(client, TOKEN)

        with patch.dict("os.environ", {"XANO_AUTH_API_URL": ""}):
            with self.assertRaises(ProfileServiceError):
                asyncio.run(run())


class EditProfileValidationTests(unittest.TestCase):
    def test_validation_messages(self) -> None:
        self.assertEqual(validate_profile("Ana", "Campinas", "SP", ""), "")
        self.assertEqual(validate_profile("  ", "Campinas", "SP", ""), "Informe seu nome.")
        self.assertEqual(validate_profile("Ana", " ", "SP", ""), "Informe sua cidade.")
        self.assertEqual(validate_profile("Ana", "Campinas", "XX", ""), "Selecione seu estado.")
        self.assertEqual(validate_profile("Ana", "Campinas", "", ""), "Selecione seu estado.")
        self.assertIn("300", validate_profile("Ana", "Campinas", "SP", "a" * 301))
        self.assertEqual(validate_profile("Ana", "Campinas", "SP", "á" * 300), "")

    def test_first_name_of(self) -> None:
        self.assertEqual(first_name_of("  Ana Beatriz Lima "), "Ana")
        self.assertEqual(first_name_of("   "), "")


class EditProfileStateTests(unittest.TestCase):
    def test_without_token_redirects_without_request(self) -> None:
        state = _state(auth_token="")
        with (
            patch("doafacil.editar_perfil.rx.redirect", return_value="login") as redirect,
            patch("doafacil.editar_perfil.fetch_profile", new_callable=AsyncMock) as fetch,
        ):
            events = _events(EditProfileState.load_profile.fn(state))
        self.assertEqual(events, ["login"])
        redirect.assert_called_once_with("/login")
        fetch.assert_not_called()

    def test_load_fills_form(self) -> None:
        state = _state()
        with patch(
            "doafacil.editar_perfil.fetch_profile",
            new_callable=AsyncMock,
            return_value=_loaded(),
        ):
            _events(EditProfileState.load_profile.fn(state))
        self.assertEqual(state.view_state, "ready")
        self.assertEqual((state.name, state.email, state.city, state.uf), ("Ana Beatriz Lima", "ana@example.test", "Campinas", "SP"))
        self.assertEqual(state.about, "Gosto de doar.\nAté breve.")
        self.assertIs(state.email_verified, True)
        self.assertEqual((state.active_count, state.completed_count), (2, 5))

    def test_state_outside_list_starts_empty(self) -> None:
        state = _state()
        with patch(
            "doafacil.editar_perfil.fetch_profile",
            new_callable=AsyncMock,
            return_value=_loaded(state="São Paulo"),
        ):
            _events(EditProfileState.load_profile.fn(state))
        self.assertEqual(state.uf, "")

    def test_load_errors(self) -> None:
        for error, message in (
            (ProfileRateLimitError(), RATE_LIMIT_MESSAGE),
            (ProfileServiceError(), LOAD_ERROR_MESSAGE),
            (httpx.ConnectError("x"), LOAD_ERROR_MESSAGE),
        ):
            with self.subTest(error=type(error).__name__):
                state = _state()
                with patch("doafacil.editar_perfil.fetch_profile", new_callable=AsyncMock, side_effect=error):
                    _events(EditProfileState.load_profile.fn(state))
                self.assertEqual(state.view_state, "error")
                self.assertEqual(state.load_error, message)

    def test_load_401_clears_session(self) -> None:
        state = _state()
        with (
            patch("doafacil.editar_perfil.rx.redirect", return_value="login"),
            patch("doafacil.editar_perfil.fetch_profile", new_callable=AsyncMock, side_effect=ProfileUnauthorizedError()),
        ):
            events = _events(EditProfileState.load_profile.fn(state))
        self.assertEqual(events, ["login"])
        self.assertEqual((state.auth_token, state.account_name), ("", ""))

    def test_preview_and_counter(self) -> None:
        state = _ready_state(name="  Beatriz Souza ", city="Santos", uf="SP", about="  Oi.\nTchau. ")
        self.assertEqual(_computed("preview_first_name", state), "Beatriz")
        self.assertEqual(_computed("preview_initial", state), "B")
        self.assertEqual(_computed("preview_location", state), "Santos, SP")
        self.assertEqual(_computed("preview_about", state), "Oi.\nTchau.")
        # O contador conta o texto do campo como está (igual ao max_length).
        self.assertEqual(_computed("about_count", state), "13/300")

    def test_about_input_is_limited_to_300(self) -> None:
        state = _ready_state()
        EditProfileState.set_about.fn(state, "a" * 350)
        self.assertEqual(len(state.about), 300)

    def test_validation_blocks_request_and_keeps_values(self) -> None:
        cases = {
            "nome": {"name": " "},
            "cidade": {"city": ""},
            "estado": {"uf": ""},
            "sobre": {"about": "a" * 301},
        }
        for label, change in cases.items():
            with self.subTest(case=label):
                state = _ready_state(**change)
                with patch("doafacil.editar_perfil.update_profile", new_callable=AsyncMock) as update:
                    _events(EditProfileState.save.fn(state))
                update.assert_not_called()
                self.assertTrue(state.form_error)
                for key, value in change.items():
                    self.assertEqual(getattr(state, key), value)

    def test_save_sends_whole_form_updates_header_and_returns_to_list(self) -> None:
        state = _ready_state(name="  Beatriz Souza  ", city=" Santos ", about="  ")
        returned = _parse_profile({**PROFILE_PAYLOAD, "name": "Beatriz Souza", "city": "Santos", "about": ""})
        with (
            patch("doafacil.editar_perfil.update_profile", new_callable=AsyncMock, return_value=returned) as update,
            patch("doafacil.editar_perfil.rx.redirect", return_value="lista") as redirect,
            patch.object(MyDonationsState, "set_flash", return_value="flash") as set_flash,
        ):
            events = _events(EditProfileState.save.fn(state))
        self.assertEqual(update.await_args.args[1], TOKEN)
        # Sempre o formulário inteiro, com o Sobre vazio (que apaga).
        self.assertEqual(
            update.await_args.args[2],
            {"name": "Beatriz Souza", "city": "Santos", "state": "SP", "about": ""},
        )
        self.assertEqual(state.account_name, "Beatriz")
        set_flash.assert_called_once_with(SAVED_MESSAGE)
        redirect.assert_called_once_with("/minhas-doacoes")
        self.assertEqual(events[-2:], ["flash", "lista"])
        self.assertFalse(state.is_saving)

    def test_save_errors_keep_values(self) -> None:
        for error, message in (
            (ProfileRejectedError(), SAVE_REJECTED_MESSAGE),
            (ProfileRateLimitError(), RATE_LIMIT_MESSAGE),
            (ProfileServiceError(), SAVE_ERROR_MESSAGE),
            (httpx.ReadTimeout("x"), SAVE_ERROR_MESSAGE),
        ):
            with self.subTest(error=type(error).__name__):
                state = _ready_state(city="Nova cidade")
                with patch("doafacil.editar_perfil.update_profile", new_callable=AsyncMock, side_effect=error):
                    _events(EditProfileState.save.fn(state))
                self.assertEqual(state.form_error, message)
                self.assertEqual(state.city, "Nova cidade")
                self.assertEqual(state.account_name, "Ana")
                self.assertFalse(state.is_saving)

    def test_save_401_redirects(self) -> None:
        state = _ready_state()
        with (
            patch("doafacil.editar_perfil.update_profile", new_callable=AsyncMock, side_effect=ProfileUnauthorizedError()),
            patch("doafacil.editar_perfil.rx.redirect", return_value="login"),
        ):
            events = _events(EditProfileState.save.fn(state))
        self.assertIn("login", events)
        self.assertEqual(state.auth_token, "")


class ProfilePhotoClientTests(unittest.TestCase):
    def test_upload_sends_multipart_with_token_and_returns_url(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, "/api:auth/auth/profile/photo")
            self.assertEqual(request.headers.get("Authorization"), f"Bearer {TOKEN}")
            self.assertTrue(request.headers["content-type"].startswith("multipart/form-data"))
            body = request.read()
            self.assertIn(b'name="photo"; filename="foto.png"', body)
            self.assertIn(b"Content-Type: image/png", body)
            self.assertIn(PNG_BYTES, body)
            return httpx.Response(200, json={"photo": PHOTO_URL})

        url = _call(handler, upload_profile_photo, "foto.png", PNG_BYTES, "image/png")
        self.assertEqual(url, PHOTO_URL)

    def test_upload_400_messages(self) -> None:
        for message, expected in (
            ("A foto pode ter no máximo 5 MB.", PHOTO_SIZE_MESSAGE),
            ("Envie uma imagem JPG, PNG, GIF ou WEBP.", PHOTO_FORMAT_MESSAGE),
            ("Missing param: photo", PHOTO_FORMAT_MESSAGE),
        ):
            with self.subTest(message=message):
                with self.assertRaises(ProfilePhotoRejectedError) as caught:
                    _call(
                        lambda r, m=message: httpx.Response(400, json={"message": m}),
                        upload_profile_photo,
                        "foto.png",
                        PNG_BYTES,
                        "image/png",
                    )
                self.assertEqual(caught.exception.message, expected)

    def test_upload_other_statuses_and_invalid_response(self) -> None:
        cases = {
            "401": (lambda r: httpx.Response(401, json={}), ProfileUnauthorizedError),
            "429": (lambda r: httpx.Response(429, json={}), ProfileRateLimitError),
            "500": (lambda r: httpx.Response(500, json={}), ProfileServiceError),
            "sem foto": (lambda r: httpx.Response(200, json={"photo": None}), ProfileServiceError),
            "não http": (lambda r: httpx.Response(200, json={"photo": "data:x"}), ProfileServiceError),
            "html": (lambda r: httpx.Response(200, text="<html>"), ProfileServiceError),
        }
        for label, (handler, error) in cases.items():
            with self.subTest(case=label):
                with self.assertRaises(error):
                    _call(handler, upload_profile_photo, "foto.png", PNG_BYTES, "image/png")

    def test_remove_sends_delete_with_token(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "DELETE")
            self.assertEqual(request.url.path, "/api:auth/auth/profile/photo")
            self.assertEqual(request.headers.get("Authorization"), f"Bearer {TOKEN}")
            return httpx.Response(200, json={"photo": None})

        self.assertIsNone(_call(handler, remove_profile_photo))
        for status, error in ((401, ProfileUnauthorizedError), (429, ProfileRateLimitError), (500, ProfileServiceError)):
            with self.subTest(status=status):
                with self.assertRaises(error):
                    _call(lambda r, s=status: httpx.Response(s, json={}), remove_profile_photo)


class ProfilePhotoValidationTests(unittest.TestCase):
    def test_validate_photo_file(self) -> None:
        self.assertEqual(validate_photo_file("foto.PNG", "image/png", PHOTO_MAX_BYTES), "")
        self.assertEqual(validate_photo_file("foto.jpeg", "image/jpeg", 10), "")
        self.assertEqual(validate_photo_file("foto.webp", "", 10), "")
        self.assertEqual(validate_photo_file("foto.png", "image/png", PHOTO_MAX_BYTES + 1), PHOTO_SIZE_MESSAGE)
        self.assertEqual(validate_photo_file("foto.pdf", "application/pdf", 10), PHOTO_FORMAT_MESSAGE)
        self.assertEqual(validate_photo_file("foto.png", "image/jpeg", 10), PHOTO_FORMAT_MESSAGE)
        self.assertEqual(validate_photo_file("foto", "image/png", 10), PHOTO_FORMAT_MESSAGE)
        self.assertEqual(validate_photo_file("foto.png", "image/png", 0), PHOTO_MISSING_MESSAGE)

    def test_rejection_message(self) -> None:
        too_large = [{"file": {}, "errors": [{"code": "file-too-large", "message": "x"}]}]
        wrong_type = [{"file": {}, "errors": [{"code": "file-invalid-type", "message": "x"}]}]
        self.assertEqual(rejection_message(too_large), PHOTO_SIZE_MESSAGE)
        self.assertEqual(rejection_message(wrong_type), PHOTO_FORMAT_MESSAGE)
        self.assertEqual(rejection_message([]), PHOTO_FORMAT_MESSAGE)
        self.assertEqual(rejection_message(None), PHOTO_FORMAT_MESSAGE)


class ProfilePhotoStateTests(unittest.TestCase):
    """Fluxo da foto com o modal “Ajustar foto” (change recorte-foto-perfil):
    escolher abre o modal sem requisição; “Usar foto” recorta e envia."""

    def _prepare(self, state, files):
        with patch("doafacil.editar_perfil.upload_profile_photo", new_callable=AsyncMock) as upload:
            # Sem eventos de limpar o upload (change navegacao-celular).
            result = asyncio.run(EditProfileState.prepare_crop.fn(state, files))
        return [] if result is None else [result], upload, None

    def _confirm(self, state, **patch_kwargs):
        with (
            patch("doafacil.editar_perfil.upload_profile_photo", new_callable=AsyncMock, **patch_kwargs) as upload,
            patch("doafacil.editar_perfil.rx.redirect", return_value="login"),
        ):
            events = _events(EditProfileState.confirm_crop.fn(state))
        return events, upload

    def _opened(self, area=None, **fields):
        """Estado com o modal aberto para o PNG de quadrantes (prévia 400x300)."""
        state = _ready_state(**fields)
        self._prepare(state, [_FakeUpload("minha foto.png", "image/png", QUADRANTS_PNG)])
        EditProfileState.set_crop_area.fn(
            state, area or {"x": 220, "y": 20, "width": 160, "height": 160}
        )
        return state

    def _upload(self, state, files, **patch_kwargs):
        """Escolher o arquivo e, se o modal abrir, acionar “Usar foto”."""
        events, upload, clear = self._prepare(state, files)
        if state.crop_open:
            EditProfileState.set_crop_area.fn(state, {"x": 0, "y": 0, "width": 300, "height": 300})
            more, upload = self._confirm(state, **patch_kwargs)
            events += more
        return events, upload, clear

    def test_choosing_a_valid_photo_opens_modal_without_request(self) -> None:
        state = _ready_state(city="Cidade digitada")
        events, upload, clear = self._prepare(state, [_FakeUpload("minha foto.png", "image/png", QUADRANTS_PNG)])
        upload.assert_not_called()
        self.assertTrue(state.crop_open)
        self.assertTrue(state.crop_preview.startswith("data:image/"))
        self.assertEqual(state._crop_source, QUADRANTS_PNG)
        self.assertEqual(state._crop_preview_size, (400, 300))
        self.assertEqual(state.crop_area, {})
        self.assertEqual(state.city, "Cidade digitada")
        self.assertIsNone(clear)  # sem rx.clear_selected_files (change navegacao-celular)

    def test_unreadable_image_shows_format_message_without_modal(self) -> None:
        state = _ready_state(photo=PHOTO_URL)
        _, upload, _ = self._prepare(state, [_FakeUpload("f.png", "image/png", PNG_BYTES)])
        upload.assert_not_called()
        self.assertFalse(state.crop_open)
        self.assertEqual(state.photo_error, PHOTO_FORMAT_MESSAGE)
        self.assertEqual(state.photo, PHOTO_URL)

    def test_cancel_clears_everything_without_request(self) -> None:
        for close in ("cancel", "esc"):
            with self.subTest(close=close):
                state = self._opened(photo=PHOTO_URL)
                with patch("doafacil.editar_perfil.upload_profile_photo", new_callable=AsyncMock) as upload:
                    if close == "cancel":
                        EditProfileState.cancel_crop.fn(state)
                    else:
                        EditProfileState.set_crop_open.fn(state, False)
                upload.assert_not_called()
                self.assertFalse(state.crop_open)
                self.assertEqual((state.crop_preview, state.crop_area), ("", {}))
                self.assertEqual(state._crop_source, b"")
                self.assertEqual(state.photo, PHOTO_URL)

    def test_use_photo_sends_square_of_framed_area_and_keeps_form(self) -> None:
        state = self._opened(city="Cidade digitada", about="Texto não salvo")
        _, upload = self._confirm(state, return_value=PHOTO_URL)
        args = upload.await_args.args
        self.assertEqual(args[1], TOKEN)
        self.assertEqual((args[2], args[4]), ("foto.png", "image/png"))
        sent = Image.open(BytesIO(args[3])).convert("RGB")
        self.assertEqual(sent.size, (512, 512))
        # A área (220, 20, 160x160) da prévia 400x300 cai no quadrante verde.
        self.assertTrue(all(abs(a - b) <= 40 for a, b in zip(sent.getpixel((256, 256)), (20, 160, 60))))
        self.assertEqual(state.photo, PHOTO_URL)
        self.assertEqual(state.account_photo, PHOTO_URL)  # o menu da conta já mostra a nova
        self.assertEqual(state.photo_notice, PHOTO_SAVED_MESSAGE)
        self.assertFalse(state.photo_busy)
        self.assertFalse(state.crop_open)
        self.assertEqual(state._crop_source, b"")
        self.assertEqual((state.city, state.about), ("Cidade digitada", "Texto não salvo"))

    def test_invalid_area_shows_error_without_request(self) -> None:
        state = self._opened(area={"x": 0, "y": 0, "width": 0, "height": 0}, photo=PHOTO_URL)
        _, upload = self._confirm(state)
        upload.assert_not_called()
        self.assertEqual(state.photo_error, PHOTO_ERROR_MESSAGE)
        self.assertEqual(state.photo, PHOTO_URL)
        self.assertFalse(state.crop_open)

    def test_use_photo_without_area_or_closed_modal_does_nothing(self) -> None:
        state = _ready_state()
        _, upload = self._confirm(state)
        upload.assert_not_called()
        self.assertEqual(state.photo_error, "")

    def test_set_crop_area_keeps_only_the_four_numbers(self) -> None:
        state = self._opened()
        EditProfileState.set_crop_area.fn(state, {"x": 1, "y": 2, "width": 3, "height": 4, "extra": 9})
        self.assertEqual(state.crop_area, {"x": 1, "y": 2, "width": 3, "height": 4})
        self.assertTrue(EditProfileState.computed_vars["crop_ready"].fget(state))
        closed = _ready_state()
        EditProfileState.set_crop_area.fn(closed, {"x": 1, "y": 2, "width": 3, "height": 4})
        self.assertEqual(closed.crop_area, {})

    def test_load_fills_photo(self) -> None:
        state = _state()
        with patch(
            "doafacil.editar_perfil.fetch_profile",
            new_callable=AsyncMock,
            return_value=_loaded(photo=PHOTO_URL),
        ):
            _events(EditProfileState.load_profile.fn(state))
        self.assertEqual(state.photo, PHOTO_URL)
        self.assertEqual(state.account_photo, PHOTO_URL)

    def test_invalid_file_is_refused_without_request(self) -> None:
        for label, files, message in (
            ("sem arquivo", [], PHOTO_MISSING_MESSAGE),
            ("formato", [_FakeUpload("doc.pdf", "application/pdf", b"x")], PHOTO_FORMAT_MESSAGE),
            ("tamanho", [_FakeUpload("g.png", "image/png", b"0" * (PHOTO_MAX_BYTES + 1))], PHOTO_SIZE_MESSAGE),
        ):
            with self.subTest(case=label):
                state = _ready_state(photo=PHOTO_URL)
                _, upload, _ = self._upload(state, files)
                upload.assert_not_called()
                self.assertEqual(state.photo_error, message)
                self.assertEqual(state.photo, PHOTO_URL)
                self.assertFalse(state.photo_busy)
                self.assertFalse(state.crop_open)

    def test_upload_errors_keep_current_photo(self) -> None:
        for error, message in (
            (ProfilePhotoRejectedError(PHOTO_SIZE_MESSAGE), PHOTO_SIZE_MESSAGE),
            (ProfilePhotoRejectedError(PHOTO_FORMAT_MESSAGE), PHOTO_FORMAT_MESSAGE),
            (ProfileRateLimitError(), RATE_LIMIT_MESSAGE),
            (ProfileServiceError(), PHOTO_ERROR_MESSAGE),
            (httpx.ConnectError("x"), PHOTO_ERROR_MESSAGE),
        ):
            with self.subTest(error=type(error).__name__, message=message):
                state = _ready_state(photo=PHOTO_URL, city="Nova cidade")
                self._upload(state, [_FakeUpload("f.png", "image/png", QUADRANTS_PNG)], side_effect=error)
                self.assertEqual(state.photo_error, message)
                self.assertEqual(state.photo_notice, "")
                self.assertEqual((state.photo, state.city), (PHOTO_URL, "Nova cidade"))
                self.assertFalse(state.photo_busy)

    def test_upload_401_redirects(self) -> None:
        state = _ready_state()
        events, _, _ = self._upload(
            state, [_FakeUpload("f.png", "image/png", QUADRANTS_PNG)], side_effect=ProfileUnauthorizedError()
        )
        self.assertIn("login", events)
        self.assertEqual(state.auth_token, "")
        self.assertFalse(state.photo_busy)

    def test_upload_ignored_while_busy(self) -> None:
        state = _ready_state(photo_busy=True)
        _, upload, _ = self._upload(state, [_FakeUpload("f.png", "image/png", QUADRANTS_PNG)])
        upload.assert_not_called()
        self.assertFalse(state.crop_open)

    def test_photo_rejected_on_screen(self) -> None:
        state = _ready_state(photo_notice=PHOTO_SAVED_MESSAGE)
        with patch("doafacil.editar_perfil.upload_profile_photo", new_callable=AsyncMock) as upload:
            EditProfileState.photo_rejected.fn(state, [{"errors": [{"code": "file-too-large"}]}])
        upload.assert_not_called()
        self.assertEqual(state.photo_error, PHOTO_SIZE_MESSAGE)
        self.assertEqual(state.photo_notice, "")

    def test_remove_photo_without_confirmation(self) -> None:
        state = _ready_state(photo=PHOTO_URL, name="Nome digitado")
        with patch("doafacil.editar_perfil.remove_profile_photo", new_callable=AsyncMock) as remove:
            _events(EditProfileState.remove_photo.fn(state))
        self.assertEqual(remove.await_args.args[1], TOKEN)
        self.assertEqual(state.photo, "")
        self.assertEqual(state.account_photo, "")  # o menu volta à inicial
        self.assertEqual(state.photo_notice, PHOTO_REMOVED_MESSAGE)
        self.assertEqual(state.name, "Nome digitado")
        self.assertFalse(state.photo_busy)

    def test_remove_photo_errors_and_without_photo(self) -> None:
        for error, message in (
            (ProfileRateLimitError(), RATE_LIMIT_MESSAGE),
            (ProfileServiceError(), PHOTO_ERROR_MESSAGE),
        ):
            with self.subTest(error=type(error).__name__):
                state = _ready_state(photo=PHOTO_URL)
                with patch("doafacil.editar_perfil.remove_profile_photo", new_callable=AsyncMock, side_effect=error):
                    _events(EditProfileState.remove_photo.fn(state))
                self.assertEqual((state.photo, state.photo_error), (PHOTO_URL, message))
                self.assertFalse(state.photo_busy)
        state = _ready_state(photo="")
        with patch("doafacil.editar_perfil.remove_profile_photo", new_callable=AsyncMock) as remove:
            _events(EditProfileState.remove_photo.fn(state))
        remove.assert_not_called()

    def test_remove_photo_401_redirects(self) -> None:
        state = _ready_state(photo=PHOTO_URL)
        with (
            patch("doafacil.editar_perfil.remove_profile_photo", new_callable=AsyncMock, side_effect=ProfileUnauthorizedError()),
            patch("doafacil.editar_perfil.rx.redirect", return_value="login"),
        ):
            events = _events(EditProfileState.remove_photo.fn(state))
        self.assertIn("login", events)
        self.assertEqual(state.auth_token, "")


class EditProfilePageTests(unittest.TestCase):
    def test_route_and_on_load(self) -> None:
        page = app._unevaluated_pages["perfil/editar"]
        self.assertEqual([h.fn for h in page.on_load], [EditProfileState.load_profile.fn, LoginState.load_account.fn])  # + a conta, uma vez por sessão (change navegacao-celular)

    def test_header_title_and_no_chat_button(self) -> None:
        page = edit_profile_page()
        self.assertEqual(
            str(page.children[0]),
            str(back_link_header("/minhas-doacoes", "Voltar a Minhas doações", "#007A42")),
        )
        rendered = str(page)
        self.assertIn("Editar perfil", _contents(page))
        self.assertIn('as:"h1"', rendered)
        self.assertNotIn("chat-fab", rendered)

    def test_preview_with_photo_counters_and_badge_without_email(self) -> None:
        preview = _preview()
        rendered = str(preview)
        for var in (
            "photo",
            "preview_initial",
            "preview_first_name",
            "preview_location",
            "preview_about",
            "active_count",
            "completed_count",
            "email_verified",
        ):
            with self.subTest(var=var):
                self.assertIn(f"{var}_rx_state_", rendered)
        # A foto atual (ou a inicial) em 80 px.
        self.assertIn("profile-avatar-photo", rendered)
        self.assertIn("profile-avatar-initial", rendered)
        self.assertIn('["width"] : "80px"', rendered)
        # Contadores e selo como aparecem para outras pessoas (perfil-credibilidade).
        self.assertIn("profile-counts", rendered)
        self.assertIn("verified-badge", rendered)
        # Nunca o e-mail: só o nome da variável do selo contém “email”.
        self.assertNotIn("email", rendered.replace("email_verified", ""))
        contents = _contents(preview)
        self.assertIn("E-mail verificado", contents)
        for excluded in ("Editar perfil", "Compartilhar", "E-mail"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, contents)

    def test_preview_counts_and_badge_come_before_about(self) -> None:
        rendered = str(_preview())
        positions = [
            rendered.index("preview_location_rx_state_"),
            rendered.index("profile-counts"),
            rendered.index("verified-badge"),
            rendered.index("profile-about-text"),
        ]
        self.assertEqual(positions, sorted(positions))

    def test_form_sections_fields_and_help(self) -> None:
        form = _form()
        contents = _contents(form)
        rendered = str(form)
        for text in (
            "Dados públicos",
            "Nome",
            NAME_HELP,
            "Sobre",
            ABOUT_HINT,
            "Localização",
            "Cidade",
            "Estado",
            "Conta",
            "E-mail",
            EMAIL_HELP,
            VISIBILITY_TITLE,
            VISIBILITY_TEXT,
            "Cancelar",
        ):
            with self.subTest(text=text):
                self.assertIn(text, contents)
        self.assertIn("maxLength:300,", rendered)
        self.assertIn("about_count_rx_state_", rendered)
        self.assertIn('"aria-live":"polite"', rendered)
        self.assertIn("readOnly:true", rendered)
        self.assertIn('"aria-describedby":"profile-email-help"', rendered)
        self.assertIn('to:"/minhas-doacoes"', rendered)
        self.assertIn('role:"alert"', rendered)
        self.assertIn("auth-card-enter", rendered)
        # As 27 UFs no select do estado.
        for uf in ("AC", "SP", "TO"):
            with self.subTest(uf=uf):
                self.assertIn(f'value:"{uf}"', rendered)
        # A seção Foto vem antes de “Dados públicos”.
        self.assertLess(contents.index("Foto"), contents.index("Dados públicos"))

    def test_photo_section(self) -> None:
        section = _photo_section()
        contents = _contents(section)
        rendered = str(section)
        for text in ("Foto", PHOTO_FORMATS_TEXT, PHOTO_PUBLIC_NOTICE, "Remover foto"):
            with self.subTest(text=text):
                self.assertIn(text, contents)
        self.assertEqual(PHOTO_PUBLIC_NOTICE, "Sua foto aparece para outras pessoas.")
        # “Alterar foto” dentro do upload; “Enviando...” enquanto envia.
        self.assertIn('"Alterar foto"', rendered)
        self.assertIn('"Enviando..."', rendered)
        self.assertIn(f'id:"{PHOTO_UPLOAD_ID}"', rendered)
        self.assertIn('type:"file"', rendered)
        self.assertIn("profile-avatar-photo", rendered)
        self.assertIn('["width"] : "96px"', rendered)
        # “Remover foto” só aparece com foto.
        self.assertIn("photo_rx_state_", rendered)
        self.assertIn("remove_photo", rendered)
        self.assertIn('role:"alert"', rendered)
        self.assertIn('role:"status"', rendered)
        self.assertIn("photo_error_rx_state_", rendered)
        self.assertIn("photo_notice_rx_state_", rendered)

    def test_crop_dialog(self) -> None:
        dialog = _crop_dialog()
        rendered = str(dialog)
        contents = _contents(dialog)
        for text in (CROP_TITLE, CROP_HELP, "Cancelar", "Usar foto"):
            with self.subTest(text=text):
                self.assertIn(text, contents)
        self.assertEqual(CROP_TITLE, "Ajustar foto")
        # Controlado pelo estado; fechar (Esc, clique fora) cancela.
        self.assertIn("crop_open_rx_state_", rendered)
        self.assertIn("set_crop_open", rendered)
        self.assertIn("cancel_crop", rendered)
        self.assertIn("confirm_crop", rendered)
        # “Usar foto” só depois da primeira área recebida.
        self.assertIn("crop_ready_rx_state_", rendered)
        # A moldura com a prévia e o evento da área final.
        self.assertIn("ImageCropper", rendered)
        self.assertIn("crop_preview_rx_state_", rendered)
        self.assertIn("set_crop_area", rendered)
        # Cabe em 360 px; botões de 44 px.
        self.assertEqual(CROP_DIALOG_WIDTH, "min(480px, calc(100vw - 32px))")
        self.assertIn(CROP_DIALOG_WIDTH, rendered)
        self.assertGreaterEqual(rendered.count('["minHeight"] : "44px"'), 2)
        # Contraste AA dos botões.
        self.assertGreaterEqual(_contrast("#FFFFFF", "#007A42"), 4.5)
        self.assertGreaterEqual(_contrast("#2A2A2A", "#FFFFFF"), 4.5)
        # O modal faz parte da seção Foto.
        self.assertIn("edit-profile-crop-dialog", str(_photo_section()))

    def test_upload_props_check_format_and_size_on_screen(self) -> None:
        # As props do rx.upload vão para o useDropzone (nos hooks do componente).
        upload = _photo_section().children[1].children[1].children[0]
        self.assertEqual(type(upload).__name__, "StyledUpload")
        hooks = "\n".join(upload.children[0].special_props[0]._get_all_var_data().hooks)
        # Escolher o arquivo abre o modal “Ajustar foto” (prepare_crop).
        self.assertIn("edit_profile_state.prepare_crop", hooks)
        self.assertIn(f'["upload_id"] : "{PHOTO_UPLOAD_ID}"', hooks)
        self.assertIn("edit_profile_state.photo_rejected", hooks)
        self.assertIn(f'["maxSize"] : {PHOTO_MAX_BYTES}', hooks)
        self.assertIn('["maxFiles"] : 1', hooks)
        self.assertIn('["multiple"] : false', hooks)
        for mime in ("image/jpeg", "image/png", "image/gif", "image/webp"):
            with self.subTest(mime=mime):
                self.assertIn(f'["{mime}"]', hooks)
        self.assertEqual(PHOTO_MAX_BYTES, 5 * 1024 * 1024)

    def test_visibility_text_matches_decision(self) -> None:
        self.assertIn("sua foto", VISIBILITY_TEXT)
        self.assertIn("a foto atual", VISIBILITY_TEXT)
        self.assertIn("só é mostrado a pessoas logadas", VISIBILITY_TEXT)
        self.assertIn("preferência “E-mail”", VISIBILITY_TEXT)
        self.assertNotIn("nunca aparece", VISIBILITY_TEXT)

    def test_email_is_readable_read_only_with_lock(self) -> None:
        email = next(
            node
            for node in _nodes(_form())
            if getattr(getattr(node, "id", None), "_var_value", getattr(node, "id", None)) == "profile-email"
        )
        rendered = str(email)
        # Só de leitura, não desativado: dá para selecionar e copiar.
        self.assertIn("readOnly:true", rendered)
        self.assertNotIn("disabled", rendered)
        self.assertIn('"aria-label":"E-mail (n\\u00e3o pode ser alterado)"', rendered)
        self.assertIn('["background"] : "#F1F1F1"', rendered)
        self.assertIn('["color"] : "#1F1F1F"', rendered)
        self.assertIn('["cursor"] : "default"', rendered)
        self.assertIn('["& input"] : ({ ["cursor"] : "default" })', rendered)
        # Cadeado decorativo dentro do campo, à direita.
        self.assertIn("RadixThemesTextField.Slot", rendered)
        self.assertIn('side:"right"', rendered)
        self.assertIn("LucideLock", rendered)
        self.assertIn('"#6B6B6B"', rendered)
        self.assertIn('"aria-hidden":"true"', rendered)

    def test_contrast_of_read_only_email_and_notice(self) -> None:
        self.assertGreaterEqual(_contrast("#1F1F1F", "#F1F1F1"), 4.5)
        # Ícone (elemento gráfico): pelo menos 3:1.
        self.assertGreaterEqual(_contrast("#6B6B6B", "#F1F1F1"), 3)
        self.assertGreaterEqual(_contrast("#2A2A2A", "#FFF3D6"), 4.5)
        self.assertGreaterEqual(_contrast("#166B3B", "#FFF3D6"), 4.5)

    def test_layout_and_animation(self) -> None:
        page = edit_profile_page()
        rendered = str(page)
        self.assertIn("minmax(220px, 280px) minmax(0, 1fr)", rendered)
        self.assertIn("24px 16px 48px", rendered)
        self.assertIn("repeat(2, minmax(0, 1fr))", rendered)
        animated = [n for n in _nodes(page) if getattr(n, "class_name", None) in {"page-fade-enter", "auth-card-enter"}]
        self.assertTrue(animated)
        styles = Path("assets/auth-card.css").read_text(encoding="utf-8")
        self.assertIn("@media (prefers-reduced-motion: reduce)", styles)


if __name__ == "__main__":
    unittest.main()
