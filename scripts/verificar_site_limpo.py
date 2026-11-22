"""Confere, pelo Xano real, que o site ficou sem os dados de teste.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e a variável XANO_API_URL definida no ambiente):

    python scripts/verificar_site_limpo.py

Só lê endpoints públicos: não pede login, não cria nem altera dados. Imprime
só o cenário, o status HTTP, contagens e OK/FALHOU. Sai com código 1 se algum
cenário falhar.

Cenários (depois de apagar chat_message, chat_conversation, donation_photo,
donation e a categoria “Alimentos”):
  L1: catalog/donations/count com count=0 e completed=0.
  L2: catalog/donations/recent vazio.
  L3: catalog/donations/search sem filtros vazio (items=[], total=0,
      page_total=0).
  L4: catalog/categories carrega (200, lista não vazia) e sem “Alimentos”.
"""

from __future__ import annotations

import os
import sys
import time
import unicodedata
from pathlib import Path

import httpx

# Reaproveita os auxiliares do teste do chat (mesma pasta scripts/).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from teste_chat_real import base_url, json_ou_none, registrar, resultados, resumo  # noqa: E402

PAUSA_SEGUNDOS = float(os.getenv("VERIFICAR_LIMPO_PAUSA", "1.5"))
CATEGORIA_APAGADA = "alimentos"


def normalizado(texto: str) -> str:
    """Minúsculas e sem acentos, para comparar nomes de categoria."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.strip().casefold()


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    api = base_url("XANO_API_URL")

    with httpx.Client(timeout=httpx.Timeout(30.0)) as cliente:

        def ler(rota: str, **params) -> tuple[httpx.Response, object]:
            time.sleep(PAUSA_SEGUNDOS)
            resposta = cliente.get(f"{api}{rota}", params=params)
            return resposta, json_ou_none(resposta)

        print("\n=== L1. Contagem da home ===")
        r, dados = ler("/catalog/donations/count")
        dados = dados if isinstance(dados, dict) else {}
        registrar(
            "L1. count=0 e completed=0",
            r.status_code == 200 and dados.get("count") == 0 and dados.get("completed") == 0,
            f"HTTP {r.status_code}, count={dados.get('count')}, completed={dados.get('completed')}",
            r,
        )

        print("\n=== L2. Doações recentes ===")
        r, dados = ler("/catalog/donations/recent")
        tamanho = len(dados) if isinstance(dados, list) else "não é lista"
        registrar(
            "L2. recent vazio",
            r.status_code == 200 and dados == [],
            f"HTTP {r.status_code}, itens={tamanho}",
            r,
        )

        print("\n=== L3. Busca sem filtros ===")
        r, dados = ler("/catalog/donations/search")
        dados = dados if isinstance(dados, dict) else {}
        itens = dados.get("items")
        registrar(
            "L3. search vazio",
            r.status_code == 200 and itens == [] and dados.get("total") == 0 and dados.get("page_total") == 0,
            f"HTTP {r.status_code}, total={dados.get('total')}, page_total={dados.get('page_total')}, "
            f"itens={len(itens) if isinstance(itens, list) else 'não é lista'}",
            r,
        )

        print("\n=== L4. Categorias ===")
        r, dados = ler("/catalog/categories")
        categorias = [c for c in dados if isinstance(c, dict)] if isinstance(dados, list) else []
        nomes = [normalizado(c["name"]) for c in categorias if isinstance(c.get("name"), str)]
        tem_alimentos = CATEGORIA_APAGADA in nomes
        registrar(
            "L4. categorias carregam, sem “Alimentos”",
            r.status_code == 200 and len(nomes) > 0 and len(nomes) == len(categorias) and not tem_alimentos,
            f"HTTP {r.status_code}, categorias={len(categorias)}, “Alimentos” presente: {'sim' if tem_alimentos else 'não'}",
            r,
        )

    resumo()
    if any(not ok for _, ok in resultados):
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido.")
