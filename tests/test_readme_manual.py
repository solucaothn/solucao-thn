"""Confere o manual de uso (README.md) contra o código (change readme-manual).

O manual não pode citar tela, botão ou mensagem que o site não tem, nem expor
endereços do Xano, tokens ou e-mails além do contato público do projeto.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
TECH_README = ROOT / "docs" / "README-tecnico.md"
CODE = "\n".join(
    path.read_text(encoding="utf-8") for path in sorted((ROOT / "doafacil").glob("*.py"))
)
CONTACT_EMAIL = "solucaothn@gmail.com"

SECTIONS = [
    "## 1. Apresentação",
    "## 2. Acesso ao aplicativo",
    "## 3. Perfis de usuários",
    "## 4. Funcionalidades",
    "## 5. Manual de utilização",
    "## 6. Exemplos de utilização",
    "## 7. Limitações conhecidas",
    "## Equipe",
    "## Capturas de tela a tirar",
]
JOURNEYS = [
    "Criar conta",
    "Entrar e recuperar a senha",
    "Explorar e filtrar",
    "detalhe da doação e o perfil de quem doa",
    "chat",
    "Publicar uma doação",
    "Minhas doações",
    "Editar o perfil e a foto",
    "Central de ajuda",
    "celular",
]
# Rótulos montados no código a partir de partes (número da foto etc.).
COMPOSED_LABELS = {"Tornar … a capa"}


def _readme() -> str:
    return README.read_text(encoding="utf-8")


class ReadmeManualTests(unittest.TestCase):
    def test_sections_follow_the_requested_order(self) -> None:
        text = _readme()
        positions = [text.find(section) for section in SECTIONS]
        self.assertNotIn(-1, positions, positions)
        self.assertEqual(positions, sorted(positions))

    def test_every_journey_has_its_own_subsection(self) -> None:
        headings = re.findall(r"^### 5\.\d+ (.+)$", _readme(), flags=re.MULTILINE)
        for journey in JOURNEYS:
            with self.subTest(journey=journey):
                self.assertTrue(any(journey.lower() in h.lower() for h in headings), headings)

    def test_access_section_has_the_local_setup(self) -> None:
        text = _readme()
        for piece in (
            "git clone https://github.com/solucaothn/solucao-thn.git",
            "python -m venv .venv",
            "pip install -r requirements.txt",
            "reflex run",
            "http://localhost:3000",
            "XANO_API_URL",
            "XANO_AUTH_API_URL",
        ):
            with self.subTest(piece=piece):
                self.assertIn(piece, text)

    def test_quoted_labels_exist_in_the_code(self) -> None:
        labels = set(re.findall(r"\*\*“([^”]+)”\*\*", _readme()))
        self.assertGreater(len(labels), 30)
        for label in sorted(labels - COMPOSED_LABELS):
            with self.subTest(label=label):
                self.assertIn(label, CODE)

    def test_quoted_messages_exist_in_the_code(self) -> None:
        # Mensagens de resultado citadas entre aspas (sem negrito).
        for message in (
            "E-mail ou senha incorretos.",
            "Nenhuma doação encontrada",
            "Quem doa prefere contato pelo chat.",
            "Não é possível conversar sobre esta doação pelo chat.",
            "Adicione pelo menos uma foto para continuar.",
            "Doação publicada!",
            "Doação marcada como reservada.",
            "Doação marcada como concluída.",
            "Alterações salvas.",
            "Doação apagada.",
            "Apagar esta doação?",
            "Foto atualizada.",
            "O site está com muitos acessos agora. Tente de novo em instantes.",
            "As fotos, a cidade e a UF não mudam por aqui.",
            "Remover o filtro de categoria",
        ):
            with self.subTest(message=message):
                self.assertIn(message, _readme())
                self.assertIn(message, CODE)

    def test_help_topics_match_the_help_center(self) -> None:
        from doafacil.institucional import HELP_CATEGORIES

        names = [category["name"] for category in HELP_CATEGORIES]
        self.assertIn(
            "**" + ", ".join(names[:-1]) + " e " + names[-1] + "**", _readme()
        )

    def test_my_donations_actions_match_the_menu(self) -> None:
        text = _readme()
        for row in (
            "| Disponível | Marcar como reservada, Marcar como concluída, Editar, Apagar |",
            "| Reservada | Marcar como disponível, Marcar como concluída, Editar, Apagar |",
            "| Concluída | Apagar |",
        ):
            with self.subTest(row=row):
                self.assertIn(row, text)

    def test_routes_cited_exist(self) -> None:
        app = (ROOT / "doafacil" / "doafacil.py").read_text(encoding="utf-8")
        for route in ("/cadastro", "/login", "/recuperar-senha", "/verificar-email", "/nova-senha",
                      "/cadastro-doacao", "/minhas-doacoes", "/perfil/editar", "/chat", "/categorias"):
            with self.subTest(route=route):
                self.assertIn(f'route="{route}"', app)

    def test_every_screenshot_is_listed_once(self) -> None:
        text = _readme()
        used = re.findall(r"!\[[^\]]+\]\(docs/manual/([0-9]{2}-[a-z0-9-]+\.png)\)", text)
        listed = re.findall(r"^\| `([0-9]{2}-[a-z0-9-]+\.png)` \|", text, flags=re.MULTILINE)
        self.assertEqual(len(used), len(set(used)))
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(used, listed)
        self.assertEqual(used, sorted(used))

    def test_screenshot_list_is_short(self) -> None:
        used = re.findall(r"!\[[^\]]+\]\(docs/manual/([0-9]{2}-[a-z0-9-]+\.png)\)", _readme())
        self.assertLessEqual(len(used), 12)

    def test_readme_only_shows_screenshots_that_exist(self) -> None:
        # Enquanto nenhuma captura foi salva, o manual guarda os espaços
        # planejados. Depois da primeira, toda imagem citada precisa existir:
        # a que não foi salva sai do README.
        manual = ROOT / "docs" / "manual"
        if not any(manual.glob("*.png")):
            self.skipTest("nenhuma captura salva em docs/manual/ ainda")
        used = re.findall(r"!\[[^\]]+\]\(docs/manual/([^)]+)\)", _readme())
        missing = [name for name in used if not (manual / name).is_file()]
        self.assertEqual(missing, [], "imagens citadas no README sem arquivo em docs/manual/")

    def test_backend_urls_were_delivered_to_the_teacher(self) -> None:
        access = _readme().split("## 2. Acesso ao aplicativo", 1)[1].split("## 3.", 1)[0]
        self.assertIn("enviadas ao professor no arquivo .txt da entrega", access)
        self.assertIn("não ficam no repositório", access)

    def test_relative_links_point_to_existing_files(self) -> None:
        for doc in (README, TECH_README):
            text = doc.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(((?!https?://|docs/manual/)[^)#]+)\)", text):
                with self.subTest(doc=doc.name, target=target):
                    self.assertTrue((doc.parent / target).exists(), target)
        self.assertTrue((ROOT / "docs" / "manual").is_dir())

    def test_no_secrets_or_personal_emails(self) -> None:
        for doc in (README, TECH_README):
            text = doc.read_text(encoding="utf-8")
            with self.subTest(doc=doc.name):
                self.assertNotIn("xano.io", text)
                self.assertNotRegex(text, r"eyJ[A-Za-z0-9_-]{10,}")
                self.assertNotRegex(text, r"SG\.[A-Za-z0-9_-]{10,}")
                emails = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))
                self.assertLessEqual(emails, {CONTACT_EMAIL})


if __name__ == "__main__":
    unittest.main()
