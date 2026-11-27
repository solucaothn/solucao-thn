"""Gera as prévias locais dos e-mails de código (change emails-novos).

Uso, na raiz do projeto, com o .venv ativo:

    python scripts/gerar_previas_emails.py

Lê o HTML de cada função do Xano (o bloco ``\"\"\"`` de ``$html_template``),
troca os marcadores pelo código de exemplo 482913, como a função faz com
``|replace``, e grava o resultado em ``docs/emails/``. O ``.xs`` continua
sendo a única fonte: depois de mudar o e-mail, rode o script de novo (um
teste confere que as prévias estão atualizadas). Não chama o Xano nem o
SendGrid.
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CODE = "482913"

# Função do Xano → prévia gerada.
EMAILS = {
    "xano/function/signup/send_confirmation_code.xs": "docs/emails/confirmacao-cadastro.html",
    "xano/function/password_recovery/send_recovery_code.xs": "docs/emails/redefinicao-senha.html",
}

_BLOCK = r'var \${name} \{{\s*value = """\n(?P<body>.*?)\n\s*"""'


def template(source: str, name: str) -> str:
    """Texto do bloco ``\"\"\"`` da variável ``$name``, sem o recuo do .xs."""
    match = re.search(_BLOCK.format(name=re.escape(name)), source, re.DOTALL)
    if match is None:
        raise ValueError(f"bloco de ${name} não encontrado")
    return textwrap.dedent(match.group("body"))


def render_html(source: str, code: str = SAMPLE_CODE) -> str:
    """HTML do e-mail com o código, como a função monta (substr + replace)."""
    return (
        template(source, "html_template")
        .replace("{{CODIGO_INICIO}}", code[0:2])
        .replace("{{CODIGO_MEIO}}", code[2:3])
        .replace("{{CODIGO_FIM}}", code[3:6])
    )


def render_text(source: str, code: str = SAMPLE_CODE) -> str:
    """Versão em texto simples do e-mail com o código."""
    return template(source, "message").replace("{{CODIGO}}", code)


def main() -> int:
    for xs, preview in EMAILS.items():
        source = (ROOT / xs).read_text(encoding="utf-8")
        target = ROOT / preview
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_html(source) + "\n", encoding="utf-8", newline="\n")
        print(f"{preview} gerado a partir de {xs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
