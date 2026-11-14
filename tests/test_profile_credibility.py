"""Selo “E-mail verificado” e contadores de doações (change perfil-credibilidade):
componentes compartilhados de doafacil/perfil_publico.py e os parsers."""

import unittest

from doafacil.editar_perfil import EditProfileState
from doafacil.perfil_publico import (
    ACTIVE_LABELS,
    COMPLETED_LABELS,
    COUNT_LABEL_COLOR,
    COUNT_NUMBER_COLOR,
    VERIFIED_BACKGROUND,
    VERIFIED_BORDER,
    VERIFIED_ICON,
    VERIFIED_LABEL,
    VERIFIED_TEXT_COLOR,
    count_label,
    donation_counts,
    parse_count,
    parse_counts,
    parse_email_verified,
    verified_badge,
)


CARD_WHITE = "#FFFFFF"


def _luminance(color: str) -> float:
    channels = [int(color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground: str, background: str) -> float:
    a, b = _luminance(foreground), _luminance(background)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


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


class ParserTests(unittest.TestCase):
    def test_email_verified_only_accepts_bool(self) -> None:
        self.assertIs(parse_email_verified(True), True)
        self.assertIs(parse_email_verified(False), False)
        for value in (None, 0, 1, "true", "", [], {}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_email_verified(value)

    def test_count_only_accepts_non_negative_int(self) -> None:
        self.assertEqual(parse_count(0), 0)
        self.assertEqual(parse_count(12), 12)
        for value in (-1, 1.0, 2.5, "3", None, True, False):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_count(value)

    def test_counts_object(self) -> None:
        self.assertEqual(parse_counts({"active": 3, "completed": 0, "extra": 9}), (3, 0))
        for value in (None, [], {"active": 1}, {"completed": 1}, {"active": -1, "completed": 0}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_counts(value)


class VerifiedBadgeTests(unittest.TestCase):
    def test_true_shows_decorative_icon_and_text(self) -> None:
        badge = verified_badge(EditProfileState.email_verified)
        rendered = str(badge)
        self.assertIn("email_verified_rx_state_", rendered)
        self.assertIn("LucideBadgeCheck", rendered)
        self.assertEqual(VERIFIED_ICON, "badge-check")
        self.assertIn('"aria-hidden":"true"', rendered)
        self.assertEqual(_contents(badge), [VERIFIED_LABEL])
        self.assertEqual(VERIFIED_LABEL, "E-mail verificado")
        self.assertIn("verified-badge", rendered)

    def test_false_renders_nothing(self) -> None:
        rendered = str(verified_badge(EditProfileState.email_verified))
        # O outro ramo do cond é um fragmento vazio: sem texto, sem espaço.
        self.assertIn("(jsx(Fragment,{},))", rendered)
        for excluded in ("não verificado", "Não verificado", "Verificado"):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, _contents(verified_badge(EditProfileState.email_verified)))

    def test_badge_fits_narrow_screens(self) -> None:
        rendered = str(verified_badge(EditProfileState.email_verified))
        # Largura do conteúdo, nunca maior que o cartão (360 px sem rolagem).
        self.assertIn('["width"] : "fit-content"', rendered)
        self.assertIn('["maxWidth"] : "100%"', rendered)
        self.assertNotIn("nowrap", rendered)

    def test_contrast_is_aa(self) -> None:
        # Texto e ícone sobre o fundo do selo.
        self.assertGreaterEqual(_contrast(VERIFIED_TEXT_COLOR, VERIFIED_BACKGROUND), 4.5)
        # O fundo do selo se distingue do cartão pela borda; o texto também
        # passa sobre o branco do cartão.
        self.assertGreaterEqual(_contrast(VERIFIED_TEXT_COLOR, CARD_WHITE), 4.5)
        self.assertEqual(
            (VERIFIED_TEXT_COLOR, VERIFIED_BACKGROUND, VERIFIED_BORDER),
            ("#166B3B", "#E8F5EC", "#B7DEC4"),
        )


class DonationCountsTests(unittest.TestCase):
    def test_labels_singular_and_plural(self) -> None:
        self.assertEqual(count_label(1, *ACTIVE_LABELS), "Doação")
        self.assertEqual(count_label(0, *ACTIVE_LABELS), "Doações")
        self.assertEqual(count_label(2, *ACTIVE_LABELS), "Doações")
        self.assertEqual(count_label(1, *COMPLETED_LABELS), "Doação realizada")
        self.assertEqual(count_label(7, *COMPLETED_LABELS), "Doações realizadas")

    def test_component_uses_both_counts_with_singular_when_one(self) -> None:
        rendered = str(
            donation_counts(EditProfileState.active_count, EditProfileState.completed_count)
        )
        self.assertIn("active_count_rx_state_", rendered)
        self.assertIn("completed_count_rx_state_", rendered)
        self.assertIn("=== 1", rendered)
        for label in ("Doa\\u00e7\\u00e3o", "Doa\\u00e7\\u00f5es", "Doa\\u00e7\\u00e3o realizada", "Doa\\u00e7\\u00f5es realizadas"):
            with self.subTest(label=label):
                self.assertIn(f'"{label}"', rendered)
        self.assertIn("profile-counts", rendered)

    def test_counts_contrast_on_white(self) -> None:
        self.assertGreaterEqual(_contrast(COUNT_NUMBER_COLOR, CARD_WHITE), 4.5)
        self.assertGreaterEqual(_contrast(COUNT_LABEL_COLOR, CARD_WHITE), 4.5)


if __name__ == "__main__":
    unittest.main()
