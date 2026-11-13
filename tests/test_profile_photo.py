"""Foto de perfil fora da edição: avatar compartilhado, parsers e telas que
mostram a foto (perfil público, Minhas doações, “Quem doa” e chat)."""

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from doafacil.chat import (
    ChatServiceError,
    ChatState,
    _conversation_header,
    _parse_conversation,
    _parse_messages_page,
)
from doafacil.detalhe_doacao import DonationDetailState, _donor_card_content, _parse_donation_detail
from doafacil.editar_perfil import EditProfileState
from doafacil.minhas_doacoes import MyDonationsServiceError, MyDonationsState, _owner_card, _parse_my_donations
from doafacil.perfil_doador import DonorProfileState, _identity_card, _parse_donor_profile
from doafacil.perfil_publico import avatar, parse_photo_url


PHOTO_URL = "https://xano.example/vault/abc/foto.png"
NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)
INVALID_PHOTOS = (3, ["x"], "javascript:alert(1)", "data:image/png;base64,AAAA", "/vault/a.png", "https://")


class ParsePhotoUrlTests(unittest.TestCase):
    def test_valid_and_empty(self) -> None:
        self.assertEqual(parse_photo_url(None), "")
        self.assertEqual(parse_photo_url(""), "")
        self.assertEqual(parse_photo_url("   "), "")
        self.assertEqual(parse_photo_url(f"  {PHOTO_URL} "), PHOTO_URL)
        self.assertEqual(parse_photo_url("http://x.example/a.jpg"), "http://x.example/a.jpg")

    def test_invalid(self) -> None:
        for value in INVALID_PHOTOS:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_photo_url(value)


class AvatarTests(unittest.TestCase):
    def _render(self) -> str:
        return str(
            avatar(
                EditProfileState.photo,
                EditProfileState.preview_initial,
                EditProfileState.preview_first_name,
                "48px",
                background="#F2F2F2",
                color="#555555",
                font_size="1.3rem",
            )
        )

    def test_photo_or_initial_with_same_size(self) -> None:
        rendered = self._render()
        self.assertIn("photo_rx_state_", rendered)
        self.assertIn("profile-avatar-photo", rendered)
        self.assertIn("profile-avatar-initial", rendered)
        self.assertIn('["objectFit"] : "cover"', rendered)
        self.assertEqual(rendered.count('["width"] : "48px"'), 2)
        self.assertEqual(rendered.count('["height"] : "48px"'), 2)
        self.assertIn('["borderRadius"] : "999px"', rendered)

    def test_alt_text_with_first_name_and_decorative_initial(self) -> None:
        rendered = self._render()
        self.assertIn('("Foto de "+', rendered)
        self.assertIn("preview_first_name_rx_state_", rendered)
        self.assertIn('"aria-hidden":"true"', rendered)


def _donor_payload(photo: object) -> dict:
    return {
        "donor": {"first_name": "Ana", "city": "Campinas", "state": "SP", "member_since": "2020-10", "photo": photo},
        "items": [],
        "page": 1,
        "per_page": 12,
        "total": 0,
        "page_total": 0,
    }


def _mine_payload(photo: object) -> dict:
    return {
        "owner": {"first_name": "Ana", "photo": photo},
        "counts": {"active": 0, "completed": 0},
        "items": [],
        "page": 1,
        "per_page": 6,
        "total": 0,
        "page_total": 0,
    }


def _detail_payload(photo: object) -> dict:
    payload = {
        "id": 42,
        "title": "Carrinho",
        "condition": "Bom",
        "description": "Em bom estado.",
        "category": "Brinquedos",
        "city": "Campinas",
        "state": "SP",
        "delivery_method": "A combinar",
        "contact_preference": "Chat",
        "donor_first_name": "Ana",
        "photos": ["https://images.example/capa.jpg"],
    }
    if photo is not ...:
        payload["donor_photo"] = photo
    return payload


def _conversation(photo: object) -> dict:
    item = {
        "conversation_id": 7,
        "donation_id": 107,
        "last_message_at": 1_762_800_000_000,
        "other_user_first_name": "Ana",
        "donation_title": "Carrinho",
        "donation_status": "disponível",
        "unread_count": 0,
    }
    if photo is not ...:
        item["other_user_photo"] = photo
    return item


