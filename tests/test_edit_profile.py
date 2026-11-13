import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx

from doafacil.chat import back_link_header
from doafacil.doafacil import app
from doafacil.editar_perfil import (
    ABOUT_HINT,
    EMAIL_HELP,
    LOAD_ERROR_MESSAGE,
    NAME_HELP,
    RATE_LIMIT_MESSAGE,
    SAVE_ERROR_MESSAGE,
    SAVE_REJECTED_MESSAGE,
    VISIBILITY_TEXT,
    VISIBILITY_TITLE,
    EditProfileState,
    ProfileRateLimitError,
    ProfileRejectedError,
    ProfileServiceError,
    ProfileUnauthorizedError,
    _form,
    _parse_profile,
    _preview,
    edit_profile_page,
    fetch_profile,
    first_name_of,
    update_profile,
    validate_profile,
)
from doafacil.minhas_doacoes import SAVED_MESSAGE, MyDonationsState
from doafacil.sobre import about_text, parse_about


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


def _call(handler, function, *args):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await function(client, TOKEN, *args)

    with patch.dict("os.environ", {"XANO_AUTH_API_URL": AUTH_URL}):
        return asyncio.run(run())


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
        form_error="",
        is_saving=False,
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
            return httpx.Response(200, json=PROFILE_PAYLOAD)

        profile = _call(handler, fetch_profile)
        self.assertEqual(profile["name"], "Ana Beatriz Lima")
        self.assertEqual(profile["state"], "SP")
        self.assertEqual(profile["about"], "Gosto de doar.\nAté breve.")

    def test_null_about_becomes_empty_and_extra_fields_are_ignored(self) -> None:
        profile = _parse_profile({**PROFILE_PAYLOAD, "about": None, "role": "admin", "password": "x"})
        self.assertEqual(profile["about"], "")
        self.assertEqual(set(profile), {"name", "email", "city", "state", "about"})
        profile = _parse_profile({k: v for k, v in PROFILE_PAYLOAD.items() if k != "about"})
        self.assertEqual(profile["about"], "")

    def test_invalid_responses(self) -> None:
        for label, payload in {
            "lista": [],
            "nome nulo": {**PROFILE_PAYLOAD, "name": None},
            "cidade número": {**PROFILE_PAYLOAD, "city": 1},
            "about número": {**PROFILE_PAYLOAD, "about": 2},
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
            return_value=_parse_profile(PROFILE_PAYLOAD),
        ):
            _events(EditProfileState.load_profile.fn(state))
        self.assertEqual(state.view_state, "ready")
        self.assertEqual((state.name, state.email, state.city, state.uf), ("Ana Beatriz Lima", "ana@example.test", "Campinas", "SP"))
        self.assertEqual(state.about, "Gosto de doar.\nAté breve.")

    def test_state_outside_list_starts_empty(self) -> None:
        state = _state()
        with patch(
            "doafacil.editar_perfil.fetch_profile",
            new_callable=AsyncMock,
            return_value=_parse_profile({**PROFILE_PAYLOAD, "state": "São Paulo"}),
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


class EditProfilePageTests(unittest.TestCase):
    def test_route_and_on_load(self) -> None:
        page = app._unevaluated_pages["perfil/editar"]
        self.assertEqual(page.on_load.fn, EditProfileState.load_profile.fn)

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

    def test_preview_without_email_counters_or_photo(self) -> None:
        preview = _preview()
        rendered = str(preview)
        for var in ("preview_initial", "preview_first_name", "preview_location", "preview_about"):
            with self.subTest(var=var):
                self.assertIn(f"{var}_rx_state_", rendered)
        self.assertNotIn("email", rendered)
        self.assertNotIn("Image", [type(n).__name__ for n in _nodes(preview)])
        contents = _contents(preview)
        for excluded in ("Doações", "Editar perfil", "Compartilhar", "E-mail"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, contents)

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
        # Sem foto nesta change.
        for excluded in ("Foto", "Alterar foto", "Remover foto"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, contents)
        self.assertNotIn("upload", rendered.lower())

    def test_visibility_text_matches_decision(self) -> None:
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
