"""Cor do texto digitado e do texto de exemplo em todos os campos do site.

O texto digitado ou colado aparecia claro, quase transparente, em campos sem
regra própria (como a Cidade de /perfil/editar). A correção é global no
app.style; estes testes conferem a regra e as telas com campos de texto.
"""

import unittest

from doafacil.cadastro import signup_page
from doafacil.cadastro_doacao import donation_creation_page
from doafacil.chat import chat_page
from doafacil.doafacil import (
    FIELD_PLACEHOLDER_COLOR,
    FIELD_PLACEHOLDER_SELECTOR,
    FIELD_TEXT_COLOR,
    FIELD_TEXT_SELECTOR,
    app,
    index,
)
from doafacil.editar_perfil import edit_profile_page
from doafacil.login import login_page
from doafacil.minhas_doacoes import edit_donation_page
from doafacil.recuperacao_senha import (
    new_password_page,
    request_recovery_page,
    verify_recovery_page,
)


def _luminance(color: str) -> float:
    channels = [int(color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground: str, background: str) -> float:
    a, b = _luminance(foreground), _luminance(background)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


PAGES = {
    "login": login_page,
    "cadastro": signup_page,
    "recuperar senha": request_recovery_page,
    "verificar e-mail": verify_recovery_page,
    "nova senha": new_password_page,
    "cadastro de doação": donation_creation_page,
    "edição de doação": edit_donation_page,
    "chat": chat_page,
    "editar perfil": edit_profile_page,
    "home (busca)": index,
}


class GlobalFieldColorTests(unittest.TestCase):
    def test_typed_text_is_dark_and_opaque_everywhere(self) -> None:
        self.assertEqual(FIELD_TEXT_COLOR, "#1F1F1F")
        self.assertEqual(
            app.style[FIELD_TEXT_SELECTOR],
            {
                "color": "#1F1F1F !important",
                "WebkitTextFillColor": "#1F1F1F !important",
                "opacity": "1 !important",
            },
        )

    def test_placeholder_is_medium_gray_and_opaque_everywhere(self) -> None:
        self.assertEqual(FIELD_PLACEHOLDER_COLOR, "#6B6B6B")
        self.assertEqual(
            app.style[FIELD_PLACEHOLDER_SELECTOR],
            {
                "color": "#6B6B6B !important",
                "WebkitTextFillColor": "#6B6B6B !important",
                "opacity": "1 !important",
            },
        )
        self.assertIn("input::placeholder", FIELD_PLACEHOLDER_SELECTOR)
        self.assertIn("textarea::placeholder", FIELD_PLACEHOLDER_SELECTOR)

    def test_selector_covers_inputs_and_textareas_with_exceptions(self) -> None:
        self.assertIn("textarea:not(:disabled)", FIELD_TEXT_SELECTOR)
        self.assertTrue(FIELD_TEXT_SELECTOR.startswith("input:not("))
        # Exceções: upload escondido, hidden, checkbox, radio e desativados
        # (o campo do chat somente leitura mantém o visual de desativado).
        for excluded in ("[type='file']", "[type='hidden']", "[type='checkbox']", "[type='radio']", ":disabled"):
            with self.subTest(excluded=excluded):
                self.assertIn(f":not({excluded})", FIELD_TEXT_SELECTOR)

    def test_no_redundant_field_specific_rules_remain(self) -> None:
        leftovers = [
            selector
            for selector in app.style
            if selector not in (FIELD_TEXT_SELECTOR, FIELD_PLACEHOLDER_SELECTOR)
            and ("::placeholder" in selector or "#donation-title" in selector or "#donation-description" in selector)
        ]
        self.assertEqual(leftovers, [])
        # Os prompts dos selects (botões, não campos) continuam com regra própria.
        self.assertTrue(any("rt-SelectTriggerInner" in selector for selector in app.style))
        # O autofill segue só com o fundo branco; a cor vem da regra global.
        autofill = [styles for selector, styles in app.style.items() if ":-webkit-autofill" in selector]
        self.assertEqual(len(autofill), 1)
        self.assertNotIn("WebkitTextFillColor", autofill[0])

    def test_contrast_on_white_and_read_only_backgrounds(self) -> None:
        for background in ("#FFFFFF", "#F1F1F1"):
            with self.subTest(background=background):
                self.assertGreaterEqual(_contrast(FIELD_TEXT_COLOR, background), 4.5)
                self.assertGreaterEqual(_contrast(FIELD_PLACEHOLDER_COLOR, background), 4.5)

    def test_pages_with_text_fields_render_and_do_not_fade_their_fields(self) -> None:
        for name, page in PAGES.items():
            with self.subTest(page=name):
                rendered = str(page())
                self.assertTrue(
                    "RadixThemesTextField.Root" in rendered
                    or "RadixThemesTextArea" in rendered
                    or "DebounceInput" in rendered
                )
                # Nenhum campo com texto claro ou semitransparente no próprio componente.
                for forbidden in ('["WebkitTextFillColor"] : "#fff', '["opacity"] : "0.'):
                    self.assertNotIn(forbidden, rendered)


if __name__ == "__main__":
    unittest.main()