def _messages_page(photo: object) -> dict:
    page = {
        "messages": [],
        "donation_title": "Carrinho",
        "donation_status": "disponível",
        "has_older": False,
        "has_newer": False,
        "other_last_read_message_id": 0,
        "edited_messages": [],
        "server_time": 1_762_800_500_000,
    }
    if photo is not ...:
        page["other_user_photo"] = photo
    return page


class ScreenParserTests(unittest.TestCase):
    def test_donor_profile_photo(self) -> None:
        self.assertEqual(_parse_donor_profile(_donor_payload(PHOTO_URL), NOW)["photo"], PHOTO_URL)
        self.assertEqual(_parse_donor_profile(_donor_payload(None), NOW)["photo"], "")
        with self.assertRaises(ValueError):
            _parse_donor_profile(_donor_payload("ftp://x.example/a.png"), NOW)

    def test_my_donations_photo(self) -> None:
        self.assertEqual(_parse_my_donations(_mine_payload(PHOTO_URL))["photo"], PHOTO_URL)
        self.assertEqual(_parse_my_donations(_mine_payload(None))["photo"], "")
        with self.assertRaises(MyDonationsServiceError):
            _parse_my_donations(_mine_payload(5))

    def test_detail_donor_photo(self) -> None:
        self.assertEqual(_parse_donation_detail(_detail_payload(PHOTO_URL), expected_id=42)["donor_photo"], PHOTO_URL)
        self.assertEqual(_parse_donation_detail(_detail_payload(None), expected_id=42)["donor_photo"], "")
        self.assertEqual(_parse_donation_detail(_detail_payload(...), expected_id=42)["donor_photo"], "")
        with self.assertRaises(ValueError):
            _parse_donation_detail(_detail_payload("javascript:x"), expected_id=42)

    def test_chat_conversation_and_page_photo(self) -> None:
        self.assertEqual(_parse_conversation(_conversation(PHOTO_URL), require_unread=True)["other_user_photo"], PHOTO_URL)
        self.assertEqual(_parse_conversation(_conversation(None), require_unread=True)["other_user_photo"], "")
        self.assertEqual(_parse_conversation(_conversation(...), require_unread=True)["other_user_photo"], "")
        self.assertEqual(_parse_messages_page(_messages_page(PHOTO_URL))["other_user_photo"], PHOTO_URL)
        self.assertEqual(_parse_messages_page(_messages_page(...))["other_user_photo"], "")
        with self.assertRaises(ChatServiceError):
            _parse_conversation(_conversation(1), require_unread=True)
        with self.assertRaises(ChatServiceError):
            _parse_messages_page(_messages_page("data:x"))


class ScreenAvatarTests(unittest.TestCase):
    def test_donor_profile_identity(self) -> None:
        rendered = str(_identity_card())
        self.assertIn("photo_rx_state_", rendered)
        self.assertIn("profile-avatar-photo", rendered)
        self.assertIn('id:"donor-profile-avatar"', rendered)
        self.assertEqual(DonorProfileState.get_fields()["photo"].default, "")

    def test_my_donations_owner_card(self) -> None:
        rendered = str(_owner_card())
        self.assertIn("photo_rx_state_", rendered)
        self.assertIn("profile-avatar-photo", rendered)
        self.assertIn('["width"] : "80px"', rendered)
        self.assertEqual(MyDonationsState.get_fields()["photo"].default, "")

    def test_detail_who_donates_has_48px_avatar(self) -> None:
        rendered = str(_donor_card_content())
        self.assertIn("donor_photo_rx_state_", rendered)
        self.assertIn("donor_initial_rx_state_", rendered)
        self.assertIn('["width"] : "48px"', rendered)
        initial = DonationDetailState.computed_vars["donor_initial"].fget(SimpleNamespace(donor_first_name="ana"))
        self.assertEqual(initial, "A")

    def test_chat_header_has_38px_avatar(self) -> None:
        rendered = str(_conversation_header())
        self.assertIn("active_other_photo_rx_state_", rendered)
        self.assertIn("active_other_initial_rx_state_", rendered)
        self.assertIn('["width"] : "38px"', rendered)
        initial = ChatState.computed_vars["active_other_initial"].fget(SimpleNamespace(active_other_name="beatriz"))
        self.assertEqual(initial, "B")


if __name__ == "__main__":
    unittest.main()
