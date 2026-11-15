"""Verificação da change esquema-xano contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e as variáveis XANO_API_URL e XANO_AUTH_API_URL
definidas no ambiente):

    python scripts/teste_esquema_xano_real.py

Só lê: não cria, não altera nem apaga dados e não envia e-mail. O ES3 pede
e-mail e senha de uma conta (mantidos só em memória). Imprime só o cenário,
status HTTP, contagens e OK/FALHOU; nunca corpos, URLs, tokens, nomes ou
e-mails.

Cenários (decisão 5 do design da change esquema-xano):
  ES1: GET catalog/donations/contact-email sem token responde 401 (a rota
       existe e continua exigindo sessão).
  ES2: as doações recentes e o detalhe de cada uma trazem as fotos só como
       URL, nunca nulas ou vazias.
  ES3: com login, auth/profile traz email_verified como verdadeiro ou falso.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx

# Reaproveita os auxiliares do teste do chat (mesma pasta scripts/).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from teste_chat_real import base_url, json_ou_none, login, registrar, resumo  # noqa: E402

PAUSA_SEGUNDOS = float(os.getenv("TESTE_ESQUEMA_PAUSA", "1.5"))


def foto_valida(valor: object) -> bool:
    return isinstance(valor, str) and valor.startswith("http")


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    api = base_url("XANO_API_URL")
    auth = base_url("XANO_AUTH_API_URL")

    with httpx.Client(timeout=httpx.Timeout(30.0)) as cliente:

        def pedir(metodo: str, url: str, **kwargs) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.request(metodo, url, **kwargs)

        print("\n=== ES1. Rota do contact-email ===")
        r = pedir("GET", f"{api}/catalog/donations/contact-email", params={"donation_id": 1})
        registrar(
            "ES1. contact-email sem token → 401",
            r.status_code == 401,
            f"HTTP {r.status_code}",
            r,
        )

        print("\n=== ES2. Fotos das doações recentes ===")
        r = pedir("GET", f"{api}/catalog/donations/recent")
        recentes = json_ou_none(r)
        ids = [
            item["id"]
            for item in (recentes if isinstance(recentes, list) else [])
            if isinstance(item, dict) and isinstance(item.get("id"), int)
        ]
        total_fotos = 0
        invalidas = 0
        detalhes_ok = 0
        for doacao_id in ids:
            d = pedir("GET", f"{api}/catalog/donations/detail", params={"donation_id": doacao_id})
            fotos = (json_ou_none(d) or {}).get("photos") if d.status_code == 200 else None
            if not isinstance(fotos, list):
                continue
            detalhes_ok += 1
            total_fotos += len(fotos)
            invalidas += sum(1 for foto in fotos if not foto_valida(foto))
        registrar(
            "ES2. Fotos do detalhe das recentes só como URL",
            r.status_code == 200 and bool(ids) and detalhes_ok == len(ids) and total_fotos > 0 and invalidas == 0,
            f"recentes: HTTP {r.status_code}, {len(ids)} doação(ões), {detalhes_ok} detalhe(s) lidos, "
            f"{total_fotos} foto(s), {invalidas} nula(s) ou inválida(s)",
            r,
        )

        print("\n=== ES3. E-mail verificado no perfil ===")
        conta = login(cliente, auth, "para o ES3")
        r = pedir("GET", f"{auth}/auth/profile", headers=conta.headers)
        dados = json_ou_none(r)
        valor = dados.get("email_verified") if isinstance(dados, dict) else None
        registrar(
            "ES3. auth/profile traz email_verified verdadeiro ou falso",
            r.status_code == 200 and isinstance(valor, bool),
            f"HTTP {r.status_code}, tipo: {type(valor).__name__}",
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
