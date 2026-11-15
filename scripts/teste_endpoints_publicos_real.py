"""Verificação da change endpoints-publicos contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e a variável XANO_AUTH_API_URL definida no ambiente):

    python scripts/teste_endpoints_publicos_real.py --antes  # antes de apagar no painel
    python scripts/teste_endpoints_publicos_real.py          # depois de apagar

Não pede login e não leva credenciais. Cada pedido usa uma entrada que falha
mesmo com o endpoint no ar (corpo vazio, sem token, senhas diferentes), então
o script não envia e-mail, não gera token, não emite sessão, não troca senha
e não cria dados, antes ou depois da remoção. Imprime só o cenário, o status
HTTP e OK/FALHOU; nunca o corpo das respostas.

Cenários (decisão 4 do design da change endpoints-publicos):
  EP1 a EP4: os endpoints removidos. Com --antes, ainda existem (status
             diferente de 404); depois, respondem 404.
  EP5 a EP7: os endpoints que ficam continuam existindo (diferente de 404)
             nos dois modos.
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

# (cenário, método, rota, kwargs do pedido). Nenhum pedido leva token.
REMOVIDOS = [
    ("EP1. POST message/send_welcome_email sem user_id", "POST", "/message/send_welcome_email", {"json": {}}),
    ("EP2. GET reset/request-reset-link sem e-mail", "GET", "/reset/request-reset-link", {}),
    ("EP3. POST reset/magic-link-login sem token nem e-mail", "POST", "/reset/magic-link-login", {"json": {}}),
    (
        "EP4. POST reset/update_password sem sessão e com senhas diferentes",
        "POST",
        "/reset/update_password",
        {"json": {"password": "naoUsada1", "confirm_password": "outraSenha2"}},
    ),
]
PRESERVADOS = [
    ("EP5. POST auth/login com corpo vazio", "POST", "/auth/login"),
    ("EP6a. POST reset/request_code com corpo vazio", "POST", "/reset/request_code"),
    ("EP6b. POST reset/verify_code com corpo vazio", "POST", "/reset/verify_code"),
    ("EP6c. POST reset/confirm_password com corpo vazio", "POST", "/reset/confirm_password"),
    ("EP7. POST auth/signup com corpo vazio", "POST", "/auth/signup"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Confere os endpoints removidos e os preservados.")
    parser.add_argument(
        "--antes",
        action="store_true",
        help="registra o estado antes da remoção (os endpoints ainda existem)",
    )
    args = parser.parse_args()
    auth = base_url("XANO_AUTH_API_URL")

    print("Modo: " + ("antes da remoção" if args.antes else "depois da remoção"))
    with httpx.Client(timeout=httpx.Timeout(20.0)) as cliente:

        def pedir(metodo: str, rota: str, **kwargs) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.request(metodo, f"{auth}{rota}", **kwargs)

        print("\n=== Endpoints removidos ===")
        for cenario, metodo, rota, kwargs in REMOVIDOS:
            r = pedir(metodo, rota, **kwargs)
            if args.antes:
                ok = r.status_code != 404
                esperado = "ainda existe (diferente de 404)"
            else:
                ok = r.status_code == 404
                esperado = "404"
            registrar(cenario, ok, f"HTTP {r.status_code}, esperado: {esperado}")

        print("\n=== Endpoints preservados ===")
        for cenario, metodo, rota in PRESERVADOS:
            r = pedir(metodo, rota, json={})
            registrar(cenario, r.status_code != 404, f"HTTP {r.status_code}, esperado: diferente de 404")

    resumo()


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido.")
