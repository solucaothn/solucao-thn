"""Roteiro de verificação manual do e-mail verificado e dos contadores contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e as variáveis XANO_API_URL e XANO_AUTH_API_URL
definidas no ambiente):

    python scripts/teste_perfil_credibilidade_real.py

Pede o e-mail e a senha de uma conta criada pelo signup_verify (com o selo
verdadeiro) e o ID de uma doação DISPONÍVEL dessa conta. As credenciais ficam
só em memória. O script não grava nada em arquivo e não imprime nomes,
e-mails, ids nem corpos de resposta: só status HTTP, chaves, tipos, contagens
e sim/não. Os e-mails são comparados só em memória.

O que ele altera: o PC9 faz um PATCH auth/profile com os valores atuais do
perfil (nome, cidade, estado e Sobre) e com email_verified: false, para provar
que o selo não muda. Os dados ficam iguais, exceto um Sobre nulo, que volta
como texto vazio (o PATCH sempre grava o Sobre).

Cenários PC1 a PC10 (tarefa 3.1 da change perfil-credibilidade).
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

import httpx

# Reaproveita os auxiliares do teste do chat (mesma pasta scripts/).
from teste_chat_real import (
    TIMEOUT,
    Conta,
    base_url,
    json_ou_none,
    login,
    registrar,
    resumo,
)

PAUSA_SEGUNDOS = float(os.getenv("TESTE_CREDIBILIDADE_PAUSA", "2.5"))
CHAVES_COUNTS = {"active", "completed"}
CHAVES_PERFIL = {
    "id",
    "created_at",
    "name",
    "email",
    "city",
    "state",
    "about",
    "photo",
    "email_verified",
    "counts",
}
CHAVES_OWNER = {"first_name", "email", "about", "photo", "email_verified"}
CHAVES_DONOR = {
    "first_name",
    "city",
    "state",
    "member_since",
    "about",
    "photo",
    "email_verified",
    "counts",
}


def eh_int(valor: object) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def counts_ok(valor: object) -> bool:
    """Objeto só com active e completed, inteiros não negativos."""
    return (
        isinstance(valor, dict)
        and set(valor) == CHAVES_COUNTS
        and all(eh_int(valor[c]) and valor[c] >= 0 for c in CHAVES_COUNTS)
    )


def obj(dados: object, *caminho: str) -> object:
    for chave in caminho:
        if not isinstance(dados, dict):
            return None
        dados = dados.get(chave)
    return dados


def chaves_em_todos_os_niveis(dados: Any) -> set[str]:
    chaves: set[str] = set()
    if isinstance(dados, dict):
        for chave, valor in dados.items():
            chaves.add(str(chave))
            chaves |= chaves_em_todos_os_niveis(valor)
    elif isinstance(dados, list):
        for item in dados:
            chaves |= chaves_em_todos_os_niveis(item)
    return chaves


def sim(valor: bool) -> str:
    return "sim" if valor else "não"


def main() -> None:
    api = base_url("XANO_API_URL")
    auth = base_url("XANO_AUTH_API_URL")

    with httpx.Client(timeout=TIMEOUT) as cliente:
        conta = login(cliente, auth, "criada pelo signup_verify")
        try:
            doacao_id = int(input("\nID de uma doação DISPONÍVEL dessa conta: ").strip())
        except ValueError:
            sys.exit("O ID da doação precisa ser um inteiro.")

        def pedir(metodo: str, url: str, conta_: Conta | None, **kwargs: Any) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            headers = conta_.headers if conta_ else {}
            return cliente.request(metodo, url, headers=headers, **kwargs)

        print("\n=== Campos novos (PC1 a PC4) ===")

        # PC1. auth/profile: email_verified booleano e counts.
        r_perfil = pedir("GET", f"{auth}/auth/profile", conta)
        perfil = json_ou_none(r_perfil)
        ok = (
            r_perfil.status_code == 200
            and isinstance(perfil, dict)
            and set(perfil) == CHAVES_PERFIL
            and isinstance(perfil.get("email_verified"), bool)
            and counts_ok(perfil.get("counts"))
        )
        registrar(
            "PC1. GET auth/profile → email_verified booleano e counts {active, completed}",
            ok,
            f"HTTP {r_perfil.status_code}",
            r_perfil,
        )
        if r_perfil.status_code != 200 or not isinstance(perfil, dict):
            print("\nSem o perfil não dá para seguir. Encerrando.")
            resumo()
            return

        # PC2. donations/mine: owner.email e owner.email_verified; counts já existiam.
        r_mine = pedir("GET", f"{api}/catalog/donations/mine", conta)
        mine = json_ou_none(r_mine)
        owner = obj(mine, "owner")
        ok = (
            r_mine.status_code == 200
            and isinstance(owner, dict)
            and set(owner) == CHAVES_OWNER
            and isinstance(owner.get("email"), str)
            and isinstance(owner.get("email_verified"), bool)
            and counts_ok(obj(mine, "counts"))
        )
        registrar(
            "PC2. GET donations/mine → owner.email, owner.email_verified booleano e counts",
            ok,
            f"HTTP {r_mine.status_code}",
            r_mine,
        )

        # PC3. donations/donor: donor.email_verified e donor.counts.
        r_donor = pedir("GET", f"{api}/catalog/donations/donor", None, params={"donation_id": doacao_id})
        donor_resp = json_ou_none(r_donor)
        donor = obj(donor_resp, "donor")
        ok = (
            r_donor.status_code == 200
            and isinstance(donor, dict)
            and set(donor) == CHAVES_DONOR
            and isinstance(donor.get("email_verified"), bool)
            and counts_ok(donor.get("counts"))
        )
        registrar(
            "PC3. GET donations/donor → donor.email_verified booleano e donor.counts",
            ok,
            f"HTTP {r_donor.status_code}",
            r_donor,
        )

        # PC4. donations/detail: donor_email_verified e donor_counts.
        r_detail = pedir("GET", f"{api}/catalog/donations/detail", None, params={"donation_id": doacao_id})
        detail = json_ou_none(r_detail)
        ok = (
            r_detail.status_code == 200
            and isinstance(detail, dict)
            and isinstance(detail.get("donor_email_verified"), bool)
            and counts_ok(detail.get("donor_counts"))
        )
        registrar(
            "PC4. GET donations/detail → donor_email_verified booleano e donor_counts",
            ok,
            f"HTTP {r_detail.status_code}",
            r_detail,
        )

        print("\n=== Coerência (PC5 a PC8) ===")

        # PC5. Os mesmos contadores e o mesmo selo nas quatro respostas.
        contadores = [
            perfil.get("counts"),
            obj(mine, "counts"),
            obj(donor, "counts"),
            obj(detail, "donor_counts"),
        ]
        selos = [
            perfil.get("email_verified"),
            obj(owner, "email_verified"),
            obj(donor, "email_verified"),
            obj(detail, "donor_email_verified"),
        ]
        iguais = all(counts_ok(c) for c in contadores) and all(c == contadores[0] for c in contadores)
        mesmo_selo = all(isinstance(s, bool) for s in selos) and len(set(selos)) == 1
        ativas = obj(contadores[0], "active")
        concluidas = obj(contadores[0], "completed")
        registrar(
            "PC5. Contadores e selo iguais em auth/profile, mine, donor e detail",
            iguais and mesmo_selo and eh_int(ativas) and ativas >= 1,
            f"contadores iguais: {sim(iguais)} (ativas {ativas}, concluídas {concluidas}), "
            f"selo igual: {sim(mesmo_selo)}",
        )

        # PC6. owner.email da mine igual ao e-mail do auth/profile (sem imprimir).
        mesmo_email = (
            isinstance(perfil.get("email"), str)
            and bool(perfil.get("email"))
            and obj(owner, "email") == perfil.get("email")
        )
        registrar("PC6. owner.email da mine igual ao e-mail do auth/profile", mesmo_email, f"igual: {sim(mesmo_email)}")

        # PC7. Nenhum e-mail no donor nem no detail (nem chave “email”, nem '@').
        sem_email = True
        for resposta, dados in ((r_donor, donor_resp), (r_detail, detail)):
            if "email" in chaves_em_todos_os_niveis(dados) or "@" in resposta.text:
                sem_email = False
        registrar("PC7. Nenhum e-mail no donor nem no detail", sem_email, f"sem e-mail: {sim(sem_email)}")

        # PC8. A conta criada pelo signup_verify tem o selo verdadeiro.
        selo_antes = perfil.get("email_verified")
        registrar(
            "PC8. A conta criada pelo signup_verify tem email_verified verdadeiro",
            selo_antes is True,
            f"verdadeiro: {sim(selo_antes is True)}",
        )

        print("\n=== Proteção (PC9 e PC10) ===")

        # PC9. PATCH com email_verified: false não muda o selo.
        dados = {
            "name": perfil.get("name"),
            "city": perfil.get("city"),
            "state": perfil.get("state"),
            "about": perfil.get("about") or "",
            "email_verified": False,
        }
        r_patch = pedir("PATCH", f"{auth}/auth/profile", conta, json=dados)
        r_depois = pedir("GET", f"{auth}/auth/profile", conta)
        selo_depois = obj(json_ou_none(r_depois), "email_verified")
        sem_selo_no_patch = "email_verified" not in (json_ou_none(r_patch) or {})
        registrar(
            "PC9. PATCH auth/profile com email_verified: false não muda o selo",
            r_patch.status_code == 200 and r_depois.status_code == 200 and selo_depois == selo_antes and sem_selo_no_patch,
            f"HTTP {r_patch.status_code} / {r_depois.status_code}, selo igual: {sim(selo_depois == selo_antes)}, "
            f"PATCH sem email_verified na resposta: {sim(sem_selo_no_patch)}",
            r_patch if r_patch.status_code != 200 else r_depois,
        )

        # PC10. Sem token → 401 no profile e na mine.
        r1 = pedir("GET", f"{auth}/auth/profile", None)
        r2 = pedir("GET", f"{api}/catalog/donations/mine", None)
        registrar(
            "PC10. Sem token → 401 no auth/profile e na donations/mine",
            r1.status_code == 401 and r2.status_code == 401,
            f"HTTP {r1.status_code} / {r2.status_code}",
            r1 if r1.status_code != 401 else r2,
        )

    resumo()


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido.")
