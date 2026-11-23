"""Cache dos dados públicos de doações no servidor do Reflex (change
navegacao-celular).

O plano grátis do Xano aceita 10 pedidos a cada 20 s para o site inteiro.
Com várias pessoas navegando ao mesmo tempo, as mesmas consultas públicas
(contagem, recentes, busca, detalhe e, desde a change correcoes-finais, o
perfil de quem doa) se repetiam a cada página. Aqui elas
ficam guardadas por PUBLIC_CACHE_SECONDS, iguais para todos:

- só dados públicos (o que qualquer visitante vê sem login); nada com token,
  e-mail ou dado pessoal;
- uma falha não fica guardada (a próxima página tenta de novo);
- cada chamada recebe uma cópia, para nenhuma página alterar o guardado;
- publicar, editar, mudar status ou apagar uma doação, e salvar o perfil ou a
  foto de perfil, limpa tudo (`invalidate_donations()`), para a pessoa ver a
  mudança na hora.
"""

from __future__ import annotations

import copy
import time
from collections.abc import Awaitable, Callable, Hashable
from typing import Any, TypeVar

PUBLIC_CACHE_SECONDS = 60.0
# Espaços do cache (todos de doações públicas).
COUNT = "contagem"
RECENT = "recentes"
SEARCH = "busca"
DETAIL = "detalhe"
# Perfil de quem doa, por doação e página (change correcoes-finais).
DONOR = "quem-doa"
DONATION_NAMESPACES = (COUNT, RECENT, SEARCH, DETAIL, DONOR)

T = TypeVar("T")
_entries: dict[tuple[str, Hashable], tuple[float, Any]] = {}


async def cached(namespace: str, key: Hashable, loader: Callable[[], Awaitable[T]]) -> T:
    """O valor guardado de (namespace, key) se ainda valer; senão, chama o
    `loader`, guarda o resultado (só se der certo) e devolve uma cópia."""
    entry = _entries.get((namespace, key))
    if entry is not None and time.monotonic() - entry[0] < PUBLIC_CACHE_SECONDS:
        return copy.deepcopy(entry[1])
    value = await loader()
    _entries[(namespace, key)] = (time.monotonic(), value)
    return copy.deepcopy(value)


def invalidate_donations() -> None:
    """Depois de publicar, editar, mudar status ou apagar uma doação: a
    contagem, as recentes, a busca e os detalhes podem ter mudado."""
    for key in [key for key in _entries if key[0] in DONATION_NAMESPACES]:
        del _entries[key]


def clear() -> None:
    """Esvazia o cache (usado pelos testes)."""
    _entries.clear()
