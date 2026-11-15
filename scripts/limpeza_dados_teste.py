"""Limpeza das doações de teste no Xano real, uma conta por vez.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e as variáveis XANO_API_URL e XANO_AUTH_API_URL
definidas no ambiente):

    python scripts/limpeza_dados_teste.py           # só lista, não apaga nada
    python scripts/limpeza_dados_teste.py --apagar  # lista e oferece apagar

Para cada conta, pede e-mail e senha (mantidos só em memória) e lista as
doações de “Minhas doações”: id, título, status e data de criação. No fim de
cada conta, pergunta se quer limpar outra.

Com --apagar, pergunta quais ids apagar (separados por vírgula ou espaço, ou
“todas”), pede a confirmação digitando APAGAR e apaga cada uma pelo mesmo
endpoint do site (DELETE /catalog/donations, que também apaga as fotos e as
conversas do chat da doação). Depois confere que o detalhe responde 404.

Apagar não tem volta. Não imprime tokens, senhas nem e-mails.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

# Reaproveita os auxiliares do teste do chat (mesma pasta scripts/).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from teste_chat_real import base_url, json_ou_none, login  # noqa: E402

PAUSA_SEGUNDOS = 1.5
MAX_PAGINAS = 50
CONFIRMACAO = "APAGAR"


def data_legivel(valor: object) -> str:
    """O created_at do Xano vem em milissegundos desde 1970."""
    if not isinstance(valor, (int, float)) or isinstance(valor, bool):
        return "-"
    try:
        return datetime.fromtimestamp(valor / 1000).strftime("%d/%m/%Y %H:%M")
    except (OverflowError, OSError, ValueError):
        return "-"


def listar_doacoes(cliente: httpx.Client, api: str, headers: dict) -> list[dict] | None:
    """Todas as páginas de “Minhas doações”. None se a leitura falhar."""
    doacoes: list[dict] = []
    pagina = 1
    while pagina <= MAX_PAGINAS:
        time.sleep(PAUSA_SEGUNDOS)
        r = cliente.get(f"{api}/catalog/donations/mine", params={"page": pagina}, headers=headers)
        dados = json_ou_none(r)
        if r.status_code != 200 or not isinstance(dados, dict) or not isinstance(dados.get("items"), list):
            print(f"  Não foi possível ler Minhas doações (HTTP {r.status_code}).")
            return None
        doacoes.extend(i for i in dados["items"] if isinstance(i, dict) and isinstance(i.get("id"), int))
        total_paginas = dados.get("page_total")
        if not isinstance(total_paginas, int) or pagina >= total_paginas:
            break
        pagina += 1
    return doacoes


def imprimir(doacoes: list[dict]) -> None:
    if not doacoes:
        print("  Nenhuma doação nesta conta.")
        return
    print(f"  {len(doacoes)} doação(ões):")
    print(f"  {'id':>6}  {'status':<12} {'criada em':<16}  título")
    for d in sorted(doacoes, key=lambda d: d["id"]):
        titulo = str(d.get("title") or "").replace("\n", " ")
        if len(titulo) > 60:
            titulo = titulo[:57] + "..."
        print(f"  {d['id']:>6}  {str(d.get('status') or '-'):<12} {data_legivel(d.get('created_at')):<16}  {titulo}")


def escolher_ids(doacoes: list[dict]) -> list[int]:
    existentes = {d["id"] for d in doacoes}
    while True:
        resposta = input('\n  Ids para apagar (vírgula ou espaço), "todas" ou Enter para nenhuma: ').strip()
        if not resposta:
            return []
        if resposta.casefold() == "todas":
            return sorted(existentes)
        try:
            ids = sorted({int(p) for p in resposta.replace(",", " ").split()})
        except ValueError:
            print("  Use só números, separados por vírgula ou espaço.")
            continue
        fora = [i for i in ids if i not in existentes]
        if fora:
            print(f"  Estes ids não estão na lista desta conta: {', '.join(map(str, fora))}.")
            continue
        return ids


def apagar(cliente: httpx.Client, api: str, headers: dict, ids: list[int]) -> None:
    for doacao_id in ids:
        time.sleep(PAUSA_SEGUNDOS)
        r = cliente.delete(f"{api}/catalog/donations", params={"donation_id": doacao_id}, headers=headers)
        dados = json_ou_none(r)
        apagada = r.status_code == 200 and isinstance(dados, dict) and dados.get("deleted") is True
        if not apagada:
            print(f"  [FALHOU] id {doacao_id}: DELETE HTTP {r.status_code}")
            continue
        time.sleep(PAUSA_SEGUNDOS)
        detalhe = cliente.get(f"{api}/catalog/donations/detail", params={"donation_id": doacao_id})
        ok = detalhe.status_code == 404
        print(
            f"  [{'OK' if ok else 'ATENÇÃO'}] id {doacao_id}: apagada; "
            f"detalhe HTTP {detalhe.status_code}{'' if ok else ' (esperado 404)'}"
        )


def limpar_conta(cliente: httpx.Client, api: str, auth: str, pode_apagar: bool) -> None:
    try:
        conta = login(cliente, auth, "a limpar")
    except SystemExit as erro:
        # O login do teste do chat encerra o script quando falha; aqui só
        # avisa e deixa tentar outra conta.
        print(f"  {erro}")
        return

    doacoes = listar_doacoes(cliente, api, conta.headers)
    if doacoes is None:
        return
    imprimir(doacoes)
    if not pode_apagar or not doacoes:
        if not pode_apagar:
            print("  Modo só leitura: nada foi apagado (use --apagar para apagar).")
        return

    ids = escolher_ids(doacoes)
    if not ids:
        print("  Nada a apagar.")
        return
    print(f"\n  Serão apagadas {len(ids)} doação(ões): {', '.join(map(str, ids))}.")
    print("  Isso apaga também as fotos e as conversas do chat delas, e não tem volta.")
    if input(f"  Digite {CONFIRMACAO} para confirmar: ").strip() != CONFIRMACAO:
        print("  Confirmação não recebida. Nada foi apagado.")
        return
    apagar(cliente, api, conta.headers, ids)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lista e, com --apagar, apaga doações de teste.")
    parser.add_argument("--apagar", action="store_true", help="oferece apagar as doações listadas")
    args = parser.parse_args()

    api = base_url("XANO_API_URL")
    auth = base_url("XANO_AUTH_API_URL")
    print("Modo: " + ("listar e apagar" if args.apagar else "só listar (nada é apagado)"))

    with httpx.Client(timeout=httpx.Timeout(30.0)) as cliente:
        while True:
            limpar_conta(cliente, api, auth, args.apagar)
            if input("\nLimpar outra conta? (s/N): ").strip().casefold() not in {"s", "sim"}:
                break


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nInterrompido.")
