"""Roteiro de verificação manual de “Minhas doações” contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e as variáveis XANO_API_URL e XANO_AUTH_API_URL
definidas no ambiente):

    python scripts/teste_minhas_doacoes_real.py

Pede e-mail e senha de duas contas (a dona das doações e outra pessoa) e os
IDs das doações. As credenciais ficam só em memória. O script não grava nada
em arquivo e não imprime nomes, e-mails, URLs, títulos nem corpos de resposta:
só status HTTP, chaves, tipos, contagens e sim/não.

O que ele altera, e como desfaz:
- a edição (MD10 a MD12) é desfeita no fim, gravando de novo os valores
  originais da doação;
- o status (MD15) vai de disponível para reservada e volta para disponível;
- a exclusão (MD19) só roda se for informada uma doação de teste e a pessoa
  confirmar com “s”. Ela não tem volta.

Cenários MD1 a MD19 (decisão 6 do design da change minhas-doacoes).
"""

from __future__ import annotations

import math
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
    sobrenomes,
    vaza_dados,
)

# Pausa entre requisições: fica abaixo do limite de 10 requisições a cada 20 s.
PAUSA_SEGUNDOS = float(os.getenv("TESTE_MINHAS_PAUSA", "2.5"))
POR_PAGINA = 6
ID_INEXISTENTE = 2_000_000_000
MENSAGEM_404 = "Doação não encontrada."
STATUS = {"disponível", "reservada", "concluída"}
CONDICOES = {"Ótimo", "Bom", "Regular"}

CHAVES_LISTA = {"owner", "counts", "items", "page", "per_page", "total", "page_total"}
# O “about” (Sobre) entrou na change editar-perfil: texto ou nulo.
CHAVES_OWNER = {"first_name", "about"}
CHAVES_COUNTS = {"active", "completed"}
CHAVES_ITEM_LISTA = {"id", "created_at", "title", "photo", "condition", "status"}
CHAVES_ITEM_EDICAO = {
    "id",
    "title",
    "description",
    "category_id",
    "condition",
    "delivery_method",
    "contact_preference",
    "status",
}
CAMPOS_EDITAVEIS = (
    "category_id",
    "title",
    "description",
    "condition",
    "delivery_method",
    "contact_preference",
)
CHAVES_PROIBIDAS = {
    "owner_id",
    "user_id",
    "user",
    "email",
    "name",
    "full_name",
    "last_name",
    "surname",
    "address",
    "role",
    "password",
}


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


def campo(resposta: httpx.Response, chave: str) -> object:
    dados = json_ou_none(resposta)
    return dados.get(chave) if isinstance(dados, dict) else None


def ids(dados: Any) -> list[object]:
    return [item.get("id") for item in itens(dados)]


def estrutura_lista_ok(dados: Any) -> tuple[bool, str]:
    if not isinstance(dados, dict) or set(dados) != CHAVES_LISTA:
        return False, f"chaves do topo: {sorted(dados) if isinstance(dados, dict) else type(dados).__name__}"
    if not isinstance(dados.get("owner"), dict) or set(dados["owner"]) != CHAVES_OWNER:
        return False, "chaves de owner inesperadas"
    if not isinstance(dados.get("counts"), dict) or set(dados["counts"]) != CHAVES_COUNTS:
        return False, "chaves de counts inesperadas"
    for item in itens(dados):
        if set(item) != CHAVES_ITEM_LISTA:
            return False, f"chaves de um item: {sorted(item)}"
    return True, "só as chaves permitidas"


def tipos_lista_ok(dados: Any) -> tuple[bool, str]:
    problemas = []
    owner = dados.get("owner", {})
    counts = dados.get("counts", {})
    nome = owner.get("first_name")
    if not isinstance(nome, str) or not nome.strip() or " " in nome.strip():
        problemas.append("first_name")
    if owner.get("about") is not None and not isinstance(owner.get("about"), str):
        problemas.append("about")
    for campo in ("active", "completed"):
        if not eh_int(counts.get(campo)) or counts[campo] < 0:
            problemas.append(campo)
    for campo in ("page", "per_page", "total", "page_total"):
        if not eh_int(dados.get(campo)):
            problemas.append(campo)
    for item in itens(dados):
        if not eh_int(item.get("id")) or not eh_int(item.get("created_at")):
            problemas.append("id/created_at")
        if not isinstance(item.get("title"), str):
            problemas.append("title")
        if item.get("photo") is not None and not isinstance(item.get("photo"), str):
            problemas.append("photo")
        if item.get("condition") is not None and item.get("condition") not in CONDICOES:
            problemas.append("condition")
        if item.get("status") not in STATUS:
            problemas.append("status")
    if problemas:
        return False, "tipos inesperados: " + ", ".join(sorted(set(problemas)))
    return True, "tipos corretos"


