"""Change emails-novos: conteúdo dos e-mails de código (confirmação de
cadastro e redefinição de senha) nas funções do Xano.

Os testes leem os .xs e o HTML/texto que o script de prévias monta a partir
deles, do mesmo jeito que a função faz (substr + replace). Nada é enviado ao
Xano nem ao SendGrid."""

import importlib.util
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "gerar_previas_emails", ROOT / "scripts" / "gerar_previas_emails.py"
)
previas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(previas)

LOGO_URL = (
    "https://raw.githubusercontent.com/solucaothn/solucao-thn/main/"
    "assets/email/logo-email.png"
)
FONT_STACK = "font-family:Helvetica, Arial, sans-serif"
EXPIRY = "O código expira em 10 minutos."
FOOTER = (
    "Você recebeu este e-mail porque alguém usou este endereço no DoaFácil.",
    "Projeto acadêmico DoaFácil",
)

EMAILS = {
    "signup": {
        "xs": "xano/function/signup/send_confirmation_code.xs",
        "preview": "docs/emails/confirmacao-cadastro.html",
        "subject": "Confirme seu e-mail no DoaFácil",
        "texts": (
            "Confirme seu e-mail",
            "Use o código abaixo para confirmar seu endereço e ativar sua conta no DoaFácil.",
            "Seu código",
            EXPIRY,
            "Se você não criou uma conta no DoaFácil, pode ignorar este e-mail. "
            "Nada será feito com o seu endereço.",
            *FOOTER,
        ),
        # Endpoints que geram o código e chamam esta função.
        "endpoints": (
            "xano/api/authentication/auth/signup_POST.xs",
            "xano/api/authentication/auth/signup_resend_POST.xs",
        ),
        "error": "Não foi possível enviar o código de confirmação.",
    },
    "recovery": {
        "xs": "xano/function/password_recovery/send_recovery_code.xs",
        "preview": "docs/emails/redefinicao-senha.html",
        "subject": "Redefinir sua senha no DoaFácil",
        "texts": (
            "Redefinir sua senha",
            "Recebemos um pedido para redefinir a senha da sua conta. "
            "Use o código abaixo para continuar.",
            "Seu código",
            EXPIRY,
            "Se você não pediu para redefinir sua senha, pode ignorar este e-mail. "
            "Sua senha atual continua valendo.",
            *FOOTER,
        ),
        "endpoints": ("xano/api/authentication/reset/request_code_POST.xs",),
        "error": "Não foi possível enviar a mensagem de recuperação.",
    },
}


