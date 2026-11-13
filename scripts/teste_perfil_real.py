"""Roteiro de verificação manual do perfil público de quem doa contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e a variável XANO_API_URL definida no ambiente):

    python scripts/teste_perfil_real.py

O endpoint é público: o script não pede login nem senha, só os IDs das doações.
Ele não grava nada em arquivo e não imprime nomes, cidades, e-mails, URLs nem
corpos de resposta; só status HTTP, chaves, tipos, contagens e sim/não.
Ele também não cria nem altera dados.

Cenários PP1 a PP10 (decisão 5 do design da change perfil-publico). O PP9 só
roda se for informada uma doação não disponível (reservada ou concluída).
"""

from __future__ import annotations

import math
import os
import re
import sys
import time
from typing import Any

import httpx

# Reaproveita os auxiliares do teste do chat (mesma pasta scripts/).
from teste_chat_real import (
    TIMEOUT,
    base_url,
    json_ou_none,
    registrar,
    resumo,
)

# Pausa entre requisições: fica abaixo do limite de 10 requisições a cada 20 s.
PAUSA_SEGUNDOS = float(os.getenv("TESTE_PERFIL_PAUSA", "2.5"))
POR_PAGINA = 12
# Id que não existe (abaixo do máximo de um int de 32 bits).
ID_INEXISTENTE = 2_000_000_000
MENSAGEM_404 = "Doação não encontrada."

CHAVES_RESPOSTA = {"donor", "items", "page", "per_page", "total", "page_total"}
# O “about” (Sobre) entrou na change editar-perfil e o “photo” (URL da foto
# de perfil) na change foto-perfil: os dois são texto ou nulo.
CHAVES_DONOR = {"first_name", "city", "state", "member_since", "about", "photo"}
CHAVES_ITEM = {"id", "created_at", "title", "photo", "condition"}
# Chaves que não podem aparecer em nenhum nível da resposta.
CHAVES_PROIBIDAS = {
    "owner_id",
    "user_id",
    "user",
    "owner",
    "email",
    "name",
    "full_name",
    "last_name",
    "surname",
    "address",
    "neighborhood",
    "bairro",
    "cep",
    "zip",
    "zip_code",
    "role",
    "password",
    "reset_code",
    "code_hash",
    "status",
}
FORMATO_MEMBRO_DESDE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def eh_int(valor: object) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


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


def itens(dados: Any) -> list[dict]:
    lista = dados.get("items") if isinstance(dados, dict) else None
    if not isinstance(lista, list):
        return []
    return [item for item in lista if isinstance(item, dict)]


def ids_dos_itens(dados: Any) -> list[object]:
    return [item.get("id") for item in itens(dados)]


def chaves_ok(dados: Any) -> tuple[bool, str]:
    if not isinstance(dados, dict):
        return False, "resposta não é objeto"
    if set(dados) != CHAVES_RESPOSTA:
        return False, f"chaves do topo: {sorted(dados)}"
    donor = dados.get("donor")
    if not isinstance(donor, dict) or set(donor) != CHAVES_DONOR:
        return False, f"chaves de donor: {sorted(donor) if isinstance(donor, dict) else type(donor).__name__}"
    for item in itens(dados):
        if set(item) != CHAVES_ITEM:
            return False, f"chaves de um item: {sorted(item)}"
    return True, "só as chaves permitidas"


def tipos_ok(dados: Any) -> tuple[bool, str]:
    if not isinstance(dados, dict) or not isinstance(dados.get("donor"), dict):
        return False, "resposta sem donor"
    donor = dados["donor"]
    problemas = []
    if not isinstance(donor.get("first_name"), str) or not donor["first_name"].strip():
        problemas.append("first_name")
    elif " " in donor["first_name"].strip():
        problemas.append("first_name com mais de uma palavra")
    for campo in ("city", "state", "member_since"):
        if not isinstance(donor.get(campo), str):
            problemas.append(campo)
    if donor.get("about") is not None and not isinstance(donor.get("about"), str):
        problemas.append("about")
    if donor.get("photo") is not None and not isinstance(donor.get("photo"), str):
        problemas.append("photo")
    for campo in ("page", "per_page", "total", "page_total"):
        if not eh_int(dados.get(campo)):
            problemas.append(campo)
    if not isinstance(dados.get("items"), list):
        problemas.append("items")
    for item in itens(dados):
        if not eh_int(item.get("id")) or not eh_int(item.get("created_at")):
            problemas.append("id/created_at de item")
        if not isinstance(item.get("title"), str) or not isinstance(item.get("condition"), str):
            problemas.append("title/condition de item")
        if item.get("photo") is not None and not isinstance(item.get("photo"), str):
            problemas.append("photo de item")
    if problemas:
        return False, "tipos inesperados: " + ", ".join(sorted(set(problemas)))
    return True, "tipos corretos"


