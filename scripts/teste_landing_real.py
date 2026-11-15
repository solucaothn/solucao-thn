"""Verificação da change landing-nova contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e a variável XANO_API_URL definida no ambiente):

    python scripts/teste_landing_real.py

Só lê endpoints públicos: não pede login, não cria nem altera dados. Imprime
só o cenário, o status HTTP, os números das contagens, a quantidade de
categorias e OK/FALHOU; nunca corpos de resposta.

Cenários:
  LN1: GET catalog/donations/count sem token traz `count` e `completed`
       inteiros e não negativos, e nenhum outro campo.
  LN2: GET catalog/categories traz uma lista não vazia de categorias com id
       e nome (as opções do seletor da busca da home).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx

# Reaproveita os auxiliares do teste do chat (mesma pasta scripts/).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from teste_chat_real import base_url, json_ou_none, registrar, resumo  # noqa: E402

PAUSA_SEGUNDOS = float(os.getenv("TESTE_LANDING_PAUSA", "1.5"))


def contagem_valida(valor: object) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool) and valor >= 0


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    api = base_url("XANO_API_URL")

    with httpx.Client(timeout=httpx.Timeout(20.0)) as cliente:
        time.sleep(PAUSA_SEGUNDOS)
        r = cliente.get(f"{api}/catalog/donations/count")
        dados = json_ou_none(r)
        chaves = sorted(dados) if isinstance(dados, dict) else []
        ok = (
            r.status_code == 200
            and chaves == ["completed", "count"]
            and contagem_valida(dados.get("count"))
            and contagem_valida(dados.get("completed"))
        )
        detalhe = (
            f"HTTP {r.status_code}, count={dados.get('count')}, completed={dados.get('completed')}"
            if isinstance(dados, dict)
            else f"HTTP {r.status_code}, corpo não é objeto"
        )
        registrar("LN1. Contagem com count e completed", ok, detalhe, r)

        time.sleep(PAUSA_SEGUNDOS)
        r = cliente.get(f"{api}/catalog/categories")
        dados = json_ou_none(r)
        validas = [
            c for c in (dados if isinstance(dados, list) else [])
            if isinstance(c, dict) and isinstance(c.get("id"), int) and isinstance(c.get("name"), str)
        ]
        registrar(
            "LN2. Categorias para o seletor da busca",
            r.status_code == 200 and bool(validas),
            f"HTTP {r.status_code}, {len(validas)} categoria(s) válida(s)",
            r,
        )

    resumo()


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido.")