class _VisibleText(HTMLParser):
    """Texto visível do HTML (sem <head> e sem o preheader oculto)."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        style = dict(attrs).get("style") or ""
        if tag in ("head", "title") or "display:none" in style:
            self._skip += 1
        elif tag == "br" and not self._skip:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self._skip and tag in ("head", "title", "div"):
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)

    def lines(self) -> list[str]:
        text = "".join(self.parts).replace("\xa0", " ")
        return [" ".join(line.split()) for line in text.splitlines() if line.strip()]


def _visible_lines(html: str) -> list[str]:
    parser = _VisibleText()
    parser.feed(html)
    return parser.lines()


class CodeEmailTests(unittest.TestCase):
    def _each(self):
        for name, email in EMAILS.items():
            source = (ROOT / email["xs"]).read_text(encoding="utf-8")
            with self.subTest(email=name):
                yield email, source

    def test_subject_and_both_content_types_in_order(self) -> None:
        for email, source in self._each():
            self.assertIn(f'subject         : "{email["subject"]}"', source)
            content = source[source.index("content         : ["):]
            plain = content.index('type : "text/plain"')
            html = content.index('type : "text/html"')
            # O SendGrid exige text/plain antes de text/html.
            self.assertLess(plain, html)
            self.assertIn("value: $message", content[plain:html])
            self.assertIn("value: $html", content[html:])

    def test_html_texts_match_the_model_in_order(self) -> None:
        for email, source in self._each():
            lines = _visible_lines(previas.render_html(source, "482913"))
            expected = list(email["texts"])
            # O código aparece logo depois de “Seu código”.
            expected.insert(expected.index("Seu código") + 1, "482913")
            self.assertEqual(lines, expected)

    def test_plain_text_has_the_same_texts_and_copyable_code(self) -> None:
        for email, source in self._each():
            text = previas.render_text(source, "482913")
            for line in email["texts"]:
                if line != "Seu código":
                    self.assertIn(line, text)
            self.assertIn("Seu código: 482913", text)
            self.assertNotIn("482 913", text)
            self.assertNotIn("{{", text)

    def test_code_shows_as_three_plus_three_without_a_space(self) -> None:
        for _email, source in self._each():
            html = previas.render_html(source, "407150")
            # Grupo 40 + 7 (com espaçamento maior) + 150; nenhum espaço entre eles.
            self.assertIn(
                ">40<span style=\"letter-spacing:28px;\">7</span>150</p>", html
            )
            self.assertIn("letter-spacing:8px;white-space:nowrap;", html)
            self.assertNotIn("{{", html)
            # A função monta as partes com substr, nas mesmas posições.
            self.assertIn('"{{CODIGO_INICIO}}":($input.code|substr:0:2)', source)
            self.assertIn('"{{CODIGO_MEIO}}":($input.code|substr:2:1)', source)
            self.assertIn('"{{CODIGO_FIM}}":($input.code|substr:3:3)', source)
            self.assertIn('|replace:"{{CODIGO}}":$input.code', source)

    def test_email_safe_html(self) -> None:
        for _email, source in self._each():
            html = previas.render_html(source)
            self.assertIn(
                f'<img src="{LOGO_URL}" width="160" height="58" alt="DoaFácil"', html
            )
            self.assertIn('width="600"', html)
            self.assertIn("max-width:600px", html)
            self.assertIn('role="presentation"', html)
            self.assertIn('bgcolor="#FFF6E8"', html)
            self.assertIn("color:#0B5A2E", html)  # título verde-escuro
            self.assertIn("background-color:#F1F3F2;border:1px solid #8E9490", html)
            self.assertIn("font-size:44px", html)
            self.assertIn("color:#168447", html)  # código verde
            self.assertIn(FONT_STACK, html)
            # Só CSS inline, sem links e sem fontes ou arquivos externos além do logo.
            self.assertNotIn("<style", html)
            self.assertNotIn("<a ", html)
            self.assertNotIn("href", html)
            self.assertEqual(re.findall(r"https?://[^\"' )]+", html), [LOGO_URL])
            # Toda font-family usada é a pilha segura.
            for family in re.findall(r"font-family:[^;\"]+", html):
                self.assertEqual(family, FONT_STACK)

    def test_expiry_text_matches_the_real_validity(self) -> None:
        for email, _source in self._each():
            for endpoint in email["endpoints"]:
                code = (ROOT / endpoint).read_text(encoding="utf-8")
                validity = re.findall(
                    r"code_expires_at\s*: now\|add_secs_to_timestamp:\((\d+)\|to_int\)",
                    code,
                )
                self.assertTrue(validity, endpoint)
                # “10 minutos” no e-mail = 600 s em todos os pontos que geram o código.
                self.assertEqual(set(validity), {"600"}, endpoint)

    def test_sendgrid_call_is_unchanged_and_key_stays_in_env(self) -> None:
        for email, source in self._each():
            self.assertIn('url = "https://api.sendgrid.com/v3/mail/send"', source)
            self.assertIn('method = "POST"', source)
            self.assertIn("params = $payload", source)
            self.assertIn('"Authorization: Bearer " ~ $env.SENDGRID_API_KEY', source)
            self.assertIn("from            : {email: $env.SENDGRID_FROM_EMAIL}", source)
            self.assertIn("timeout = 30", source)
            self.assertIn(
                "precondition ($sendgrid_response.response.status >= 200 && "
                "$sendgrid_response.response.status < 300)",
                source,
            )
            self.assertIn(email["error"], source)
            self.assertIn("response = {success: true}", source)
            self.assertNotRegex(source, r"SG\.[A-Za-z0-9_-]{10,}")

    def test_previews_are_up_to_date(self) -> None:
        for email, source in self._each():
            preview = (ROOT / email["preview"]).read_text(encoding="utf-8")
            self.assertEqual(
                preview,
                previas.render_html(source) + "\n",
                "rode python scripts/gerar_previas_emails.py",
            )
            self.assertIn(">48<span", preview)


if __name__ == "__main__":
    unittest.main()