def main() -> None:
    api = base_url("XANO_API_URL")

    try:
        donation_id = int(input("ID de uma doação disponível: ").strip())
    except ValueError:
        sys.exit("ID da doação precisa ser um inteiro.")

    texto = input(
        "ID de uma doação NÃO disponível (reservada ou concluída), para o PP9"
        " (Enter para pular): "
    ).strip()
    indisponivel_id: int | None = None
    if texto:
        try:
            indisponivel_id = int(texto)
        except ValueError:
            sys.exit("ID da doação precisa ser um inteiro.")

    with httpx.Client(timeout=TIMEOUT) as cliente:

        def perfil(doacao: int, pagina: int | None = None) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            parametros: dict[str, int] = {"donation_id": doacao}
            if pagina is not None:
                parametros["page"] = pagina
            return cliente.get(f"{api}/catalog/donations/donor", params=parametros)

        def detalhe(doacao: object) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.get(
                f"{api}/catalog/donations/detail", params={"donation_id": doacao}
            )

        print("\n=== Cenários ===")

        # PP1. 200 com só as chaves permitidas (sem page: usa o padrão 1).
        r1 = perfil(donation_id)
        d1 = json_ou_none(r1)
        ok, detalhe_chaves = chaves_ok(d1)
        registrar(
            "PP1. Perfil de doação disponível → 200 com só as chaves permitidas",
            r1.status_code == 200 and ok,
            f"HTTP {r1.status_code}, {detalhe_chaves}",
            r1,
        )
        if r1.status_code != 200 or not isinstance(d1, dict):
            print("\nSem resposta 200 não dá para seguir. Encerrando.")
            resumo()
            return

        # PP2. Tipos dos campos.
        ok, detalhe_tipos = tipos_ok(d1)
        registrar("PP2. Tipos dos campos", ok, detalhe_tipos)

        # PP3. member_since no formato AAAA-MM.
        donor = d1.get("donor") if isinstance(d1.get("donor"), dict) else {}
        membro = donor.get("member_since")
        formato = isinstance(membro, str) and bool(FORMATO_MEMBRO_DESDE.match(membro))
        registrar(
            "PP3. member_since no formato AAAA-MM (sem dia nem horário)",
            formato,
            f"formato correto: {'sim' if formato else 'não'}",
        )

        # PP4. Chaves proibidas ausentes em todos os níveis, e nenhum '@'.
        proibidas = sorted(chaves_em_todos_os_niveis(d1) & CHAVES_PROIBIDAS)
        tem_arroba = "@" in r1.text
        registrar(
            "PP4. Sem chaves proibidas em nenhum nível e sem '@'",
            not proibidas and not tem_arroba,
            "nada encontrado"
            if not proibidas and not tem_arroba
            else f"chaves proibidas: {proibidas}, contém '@': {'sim' if tem_arroba else 'não'}",
        )

        # PP5. Até 12 itens, total e páginas coerentes, ordem decrescente.
        lista = itens(d1)
        total = d1.get("total")
        paginas = d1.get("page_total")
        ids = ids_dos_itens(d1)
        datas = [item.get("created_at") for item in lista]
        coerente = (
            eh_int(total)
            and eh_int(paginas)
            and total >= 1
            and d1.get("page") == 1
            and d1.get("per_page") == POR_PAGINA
            and len(lista) == min(POR_PAGINA, total)
            and paginas == math.ceil(total / POR_PAGINA)
            and len(set(ids)) == len(ids)
        )
        decrescente = all(eh_int(d) for d in datas) and datas == sorted(datas, reverse=True)
        # A doação de origem entra na lista (dúvida 2); só dá para conferir na
        # página 1 quando a pessoa tem até 12 doações disponíveis.
        origem_ok = (not eh_int(total)) or total > POR_PAGINA or donation_id in ids
        registrar(
            "PP5. Até 12 itens, total e páginas coerentes, mais recentes primeiro, origem na lista",
            coerente and decrescente and origem_ok,
            f"{len(lista)} item(ns), total {total}, {paginas} página(s), "
            f"ordem decrescente: {'sim' if decrescente else 'não'}, "
            f"origem na lista: {'sim' if origem_ok else 'não'}",
            r1,
        )

        # PP6. Página 0 vira a página 1.
        r6 = perfil(donation_id, 0)
        d6 = json_ou_none(r6)
        mesma = isinstance(d6, dict) and d6.get("page") == 1 and ids_dos_itens(d6) == ids
        registrar(
            "PP6. page=0 → tratada como a página 1",
            r6.status_code == 200 and mesma,
            f"HTTP {r6.status_code}, igual à página 1: {'sim' if mesma else 'não'}",
            r6,
        )

        # PP7. Página além da última: lista vazia com o total.
        if eh_int(paginas):
            alem = paginas + 1
            r7 = perfil(donation_id, alem)
            d7 = json_ou_none(r7)
            vazia = (
                isinstance(d7, dict)
                and d7.get("items") == []
                and d7.get("total") == total
                and d7.get("page_total") == paginas
                and d7.get("page") == alem
            )
            registrar(
                "PP7. Página além da última → 200, lista vazia e o mesmo total",
                r7.status_code == 200 and vazia,
                f"HTTP {r7.status_code}, vazia com o total: {'sim' if vazia else 'não'}",
                r7,
            )
        else:
            registrar("PP7. Página além da última", False, "page_total ausente no PP1")

        # PP8. Id inexistente → 404 genérico.
        r8 = perfil(ID_INEXISTENTE)
        d8 = json_ou_none(r8)
        mensagem_8 = d8.get("message") if isinstance(d8, dict) else None
        registrar(
            "PP8. Doação inexistente → 404 “Doação não encontrada.”",
            r8.status_code == 404 and mensagem_8 == MENSAGEM_404,
            f"HTTP {r8.status_code}, mensagem genérica: {'sim' if mensagem_8 == MENSAGEM_404 else 'não'}",
            r8,
        )

        # PP9. (Opcional) Doação indisponível → o mesmo 404 do inexistente.
        if indisponivel_id is None:
            print("Cenário PP9 pulado: nenhuma doação não disponível informada.")
        else:
            r9 = perfil(indisponivel_id)
            d9 = json_ou_none(r9)
            igual = (
                isinstance(d9, dict)
                and isinstance(d8, dict)
                and d9.get("code") == d8.get("code")
                and d9.get("message") == MENSAGEM_404
            )
            registrar(
                "PP9. Doação não disponível → o mesmo 404 genérico do inexistente",
                r9.status_code == 404 and igual,
                f"HTTP {r9.status_code}, igual ao PP8: {'sim' if igual else 'não'}",
                r9,
            )

        # PP10. Cada item da página 1 abre no detalhe (só doações disponíveis).
        print(f"\nCenário PP10: consultando o detalhe de {len(ids)} item(ns), com pausa de {PAUSA_SEGUNDOS} s...")
        falhas_10: list[str] = []
        ultima_falha: httpx.Response | None = None
        for posicao, item_id in enumerate(ids, start=1):
            r = detalhe(item_id)
            if r.status_code != 200:
                falhas_10.append(f"item {posicao}: HTTP {r.status_code}")
                ultima_falha = r
        registrar(
            "PP10. Todos os itens da página 1 abrem no detalhe (disponíveis) → 200",
            bool(ids) and not falhas_10,
            "todos 200" if ids and not falhas_10 else ("; ".join(falhas_10) or "lista vazia"),
            ultima_falha,
        )

    resumo()


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido.")
