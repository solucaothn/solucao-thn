"""Confere, no Xano real, o limite de título do POST catalog/donations/publish
(change correcoes-finais). Só envia entradas inválidas: nunca cria doação.

Fica fora de tests/ de propósito: o unittest não deve executá-lo. Rode depois
do push do publish_POST.xs.

Uso (com o .venv ativo e as variáveis XANO_API_URL e XANO_AUTH_API_URL
definidas no ambiente):

    python scripts/teste_publicar_limites_real.py

Pede e-mail e senha de uma conta com cidade e estado no perfil (mantidos só
em memória). Imprime só o cenário, o status HTTP e OK/FALHOU; nunca token,
e-mail ou corpo de resposta.

Como nunca cria doação: as duas requisições vão SEM fotos. O Xano valida os
campos antes do stack, então:
  P1: título com 101 caracteres → 400 pelo título, antes da regra das fotos.
      Se vier a mensagem “Adicione pelo menos uma foto”, o limite ainda não
      está no Xano (o push não foi feito) e o cenário falha.
  P2: controle, título com 100 caracteres → o título passa e o 400 vem da
      regra das fotos (“Adicione pelo menos uma foto”).
Nos dois casos a precondição das fotos impede a criação da doação.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

# Reaproveita os auxiliares do teste do chat (mesma pasta scripts/).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from teste_chat_real import base_url, json_ou_none, login, registrar, resultados, resumo  # noqa: E402

PAUSA_SEGUNDOS = 2.5
MENSAGEM_FOTOS = "Adicione pelo menos uma foto"
TITULO_LONGO = "a" * 101
TITULO_NO_LIMITE = "a" * 100


def publicar_sem_fotos(cliente: httpx.Client, api: str, headers: dict, categoria: int, titulo: str) -> httpx.Response:
    """Multipart como o site envia, mas sem nenhum arquivo em photos[]."""
    campos = {
        "category_id": str(categoria),
        "title": titulo,
        "description": "Teste de limite, sem fotos: não cria doação.",
        "condition": "Bom",
        "delivery_method": "A combinar",
        "contact_preference": "Chat do DoaFácil",
    }
    time.sleep(PAUSA_SEGUNDOS)
    return cliente.post(
        f"{api}/catalog/donations/publish",
        files=[(chave, (None, valor)) for chave, valor in campos.items()],
        headers=headers,
    )


def fala_das_fotos(resposta: httpx.Response) -> bool:
    return MENSAGEM_FOTOS in resposta.text


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    api = base_url("XANO_API_URL")
    auth = base_url("XANO_AUTH_API_URL")

    with httpx.Client(timeout=httpx.Timeout(30.0)) as cliente:
        conta = login(cliente, auth, "do teste")

        # Uma categoria real (leitura pública), para o resto do corpo ser válido.
        time.sleep(PAUSA_SEGUNDOS)
        rc = cliente.get(f"{api}/catalog/categories")
        categorias = [c for c in (json_ou_none(rc) or []) if isinstance(c, dict) and isinstance(c.get("id"), int)]
        if not categorias:
            sys.exit(f"Não foi possível ler as categorias (HTTP {rc.status_code}).")
        categoria = categorias[0]["id"]

        print("\n=== P1. Título com 101 caracteres ===")
        r = publicar_sem_fotos(cliente, api, conta.headers, categoria, TITULO_LONGO)
        fotos = fala_das_fotos(r)
        registrar(
            "P1. Título com 101 caracteres dá 400 pelo título",
            r.status_code == 400 and not fotos,
            f"HTTP {r.status_code}, recusado pela regra das fotos: {'sim (limite ausente; o push foi feito?)' if fotos else 'não'}",
            r,
        )

        print("\n=== P2. Controle: título com 100 caracteres ===")
        r = publicar_sem_fotos(cliente, api, conta.headers, categoria, TITULO_NO_LIMITE)
        fotos = fala_das_fotos(r)
        registrar(
            "P2. Título com 100 caracteres passa e para nas fotos",
            r.status_code == 400 and fotos,
            f"HTTP {r.status_code}, recusado pela regra das fotos: {'sim' if fotos else 'não'}",
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
