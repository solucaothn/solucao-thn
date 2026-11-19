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
