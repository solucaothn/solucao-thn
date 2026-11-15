"""Change esquema-xano: um único arquivo do xano/ declara a rota
catalog/donations/contact-email (o arquivo antigo, de outro nome e mesmo guid,
era uma sobra local).

As linhas de esquema das tabelas não são conferidas aqui: a exportação do CLI
omite o "=valor" dos padrões e mostra "?" mesmo em campo obrigatório, então
qualquer pull as mudaria. O painel do Xano é a fonte da verdade para elas."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTACT_EMAIL_ROUTE = 'query "catalog/donations/contact-email" verb=GET'


class ContactEmailRouteTests(unittest.TestCase):
    def test_single_file_declares_contact_email_route(self) -> None:
        files = [
            path.relative_to(ROOT).as_posix()
            for path in sorted((ROOT / "xano").rglob("*.xs"))
            if CONTACT_EMAIL_ROUTE in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(files, ["xano/api/catalog/catalog/donations/contact_email_GET.xs"])


if __name__ == "__main__":
    unittest.main()