def pedir_id(texto: str, obrigatorio: bool) -> int | None:
    valor = input(texto).strip()
    if not valor and not obrigatorio:
        return None
    try:
        return int(valor)
    except ValueError:
        sys.exit("O ID da doação precisa ser um inteiro.")


def main() -> None:
    api = base_url("XANO_API_URL")
    auth = base_url("XANO_AUTH_API_URL")

    with httpx.Client(timeout=TIMEOUT) as cliente:
        dona = login(cliente, auth, "dona das doações")
        outra = login(cliente, auth, "outra pessoa")

        doacao_id = pedir_id("\nID de uma doação DISPONÍVEL da dona: ", True)
        concluida_id = pedir_id(
            "ID de uma doação CONCLUÍDA da dona, para MD14 e MD17 (Enter para pular): ",
            False,
        )
        apagar_id = pedir_id(
            "ID de uma doação de TESTE da dona que pode ser APAGADA, para MD19"
            " (Enter para pular): ",
            False,
        )
        proibidos = sobrenomes([dona])

        def pedir(metodo: str, caminho: str, conta: Conta | None, **kwargs: Any) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            headers = conta.headers if conta else {}
            return cliente.request(metodo, f"{api}{caminho}", headers=headers, **kwargs)

        def lista(conta: Conta | None, pagina: int | None = None) -> httpx.Response:
            params = {} if pagina is None else {"page": pagina}
            return pedir("GET", "/catalog/donations/mine", conta, params=params)

        def item(conta: Conta | None, doacao: int) -> httpx.Response:
            return pedir("GET", "/catalog/donations/mine/item", conta, params={"donation_id": doacao})

        def editar(conta: Conta | None, dados: dict) -> httpx.Response:
            return pedir("PATCH", "/catalog/donations", conta, json=dados)

        def mudar_status(conta: Conta | None, doacao: int, status: str) -> httpx.Response:
            return pedir(
                "PATCH",
                "/catalog/donations/status",
                conta,
                json={"donation_id": doacao, "status": status},
            )

        def apagar(conta: Conta | None, doacao: int) -> httpx.Response:
            return pedir("DELETE", "/catalog/donations", conta, params={"donation_id": doacao})

        def detalhe_publico(doacao: int) -> httpx.Response:
            return pedir("GET", "/catalog/donations/detail", None, params={"donation_id": doacao})

        print("\n=== Lista (MD1 a MD6) ===")

        # MD1. Sem token → 401.
        r = lista(None)
        registrar("MD1. Lista sem token → 401", r.status_code == 401, f"HTTP {r.status_code}", r)

        # MD2. Dona: 200 com só as chaves permitidas e os tipos certos.
        r2 = lista(dona)
        d2 = json_ou_none(r2)
        ok, detalhe = estrutura_lista_ok(d2)
        registrar("MD2a. Lista da dona → 200 com só as chaves permitidas", r2.status_code == 200 and ok, f"HTTP {r2.status_code}, {detalhe}", r2)
        if r2.status_code != 200 or not ok:
            print("\nSem a lista não dá para seguir. Encerrando.")
            resumo()
            return
        ok, detalhe = tipos_lista_ok(d2)
        registrar("MD2b. Tipos dos campos da lista", ok, detalhe)

        # MD3. Nada de chaves proibidas, '@' ou sobrenome; a outra pessoa não vê a doação da dona.
        proibidas = sorted(chaves_em_todos_os_niveis(d2) & CHAVES_PROIBIDAS)
        vazamento = vaza_dados(r2, proibidos)
        registrar(
            "MD3a. Sem chaves proibidas, '@' ou sobrenome",
            not proibidas and vazamento is None,
            "nada encontrado" if not proibidas and vazamento is None else f"chaves: {proibidas}; {vazamento or ''}",
        )
        r3 = lista(outra)
        d3 = json_ou_none(r3)
        isolada = r3.status_code == 200 and doacao_id not in ids(d3)
        registrar(
            "MD3b. A lista da outra pessoa não traz a doação da dona",
            isolada,
            f"HTTP {r3.status_code}, isolada: {'sim' if isolada else 'não'}",
            r3,
        )

        # MD4. Até 6 itens, página 1, mais recentes primeiro, sem repetição.
        lista_1 = itens(d2)
        datas = [i.get("created_at") for i in lista_1]
        ordem = all(eh_int(d) for d in datas) and datas == sorted(datas, reverse=True)
        ok = (
            len(lista_1) <= POR_PAGINA
            and d2.get("page") == 1
            and d2.get("per_page") == POR_PAGINA
            and len(set(ids(d2))) == len(lista_1)
            and ordem
        )
        registrar(
            "MD4. Até 6 itens, página 1, mais recentes primeiro, sem repetição",
            ok,
            f"{len(lista_1)} item(ns), ordem decrescente: {'sim' if ordem else 'não'}",
        )

        # MD5. Totais e contadores coerentes.
        total = d2.get("total")
        paginas = d2.get("page_total")
        counts = d2.get("counts", {})
        ativos, concluidos = counts.get("active"), counts.get("completed")
        coerente = (
            eh_int(total)
            and eh_int(paginas)
            and eh_int(ativos)
            and eh_int(concluidos)
            and total >= 1
            and ativos + concluidos <= total
            and paginas == math.ceil(total / POR_PAGINA)
            and len(lista_1) == min(POR_PAGINA, total)
        )
        na_pagina = {s: sum(1 for i in lista_1 if i.get("status") == s) for s in STATUS}
        cabe = coerente and (
            na_pagina["disponível"] + na_pagina["reservada"] <= ativos
            and na_pagina["concluída"] <= concluidos
        )
        origem = (eh_int(total) and total > POR_PAGINA) or doacao_id in ids(d2)
        registrar(
            "MD5. Totais, páginas e contadores coerentes",
            coerente and cabe and origem,
            f"total {total}, {paginas} página(s), ativas {ativos}, concluídas {concluidos}, "
            f"doação informada na lista: {'sim' if origem else 'não'}",
        )

        # MD6. Página 0 vira 1; página além da última vem vazia com os totais.
        r = lista(dona, 0)
        d = json_ou_none(r)
        mesma = isinstance(d, dict) and d.get("page") == 1 and ids(d) == ids(d2)
        registrar("MD6a. page=0 → página 1", r.status_code == 200 and mesma, f"HTTP {r.status_code}, igual à página 1: {'sim' if mesma else 'não'}", r)
        alem = (paginas if eh_int(paginas) else 0) + 1
        r = lista(dona, alem)
        d = json_ou_none(r)
        vazia = (
            isinstance(d, dict)
            and d.get("items") == []
            and d.get("total") == total
            and d.get("counts") == counts
            and d.get("page") == alem
        )
        registrar("MD6b. Página além da última → vazia com os totais", r.status_code == 200 and vazia, f"HTTP {r.status_code}, vazia com os totais: {'sim' if vazia else 'não'}", r)

        print("\n=== Leitura para edição (MD7 a MD9) ===")

        # MD7. A própria doação → 200 só com os campos editáveis e o status.
        r7 = item(dona, doacao_id)
        original = json_ou_none(r7)
        ok = r7.status_code == 200 and isinstance(original, dict) and set(original) == CHAVES_ITEM_EDICAO
        registrar("MD7. Dona lê a própria doação → 200 com só os campos editáveis", ok, f"HTTP {r7.status_code}", r7)
        if not ok:
            print("\nSem a leitura da doação não dá para seguir. Encerrando.")
            resumo()
            return
        if original.get("status") != "disponível":
            print("Aviso: a doação informada não está disponível; os cenários de status vão falhar.")

        # MD8. Outra pessoa e id inexistente → o mesmo 404 genérico.
        r_outra = item(outra, doacao_id)
        r_inexistente = item(dona, ID_INEXISTENTE)
        mensagens = [campo(x, "message") for x in (r_outra, r_inexistente)]
        igual = (
            r_outra.status_code == 404
            and r_inexistente.status_code == 404
            and mensagens[0] == mensagens[1] == MENSAGEM_404
        )
        registrar(
            "MD8. Outra pessoa e id inexistente → o mesmo 404 genérico",
            igual,
            f"HTTP {r_outra.status_code} / {r_inexistente.status_code}, mesma mensagem: {'sim' if mensagens[0] == mensagens[1] else 'não'}",
            r_outra if r_outra.status_code != 404 else r_inexistente,
        )

        # MD9. Sem token → 401.
        r = item(None, doacao_id)
        registrar("MD9. Leitura sem token → 401", r.status_code == 401, f"HTTP {r.status_code}", r)

        print("\n=== Edição (MD10 a MD14) ===")

        base = {"donation_id": doacao_id, **{c: original.get(c) for c in CAMPOS_EDITAVEIS}}
        if base["delivery_method"] != "A combinar" or base["contact_preference"] not in {"E-mail", "Chat do DoaFácil"}:
            print(
                "Aviso: a doação tem entrega ou contato fora das opções do cadastro. A edição grava"
                " “A combinar” e “Chat do DoaFácil”, e a restauração no fim não volta esses dois campos."
            )
            base["delivery_method"] = "A combinar"
            if base["contact_preference"] not in {"E-mail", "Chat do DoaFácil"}:
                base["contact_preference"] = "Chat do DoaFácil"
        if not base.get("description"):
            base["description"] = "Descrição de teste."

        try:
            # MD10. Edição válida → 200 com os campos novos, sem owner_id.
            titulo_teste = "Teste de edição"
            r = editar(dona, {**base, "title": titulo_teste, "condition": "Regular"})
            d = json_ou_none(r)
            gravou = isinstance(d, dict) and d.get("title") == titulo_teste and d.get("condition") == "Regular"
            sem_dono = isinstance(d, dict) and not (chaves_em_todos_os_niveis(d) & CHAVES_PROIBIDAS)
            registrar(
                "MD10. Edição válida → 200 com os campos novos e sem owner_id",
                r.status_code == 200 and gravou and sem_dono,
                f"HTTP {r.status_code}, gravou: {'sim' if gravou else 'não'}, sem owner_id: {'sim' if sem_dono else 'não'}",
                r,
            )

            # MD11. Título com 100 “á” → aceito (o limite conta caracteres).
            r = editar(dona, {**base, "title": "á" * 100})
            registrar("MD11. Título com 100 'á' → 200", r.status_code == 200, f"HTTP {r.status_code}", r)

            # MD12. Valores inválidos → 400, sem alterar a doação.
            invalidos = {
                "título vazio": {"title": "   "},
                "título com 101 caracteres": {"title": "a" * 101},
                "descrição vazia": {"description": "   "},
                "descrição com 2001 caracteres": {"description": "a" * 2001},
                "entrega 'Entrega'": {"delivery_method": "Entrega"},
                "contato 'WhatsApp'": {"contact_preference": "WhatsApp"},
                "condição 'Novo'": {"condition": "Novo"},
                "categoria inexistente": {"category_id": ID_INEXISTENTE},
            }
            falhas: list[str] = []
            for rotulo, mudanca in invalidos.items():
                r = editar(dona, {**base, **mudanca})
                if r.status_code != 400:
                    falhas.append(f"{rotulo}: HTTP {r.status_code}")
            r = item(dona, doacao_id)
            atual = json_ou_none(r)
            intacta = isinstance(atual, dict) and atual.get("title") == "á" * 100
            registrar(
                "MD12. Valores inválidos → 400, sem alterar a doação",
                not falhas and intacta,
                ("todos 400" if not falhas else "; ".join(falhas)) + f", doação intacta: {'sim' if intacta else 'não'}",
            )

            # MD13. Outra pessoa edita a doação da dona → 404.
            r = editar(outra, {**base, "title": "Tentativa da outra pessoa"})
            registrar("MD13. Outra pessoa edita a doação da dona → 404", r.status_code == 404, f"HTTP {r.status_code}", r)

            # MD14. Doação concluída → 400.
            if concluida_id is None:
                print("Cenário MD14 pulado: nenhuma doação concluída informada.")
            else:
                rc = item(dona, concluida_id)
                dc = json_ou_none(rc)
                if rc.status_code != 200 or not isinstance(dc, dict) or dc.get("status") != "concluída":
                    registrar("MD14. Edição de doação concluída → 400", False, f"a doação informada não é uma concluída da dona (HTTP {rc.status_code})", rc)
                else:
                    dados = {"donation_id": concluida_id, **{c: dc.get(c) for c in CAMPOS_EDITAVEIS}}
                    dados.update(delivery_method="A combinar", description=dc.get("description") or "Descrição.")
                    if dados["contact_preference"] not in {"E-mail", "Chat do DoaFácil"}:
                        dados["contact_preference"] = "Chat do DoaFácil"
                    r = editar(dona, dados)
                    registrar("MD14. Edição de doação concluída → 400", r.status_code == 400, f"HTTP {r.status_code}", r)

            print("\n=== Status (MD15 a MD17) ===")

            # MD15. disponível → reservada → disponível, conferindo o detalhe público.
            r_res = mudar_status(dona, doacao_id, "reservada")
            r_det_res = detalhe_publico(doacao_id)
            r_disp = mudar_status(dona, doacao_id, "disponível")
            r_det_disp = detalhe_publico(doacao_id)
            ok = (
                r_res.status_code == 200
                and campo(r_res, "status") == "reservada"
                and r_det_res.status_code == 404
                and r_disp.status_code == 200
                and campo(r_disp, "status") == "disponível"
                and r_det_disp.status_code == 200
            )
            registrar(
                "MD15. disponível → reservada → disponível, com o detalhe público acompanhando",
                ok,
                f"HTTP {r_res.status_code} / detalhe {r_det_res.status_code} / {r_disp.status_code} / detalhe {r_det_disp.status_code}",
                r_disp if r_res.status_code == 200 else r_res,
            )

            # MD16. Outra pessoa muda o status → recusado, sem alterar.
            r = mudar_status(outra, doacao_id, "reservada")
            r_check = item(dona, doacao_id)
            segue = campo(r_check, "status") == "disponível"
            registrar(
                "MD16. Outra pessoa muda o status → recusado (403/404), sem alterar",
                r.status_code in {403, 404} and segue,
                f"HTTP {r.status_code}, status mantido: {'sim' if segue else 'não'}",
                r,
            )

            # MD17. Concluída → disponível → 400.
            if concluida_id is None:
                print("Cenário MD17 pulado: nenhuma doação concluída informada.")
            else:
                r = mudar_status(dona, concluida_id, "disponível")
                registrar("MD17. Concluída → disponível → 400", r.status_code == 400, f"HTTP {r.status_code}", r)

            print("\n=== Exclusão (MD18 e MD19) ===")

            # MD18. Outra pessoa apaga a doação da dona → recusado, e a doação continua.
            r = apagar(outra, doacao_id)
            r_check = item(dona, doacao_id)
            registrar(
                "MD18. Outra pessoa apaga a doação da dona → recusado (403/404), e ela continua",
                r.status_code in {403, 404} and r_check.status_code == 200,
                f"HTTP {r.status_code}, doação continua: {'sim' if r_check.status_code == 200 else 'não'}",
                r,
            )

            # MD19. (Opcional) A dona apaga a doação de teste.
            if apagar_id is None:
                print("Cenário MD19 pulado: nenhuma doação de teste informada.")
            elif apagar_id == doacao_id:
                print("Cenário MD19 pulado: a doação de teste não pode ser a mesma dos outros cenários.")
            elif input(f"\nApagar AGORA a doação de teste {apagar_id}? Isso não tem volta. (s/N) ").strip().lower() != "s":
                print("Cenário MD19 pulado: doação mantida.")
            else:
                r = apagar(dona, apagar_id)
                d = json_ou_none(r)
                apagou = isinstance(d, dict) and d.get("deleted") is True
                r_check = item(dona, apagar_id)
                registrar(
                    "MD19. Dona apaga a doação de teste → 200, e a leitura dá 404",
                    r.status_code == 200 and apagou and r_check.status_code == 404,
                    f"HTTP {r.status_code}, leitura depois: HTTP {r_check.status_code}",
                    r,
                )

        finally:
            print("\n=== Restauração ===")
            r = editar(dona, base)
            r_check = item(dona, doacao_id)
            atual = json_ou_none(r_check)
            restaurada = isinstance(atual, dict) and all(atual.get(c) == base[c] for c in CAMPOS_EDITAVEIS)
            registrar(
                "Restauração dos valores originais da doação",
                r.status_code == 200 and restaurada,
                f"HTTP {r.status_code}, restaurada: {'sim' if restaurada else 'não'}",
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
