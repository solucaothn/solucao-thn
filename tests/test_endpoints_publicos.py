"""Endpoints do modelo do Xano removidos (change endpoints-publicos): os cinco
arquivos não existem mais no xano/, nada no xano/ os cita e o site não chama
nenhum deles."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Rotas e função removidas (decisão 2 do design da change).
REMOVED_REFERENCES = (
    "send_welcome_email",
    "request-reset-link",
    "request_reset_link",
    "magic-link-login",
    "magic_link_login",
    "reset/update_password",
    "generate_magic_link",
)


REMOVED_FILES = (
    "xano/api/authentication/message/send_welcome_email_POST.xs",
    "xano/api/authentication/reset/request_reset_link_GET.xs",
    "xano/api/authentication/reset/magic_link_login_POST.xs",
    "xano/api/authentication/reset/update_password_POST.xs",
    "xano/function/quick_start/generate_magic_link.xs",
)


class RemovedEndpointsTests(unittest.TestCase):
    def test_removed_xano_files_do_not_exist(self) -> None:
        for relative in REMOVED_FILES:
            with self.subTest(file=relative):
                self.assertFalse((ROOT / relative).exists())

    def test_xano_folder_does_not_reference_removed_objects(self) -> None:
        for path in sorted((ROOT / "xano").rglob("*.xs")):
            text = path.read_text(encoding="utf-8")
            for reference in REMOVED_REFERENCES:
                with self.subTest(file=str(path.relative_to(ROOT)), reference=reference):
                    self.assertNotIn(reference, text)

    def test_frontend_does_not_call_removed_endpoints(self) -> None:
        for path in sorted((ROOT / "doafacil").rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for reference in REMOVED_REFERENCES:
                with self.subTest(file=path.name, reference=reference):
                    self.assertNotIn(reference, text)


if __name__ == "__main__":
    unittest.main()
