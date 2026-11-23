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


class PublishInputsTests(unittest.TestCase):
    """Change correcoes-finais: o publish aceita os mesmos limites e valores
    da edição (donations_PATCH)."""

    def setUp(self) -> None:
        catalog = ROOT / "xano" / "api" / "catalog" / "catalog"
        self.publish = (catalog / "donations" / "publish_POST.xs").read_text(encoding="utf-8")
        self.patch = (catalog / "donations_PATCH.xs").read_text(encoding="utf-8")

    def test_title_and_description_limits(self) -> None:
        self.assertIn("text title filters=trim|min:1|max:100", self.publish)
        # A descrição continua opcional no publish (outros consumidores).
        self.assertIn("text description? filters=trim|max:2000", self.publish)

    def test_delivery_and_contact_values_match_the_edit(self) -> None:
        for block in (
            'enum delivery_method {\n      values = ["A combinar"]\n    }',
            'enum contact_preference {\n      values = ["E-mail", "Chat do DoaFácil"]\n    }',
        ):
            with self.subTest(block=block.split()[1]):
                self.assertIn(block, self.publish)
                self.assertIn(block, self.patch)
        for removed in ("WhatsApp", "Retirada", '"Entrega"'):
            with self.subTest(value=removed):
                self.assertNotIn(removed, self.publish)


if __name__ == "__main__":
    unittest.main()
