"""Roteiro de verificação manual da edição do perfil contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e as variáveis XANO_API_URL e XANO_AUTH_API_URL
definidas no ambiente):

    python scripts/teste_editar_perfil_real.py

Pede o e-mail e a senha de uma conta e, opcionalmente, o ID de uma doação
disponível dessa conta (para o perfil público e a cidade da doação). As
credenciais ficam só em memória. O script não grava nada em arquivo e não
imprime nomes, e-mails, cidades, textos de Sobre, URLs nem corpos de resposta:
só status HTTP, chaves, tipos e sim/não.

O script ALTERA o perfil da conta (cidade, estado e Sobre) e, no fim, grava de
novo os valores originais, mesmo se der erro no meio. Um Sobre original nulo
volta como texto vazio (o PATCH sempre grava o Sobre; vazio apaga).

Cenários EP1 a EP12 (decisão 6 do design da change editar-perfil).
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

PAUSA_SEGUNDOS = float(os.getenv("TESTE_PERFIL_EDICAO_PAUSA", "2.5"))
# O GET devolve também a URL da foto (change foto-perfil); a resposta do PATCH
# não muda e continua sem “photo”.
CHAVES_PERFIL_PATCH = {"id", "created_at", "name", "email", "city", "state", "about"}
CHAVES_PERFIL = CHAVES_PERFIL_PATCH | {"photo"}
CHAVES_DONOR = {"first_name", "city", "state", "member_since", "about", "photo"}
SOBRE_TESTE = "Teste de Sobre.\nSegunda linha."
SOBRE_HTML = "<b>oi</b> & <script>x</script>"
CIDADE_TESTE = "Cidade de Teste"


def campo(resposta: httpx.Response, chave: str) -> object:
    dados = json_ou_none(resposta)
    return dados.get(chave) if isinstance(dados, dict) else None


def sobre(resposta: httpx.Response) -> str:
    """Sobre normalizado: nulo vira texto vazio."""
    valor = campo(resposta, "about")
    return valor if isinstance(valor, str) else ""


def main() -> None:
    api = base_url("XANO_API_URL")
    auth = base_url("XANO_AUTH_API_URL")

    with httpx.Client(timeout=TIMEOUT) as cliente:
        conta = login(cliente, auth, "da pessoa")
        texto = input(
            "\nID de uma doação DISPONÍVEL dessa conta, para EP11 e EP12 (Enter para pular): "
        ).strip()
        doacao_id: int | None = None
        if texto:
            try:
                doacao_id = int(texto)
            except ValueError:
                sys.exit("O ID da doação precisa ser um inteiro.")

        def pedir(metodo: str, url: str, conta_: Conta | None, **kwargs: Any) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            headers = conta_.headers if conta_ else {}
            return cliente.request(metodo, url, headers=headers, **kwargs)

        def perfil(conta_: Conta | None) -> httpx.Response:
            return pedir("GET", f"{auth}/auth/profile", conta_)

        def salvar(dados: dict[str, Any]) -> httpx.Response:
            return pedir("PATCH", f"{auth}/auth/profile", conta, json=dados)

        print("\n=== Leitura (EP1 e EP2) ===")

        # EP1. Sem token → 401.
        r = perfil(None)
        registrar("EP1. GET auth/profile sem token → 401", r.status_code == 401, f"HTTP {r.status_code}", r)

        # EP2. Com token: só as chaves do perfil, com o about.
        r2 = perfil(conta)
        original = json_ou_none(r2)
        ok = (
            r2.status_code == 200
            and isinstance(original, dict)
            and set(original) == CHAVES_PERFIL
            and (original.get("about") is None or isinstance(original.get("about"), str))
        )
        registrar("EP2. GET auth/profile → 200 com o about e só as chaves do perfil", ok, f"HTTP {r2.status_code}", r2)
        if not ok:
            print("\nSem o perfil original não dá para seguir com segurança. Encerrando.")
            resumo()
            return

        email_original = original.get("email")
        restaurar = {
            "name": original.get("name"),
            "city": original.get("city"),
            "state": original.get("state"),
            "about": original.get("about") or "",
        }
        estado_teste = "AC" if original.get("state") != "AC" else "RJ"

        cidade_doacao_antes = None
        if doacao_id is not None:
            r = pedir("GET", f"{api}/catalog/donations/detail", None, params={"donation_id": doacao_id})
            cidade_doacao_antes = campo(r, "city")
            if r.status_code != 200:
                print(f"Aviso: o detalhe da doação informada respondeu HTTP {r.status_code}; EP11 e EP12 vão falhar.")

        try:
            print("\n=== Edição (EP3 a EP9) ===")

            # EP3. PATCH válido → 200 com os campos novos e o mesmo e-mail.
            dados = {
                "name": original.get("name"),
                "city": CIDADE_TESTE,
                "state": estado_teste,
                "about": SOBRE_TESTE,
            }
            r = salvar(dados)
            d = json_ou_none(r)
            gravou = (
                isinstance(d, dict)
                and set(d) == CHAVES_PERFIL_PATCH
                and d.get("city") == CIDADE_TESTE
                and d.get("state") == estado_teste
                and d.get("about") == SOBRE_TESTE
                and d.get("email") == email_original
            )
            registrar(
                "EP3. PATCH válido → 200 com os campos novos, o Sobre com quebra de linha e o mesmo e-mail",
                r.status_code == 200 and gravou,
                f"HTTP {r.status_code}, gravou: {'sim' if gravou else 'não'}",
                r,
            )

            # EP4. O GET reflete a mudança; e-mail igual.
            r = perfil(conta)
            reflete = (
                campo(r, "city") == CIDADE_TESTE
                and campo(r, "state") == estado_teste
                and campo(r, "about") == SOBRE_TESTE
                and campo(r, "email") == email_original
            )
            registrar("EP4. GET reflete a edição e o e-mail não muda", r.status_code == 200 and reflete, f"HTTP {r.status_code}", r)

            # EP5. Sobre com 300 'á' aceito; com 301, 400 sem alterar.
            r300 = salvar({**dados, "about": "á" * 300})
            r301 = salvar({**dados, "about": "á" * 301})
            r_check = perfil(conta)
            intacto = sobre(r_check) == "á" * 300
            registrar(
                "EP5. Sobre com 300 'á' → 200; com 301 → 400, sem alterar",
                r300.status_code == 200 and r301.status_code == 400 and intacto,
                f"HTTP {r300.status_code} / {r301.status_code}, Sobre intacto: {'sim' if intacto else 'não'}",
                r301 if r300.status_code == 200 else r300,
            )

            # EP6. UF fora das 27 → 400.
            r = salvar({**dados, "state": "XX"})
            registrar("EP6. Estado 'XX' → 400", r.status_code == 400, f"HTTP {r.status_code}", r)

            # EP7. Nome ou cidade vazios → 400, sem alterar.
            r_nome = salvar({**dados, "name": "   "})
            r_cidade = salvar({**dados, "city": ""})
            r_check = perfil(conta)
            sem_mudar = campo(r_check, "name") == original.get("name") and campo(r_check, "city") == CIDADE_TESTE
            registrar(
                "EP7. Nome ou cidade vazios → 400, sem alterar",
                r_nome.status_code == 400 and r_cidade.status_code == 400 and sem_mudar,
                f"HTTP {r_nome.status_code} / {r_cidade.status_code}, perfil intacto: {'sim' if sem_mudar else 'não'}",
                r_nome if r_nome.status_code != 400 else r_cidade,
            )

            # EP8. O Sobre é sempre gravado: omitido apaga; vazio apaga.
            salvar({**dados, "about": SOBRE_TESTE})
            r_omitido = salvar({k: v for k, v in dados.items() if k != "about"})
            apagou_omitido = r_omitido.status_code == 200 and sobre(r_omitido) == ""
            salvar({**dados, "about": SOBRE_TESTE})
            r_vazio = salvar({**dados, "about": ""})
            apagou_vazio = r_vazio.status_code == 200 and sobre(r_vazio) == ""
            r_check = perfil(conta)
            confirmado = sobre(r_check) == ""
            registrar(
                "EP8. Sobre omitido e Sobre vazio apagam o texto",
                apagou_omitido and apagou_vazio and confirmado,
                f"HTTP {r_omitido.status_code} / {r_vazio.status_code}, omitido apagou: "
                f"{'sim' if apagou_omitido else 'não'}, vazio apagou: {'sim' if apagou_vazio else 'não'}, "
                f"GET confirma: {'sim' if confirmado else 'não'}",
                r_omitido if not apagou_omitido else r_vazio,
            )

            # EP9. Sobre com HTML volta literal.
            r = salvar({**dados, "about": SOBRE_HTML})
            registrar(
                "EP9. Sobre com marcação HTML volta igual (texto literal)",
                r.status_code == 200 and sobre(r) == SOBRE_HTML,
                f"HTTP {r.status_code}, igual: {'sim' if sobre(r) == SOBRE_HTML else 'não'}",
                r,
            )

            print("\n=== Sobre em outros endpoints (EP10 a EP12) ===")

            # EP10. Minhas doações traz o owner.about atual.
            r = pedir("GET", f"{api}/catalog/donations/mine", conta)
            owner = campo(r, "owner")
            igual = isinstance(owner, dict) and owner.get("about") == SOBRE_HTML
            registrar("EP10. GET donations/mine traz owner.about atual", r.status_code == 200 and igual, f"HTTP {r.status_code}, igual: {'sim' if igual else 'não'}", r)

            if doacao_id is None:
                print("Cenários EP11 e EP12 pulados: nenhuma doação informada.")
            else:
                # EP11. Perfil público traz o about, sem e-mail.
                r = pedir("GET", f"{api}/catalog/donations/donor", None, params={"donation_id": doacao_id})
                donor = campo(r, "donor")
                ok = (
                    isinstance(donor, dict)
                    and set(donor) == CHAVES_DONOR
                    and donor.get("about") == SOBRE_HTML
                    and "@" not in r.text
                )
                registrar("EP11. Perfil público traz o about atual, sem e-mail", r.status_code == 200 and ok, f"HTTP {r.status_code}, ok: {'sim' if ok else 'não'}", r)

                # EP12. A cidade da doação publicada não mudou.
                r = pedir("GET", f"{api}/catalog/donations/detail", None, params={"donation_id": doacao_id})
                mesma = cidade_doacao_antes is not None and campo(r, "city") == cidade_doacao_antes
                registrar(
                    "EP12. Mudar a cidade do perfil não muda a cidade da doação publicada",
                    r.status_code == 200 and mesma,
                    f"HTTP {r.status_code}, mesma cidade: {'sim' if mesma else 'não'}",
                    r,
                )
        finally:
            print("\n=== Restauração ===")
            if restaurar["state"] not in {
                "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
                "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
            }:
                print("Aviso: o estado original não é uma das 27 siglas; a restauração vai falhar.")
            r = salvar(restaurar)
            r_check = perfil(conta)
            restaurado = (
                campo(r_check, "name") == restaurar["name"]
                and campo(r_check, "city") == restaurar["city"]
                and campo(r_check, "state") == restaurar["state"]
                and sobre(r_check) == restaurar["about"]
            )
            registrar(
                "Restauração do perfil original",
                r.status_code == 200 and restaurado,
                f"HTTP {r.status_code}, restaurado: {'sim' if restaurado else 'não'}",
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
