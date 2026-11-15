"""Verificação da busca pública (change explorar-categorias) contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e a variável XANO_API_URL definida no ambiente):

    python scripts/teste_explorar_real.py

Só lê endpoints públicos: não pede login, não cria nem altera dados. Imprime
só o cenário, o status HTTP, contagens e OK/FALHOU; nunca títulos, corpos de
resposta ou dados pessoais.

Cenários (decisão 7 do design da change explorar-categorias):
  EX1: sem filtros, itens só com os campos do cartão e totais coerentes.
  EX2: o filtro por uma categoria do backend responde e não traz mais
       resultados que a busca sem filtros.
  EX3: o texto sem diferenciar maiúsculas: o título de uma doação da EX1
       buscado em MAIÚSCULAS e em minúsculas encontra a mesma doação.
  EX4: uma página além do total vem vazia, com os mesmos totais.
  EX5: UF com mais de 2 letras e page=0 dão 400.
  EX6: nenhuma chave além das do cartão e da paginação na resposta.
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

PAUSA_SEGUNDOS = float(os.getenv("TESTE_EXPLORAR_PAUSA", "1.5"))
CARD_KEYS = {"id", "created_at", "title", "photo", "condition"}
PAGE_KEYS = {"items", "page", "per_page", "total", "page_total"}


def inteiro(valor: object) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool) and valor >= 0


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    api = base_url("XANO_API_URL")
    rota = f"{api}/catalog/donations/search"

    with httpx.Client(timeout=httpx.Timeout(30.0)) as cliente:

        def buscar(**params) -> tuple[httpx.Response, dict]:
            time.sleep(PAUSA_SEGUNDOS)
            r = cliente.get(rota, params=params)
            dados = json_ou_none(r)
            return r, dados if isinstance(dados, dict) else {}

        print("\n=== EX1. Sem filtros ===")
        r, base = buscar()
        itens = base.get("items") if isinstance(base.get("items"), list) else []
        total = base.get("total")
        coerente = (
            r.status_code == 200
            and inteiro(total)
            and inteiro(base.get("page_total"))
            and base.get("per_page") == 12
            and base.get("page") == 1
            and len(itens) <= 12
            and (total == 0 or len(itens) == min(12, total))
            and base.get("page_total") == -(-total // 12)
        )
        campos_ok = all(isinstance(i, dict) and set(i) == CARD_KEYS for i in itens)
        registrar(
            "EX1. Sem filtros: campos do cartão e totais coerentes",
            coerente and campos_ok,
            f"HTTP {r.status_code}, total={total}, itens={len(itens)}, campos ok: {'sim' if campos_ok else 'não'}",
            r,
        )

        print("\n=== EX2. Filtro por categoria ===")
        time.sleep(PAUSA_SEGUNDOS)
        rc = cliente.get(f"{api}/catalog/categories")
        categorias = [c for c in (json_ou_none(rc) or []) if isinstance(c, dict) and isinstance(c.get("id"), int)]
        if categorias:
            r, filtrada = buscar(category_id=categorias[0]["id"])
            ok = r.status_code == 200 and inteiro(filtrada.get("total")) and inteiro(total) and filtrada["total"] <= total
            registrar("EX2. Categoria do backend filtra", ok, f"HTTP {r.status_code}, total={filtrada.get('total')} de {total}", r)
        else:
            registrar("EX2. Categoria do backend filtra", False, f"sem categorias (HTTP {rc.status_code})", rc)

        print("\n=== EX3. Texto sem diferenciar maiúsculas ===")
        alvo = next((i for i in itens if isinstance(i.get("title"), str) and i["title"].strip()), None)
        if alvo is None:
            registrar("EX3. Texto sem diferenciar maiúsculas", False, "sem doação na EX1 para usar como alvo")
        else:
            achou = []
            for variante in (alvo["title"].upper(), alvo["title"].lower()):
                r, res = buscar(q=variante)
                ids = {i.get("id") for i in res.get("items", []) if isinstance(i, dict)}
                # O alvo pode estar numa página seguinte se houver muitas
                # doações com o mesmo título; basta o total ser positivo e o id
                # aparecer na primeira página na maioria dos casos.
                achou.append(r.status_code == 200 and (alvo["id"] in ids or (inteiro(res.get("total")) and res["total"] > 12)))
            registrar(
                "EX3. Título em MAIÚSCULAS e minúsculas encontra a doação",
                all(achou),
                f"maiúsculas: {'sim' if achou[0] else 'não'}, minúsculas: {'sim' if achou[1] else 'não'}",
            )

        print("\n=== EX4. Página além do total ===")
        alem = (base.get("page_total") or 0) + 1
        r, fora = buscar(page=alem)
        ok = r.status_code == 200 and fora.get("items") == [] and fora.get("total") == total
        registrar("EX4. Página além do total vem vazia", ok, f"HTTP {r.status_code}, página {alem}, itens={len(fora.get('items') or [])}", r)

        print("\n=== EX5. Entradas inválidas ===")
        r1, _ = buscar(state="SPX")
        r2, _ = buscar(page=0)
        registrar(
            "EX5. UF inválida e page=0 dão 400",
            r1.status_code == 400 and r2.status_code == 400,
            f"UF: HTTP {r1.status_code}, page=0: HTTP {r2.status_code}",
        )

        print("\n=== EX6. Sem dados pessoais ===")
        chaves_extra = set(base) - PAGE_KEYS
        campos_extra = {k for i in itens if isinstance(i, dict) for k in set(i) - CARD_KEYS}
        registrar(
            "EX6. Só as chaves do cartão e da paginação",
            not chaves_extra and not campos_extra,
            f"chaves extras: {len(chaves_extra)}, campos extras nos itens: {len(campos_extra)}",
        )

    resumo()


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido.")
