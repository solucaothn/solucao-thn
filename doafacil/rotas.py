"""Leitura dos parâmetros da página pelo `router.url` (a API atual do Reflex;
o `router.page` está obsoleto desde a 0.8.1 e sai na 1.0).

O `router.url.path` traz o caminho que a pessoa abriu (por exemplo
`/doacao/17/quem-doa`), e o `router.url.query_parameters`, a query string.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import unquote


def path_segment_after(router: Any, segment: str) -> str:
    """O trecho do caminho logo depois de `segment`, ou "" se não houver.

    `path_segment_after(router, "doacao")` dá "17" em `/doacao/17` e em
    `/doacao/17/quem-doa`.
    """
    path = str(getattr(getattr(router, "url", None), "path", "") or "")
    parts = [part for part in path.split("/") if part]
    try:
        index = parts.index(segment)
    except ValueError:
        return ""
    return unquote(parts[index + 1]) if index + 1 < len(parts) else ""


def query_parameter(router: Any, name: str) -> str:
    """Um parâmetro da query string, ou "" se não houver."""
    parameters = getattr(getattr(router, "url", None), "query_parameters", None) or {}
    value = parameters.get(name, "")
    return value if isinstance(value, str) else ""


# Voltar à origem depois do login (change acabamento) -------------------------

# Telas do fluxo de autenticação: nunca são destino do `next`.
AUTH_PATHS = ("/login", "/cadastro", "/recuperar-senha", "/verificar-email", "/nova-senha")
NEXT_MAX_LENGTH = 512


def safe_next(value: Any) -> str:
    """O caminho interno de `value`, ou "" se ele não for seguro.

    Só aceita um caminho do próprio site: começa com uma única “/”, sem
    esquema nem host, sem “\”, espaços ou caracteres de controle, com até
    NEXT_MAX_LENGTH caracteres e fora das telas de autenticação. Assim o
    `next` nunca leva a um endereço externo (open redirect).
    """
    from urllib.parse import urlsplit

    if not isinstance(value, str) or not value or len(value) > NEXT_MAX_LENGTH:
        return ""
    if not value.startswith("/") or value.startswith("//") or "\\" in value:
        return ""
    if any(ord(char) < 0x21 or ord(char) == 0x7F for char in value):
        return ""
    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        return ""
    path = parts.path.rstrip("/") or "/"
    if any(path == auth or path.startswith(auth + "/") for auth in AUTH_PATHS):
        return ""
    return value


def current_path(router: Any) -> str:
    """O caminho da página atual, com a query, pelo router.url."""
    url = getattr(router, "url", None)
    path = str(getattr(url, "path", "") or "")
    query = str(getattr(url, "query", "") or "")
    return f"{path}?{query}" if path and query else path


def login_url(next_path: Any) -> str:
    """`/login?next=<caminho>` quando o caminho é seguro; senão, `/login`."""
    from urllib.parse import quote

    safe = safe_next(next_path)
    return f"/login?next={quote(safe, safe='/')}" if safe else "/login"


def signup_url(next_path: Any) -> str:
    """`/cadastro?next=<caminho>` quando o caminho é seguro; senão, `/cadastro`."""
    from urllib.parse import quote

    safe = safe_next(next_path)
    return f"/cadastro?next={quote(safe, safe='/')}" if safe else "/cadastro"


def login_redirect(state: Any):
    """Vai ao login levando a página atual em `next` (estado sem router, como
    nos testes, vai ao /login puro)."""
    import reflex as rx

    return rx.redirect(login_url(current_path(getattr(state, "router", None))))
