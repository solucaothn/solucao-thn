"""Verificação da change endpoints-antigos contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e a variável XANO_API_URL, a do grupo Catalog,
definida no ambiente):

    python scripts/teste_endpoints_antigos_real.py --antes  # antes de apagar no painel
    python scripts/teste_endpoints_antigos_real.py          # depois de apagar

Não pede login e não leva credenciais. Cada pedido usa uma entrada que falha
mesmo com o endpoint no ar (categoria 0, página 0, sem token), então o
script não lista doações, não cria, não edita e não apaga nada, antes ou
depois da remoção. Imprime só o cenário, o status HTTP e OK/FALHOU; nunca o
corpo das respostas (num 2xx inesperado, só a estrutura).

Cenários (decisão 2 do design da change endpoints-antigos):
  EA1 e EA2: o GET e o POST de catalog/donations, removidos. Com --antes,
             ainda existem (status diferente de 404 e de 405); depois,
             respondem 404 ou 405 (o caminho continua existindo para o
             PATCH e o DELETE).
  EA3 a EA6: o PATCH e o DELETE do mesmo caminho, o publish e a busca
             continuam existindo (diferente de 404) nos dois modos.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import httpx

# Reaproveita os auxiliares do teste do chat (mesma pasta scripts/).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from teste_chat_real import base_url, registrar, resumo  # noqa: E402

PAUSA_SEGUNDOS = float(os.getenv("TESTE_ENDPOINTS_PAUSA", "1.5"))
FECHADO = {404, 405}

# (cenário, método, rota, kwargs do pedido). Nenhum pedido leva token.
REMOVIDOS = [
    (
        "EA1. GET catalog/donations com a categoria 0 (inexistente)",
        "GET",
        "/catalog/donations",
        {"params": {"category_id": 0}},
    ),
    ("EA2. POST catalog/donations sem token e com corpo vazio", "POST", "/catalog/donations", {"json": {}}),
]
PRESERVADOS = [
    ("EA3. PATCH catalog/donations sem token", "PATCH", "/catalog/donations", {"json": {}}),
    ("EA4. DELETE catalog/donations sem token", "DELETE", "/catalog/donations", {"params": {"donation_id": 0}}),
    ("EA5. POST catalog/donations/publish sem token", "POST", "/catalog/donations/publish", {"json": {}}),
    ("EA6. GET catalog/donations/search com a página 0", "GET", "/catalog/donations/search", {"params": {"page": 0}}),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Confere os endpoints antigos removidos e os preservados.")
    parser.add_argument(
        "--antes",
        action="store_true",
        help="registra o estado antes da remoção (o GET e o POST ainda existem)",
    )
    args = parser.parse_args()
    catalogo = base_url("XANO_API_URL")

    print("Modo: " + ("antes da remoção" if args.antes else "depois da remoção"))
    with httpx.Client(timeout=httpx.Timeout(20.0)) as cliente:

        def pedir(metodo: str, rota: str, **kwargs) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.request(metodo, f"{catalogo}{rota}", **kwargs)

        print("\n=== Endpoints removidos ===")
        for cenario, metodo, rota, kwargs in REMOVIDOS:
            r = pedir(metodo, rota, **kwargs)
            if args.antes:
                ok = r.status_code not in FECHADO
                esperado = "ainda existe (diferente de 404 e 405)"
            else:
                ok = r.status_code in FECHADO
                esperado = "404 ou 405"
            registrar(cenario, ok, f"HTTP {r.status_code}, esperado: {esperado}", r)

        print("\n=== Endpoints preservados ===")
        for cenario, metodo, rota, kwargs in PRESERVADOS:
            r = pedir(metodo, rota, **kwargs)
            registrar(cenario, r.status_code not in FECHADO, f"HTTP {r.status_code}, esperado: diferente de 404 e 405", r)

    resumo()


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido.")
