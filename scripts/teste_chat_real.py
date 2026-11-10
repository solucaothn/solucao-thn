"""Roteiro de verificação manual do backend do chat contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e as variáveis XANO_API_URL e XANO_AUTH_API_URL
definidas no ambiente):

    python scripts/teste_chat_real.py

As credenciais são pedidas no terminal e mantidas só em memória. O script não
grava nada em arquivo e não imprime tokens, e-mails nem corpos de resposta.

Atenção: o script cria dados reais (conversa e mensagens) na doação informada.
Os cenários 9 (status) e 10 (exclusão) são opcionais e pedem confirmação:
o 9 deixa a doação concluída, o que não tem volta.
"""

from __future__ import annotations

import getpass
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx

TIMEOUT = httpx.Timeout(20.0)
LIMITE_TENTATIVAS_RATE_LIMIT = 20
MENSAGEM_ACENTUADA = "Olá! A doação ainda está disponível?"
MENSAGEM_HTML = "<b>oi</b> & <script>x</script>"
# Espera para a janela de 60 s do limite do chat esvaziar depois do cenário 8.
ESPERA_JANELA_SEGUNDOS = 62
# Mensagem do 429 do próprio endpoint; outro texto indica limite da plataforma.
MENSAGEM_LIMITE_CHAT = "Limite de mensagens atingido"
# Pausa entre requisições dos cenários 1 a 7, para não esbarrar em um possível
# limite de requisições da instância Xano (diferente do limite do chat).
PAUSA_SEGUNDOS = float(os.getenv("TESTE_CHAT_PAUSA", "2.5"))
# Pausa entre envios do cenário 8: fica abaixo de 10 requisições por 20 s da
# plataforma e ainda manda as 10 mensagens dentro da janela de 60 s do chat.
PAUSA_RATE_LIMIT_SEGUNDOS = 2.2

resultados: list[tuple[str, bool]] = []


@dataclass
class Conta:
    papel: str
    token: str = field(repr=False)
    nome_completo: str = field(default="", repr=False)

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


def base_url(variavel: str) -> str:
    valor = os.getenv(variavel, "").strip().rstrip("/")
    partes = urlparse(valor)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        sys.exit(f"{variavel} precisa conter uma URL HTTP(S) válida.")
    return valor


def json_ou_none(resposta: httpx.Response) -> Any:
    try:
        return resposta.json()
    except ValueError:
        return None


def erro_resumido(resposta: httpx.Response | None) -> str:
    """Só os campos code e message do JSON de erro; nunca o corpo inteiro."""
    if resposta is None:
        return ""
    dados = json_ou_none(resposta)
    if not isinstance(dados, dict):
        return " | corpo não é JSON"
    partes = []
    for campo in ("code", "message"):
        valor = dados.get(campo)
        if isinstance(valor, str) and valor:
            partes.append(f"{campo}={valor[:200]!r}")
    return " | " + (", ".join(partes) if partes else "sem code/message")


def registrar(
    cenario: str, ok: bool, detalhe: str, resposta: httpx.Response | None = None
) -> None:
    resultados.append((cenario, ok))
    extra = "" if ok else erro_resumido(resposta)
    print(f"[{'OK' if ok else 'FALHOU'}] {cenario} — {detalhe}{extra}")


def login(cliente: httpx.Client, auth_url: str, papel: str) -> Conta:
    print(f"\nConta {papel}:")
    email = input("  E-mail: ").strip()
    senha = getpass.getpass("  Senha: ")
    resposta = cliente.post(
        f"{auth_url}/auth/login", json={"email": email, "password": senha}
    )
    del email, senha
    dados = json_ou_none(resposta)
    if resposta.status_code != 200 or not isinstance(dados, dict) or not dados.get("authToken"):
        sys.exit(f"Login da conta {papel} falhou (HTTP {resposta.status_code}).")
    conta = Conta(papel=papel, token=dados["authToken"])

    time.sleep(PAUSA_SEGUNDOS)
    me = cliente.get(f"{auth_url}/auth/me", headers=conta.headers)
    me_dados = json_ou_none(me)
    if me.status_code == 200 and isinstance(me_dados, dict):
        conta.nome_completo = str(me_dados.get("name") or "")
    print(f"  Login da conta {papel}: HTTP {resposta.status_code}")
    return conta


def sobrenomes(contas: list[Conta]) -> list[str]:
    """Partes do nome depois do primeiro nome, só para checagem em memória."""
    partes: list[str] = []
    for conta in contas:
        nomes = conta.nome_completo.split()
        partes.extend(p for p in nomes[1:] if len(p) >= 3)
    return partes


def vaza_dados(resposta: httpx.Response, proibidos: list[str]) -> str | None:
    texto = resposta.text
    if "@" in texto:
        return "contém '@'"
    texto_minusculo = texto.lower()
    for parte in proibidos:
        if parte.lower() in texto_minusculo:
            return "contém sobrenome de participante"
    return None


def main() -> None:
    api = base_url("XANO_API_URL")
    auth = base_url("XANO_AUTH_API_URL")

    with httpx.Client(timeout=TIMEOUT) as cliente:
        dona = login(cliente, auth, "dona da doação")
        interessada = login(cliente, auth, "interessada")
        estranha = login(cliente, auth, "não participante")

        try:
            donation_id = int(input("\nID da doação (da dona, disponível, contato por chat): ").strip())
        except ValueError:
            sys.exit("ID da doação precisa ser um inteiro.")

        texto_email = input(
            "ID de outra doação, disponível, com contato por E-mail e sem conversa da"
            " interessada (Enter para pular): "
        ).strip()
        donation_email_id: int | None = None
        if texto_email:
            try:
                donation_email_id = int(texto_email)
            except ValueError:
                sys.exit("ID da doação precisa ser um inteiro.")

        proibidos = sobrenomes([dona, interessada])
        if not proibidos:
            print("Aviso: nenhum sobrenome encontrado nas contas; a checagem de sobrenome fica limitada.")

        def iniciar(conta: Conta, doacao: int | None = None) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.post(
                f"{api}/catalog/chat/conversations/start",
                json={"donation_id": donation_id if doacao is None else doacao},
                headers=conta.headers,
            )

        def mudar_status(status: str) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.patch(
                f"{api}/catalog/donations/status",
                json={"donation_id": donation_id, "status": status},
                headers=dona.headers,
            )

        def textos(resposta: httpx.Response) -> list[str]:
            dados = json_ou_none(resposta)
            lista = dados.get("messages") if isinstance(dados, dict) else None
            if not isinstance(lista, list):
                return []
            return [m.get("text") for m in lista if isinstance(m, dict)]

        def enviar(conta: Conta, conversa: int, texto: str, pausar: bool = True) -> httpx.Response:
            if pausar:
                time.sleep(PAUSA_SEGUNDOS)
            return cliente.post(
                f"{api}/catalog/chat/messages",
                json={"conversation_id": conversa, "message_text": texto},
                headers=conta.headers,
            )

        def ler(conta: Conta, conversa: int) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.get(
                f"{api}/catalog/chat/messages",
                params={"conversation_id": conversa, "limit": 100},
                headers=conta.headers,
            )

        def ler_sem_limite(conta: Conta, conversa: int) -> httpx.Response:
            # Sem o parâmetro limit de propósito: cobre a correção do messages_GET.
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.get(
                f"{api}/catalog/chat/messages",
                params={"conversation_id": conversa},
                headers=conta.headers,
            )

        def listar(conta: Conta) -> httpx.Response:
            # Sem parâmetros de propósito: é o caso do bug 1.
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.get(
                f"{api}/catalog/chat/conversations", headers=conta.headers
            )

        print("\n=== Cenários ===")

        # 1. Dona tenta iniciar conversa na própria doação.
        r = iniciar(dona)
        registrar("1. Dona inicia conversa na própria doação → 404", r.status_code == 404, f"HTTP {r.status_code}", r)

        # 2. Interessada inicia conversa; segunda chamada devolve a mesma.
        r1 = iniciar(interessada)
        d1 = json_ou_none(r1)
        conversa_id = d1.get("conversation_id") if isinstance(d1, dict) else None
        registrar(
            "2a. Interessada inicia conversa → sucesso",
            r1.status_code == 200 and isinstance(conversa_id, int),
            f"HTTP {r1.status_code}",
            r1,
        )
        if not isinstance(conversa_id, int):
            print("\nSem conversation_id não dá para seguir. Encerrando.")
            resumo()
            return
        r2 = iniciar(interessada)
        d2 = json_ou_none(r2)
        mesmo = isinstance(d2, dict) and d2.get("conversation_id") == conversa_id
        registrar(
            "2b. Segunda chamada devolve a mesma conversa",
            r2.status_code == 200 and mesmo,
            f"HTTP {r2.status_code}, mesma conversa: {'sim' if mesmo else 'não'}",
            r2,
        )

        # 2c. (Opcional) Doação com preferência "E-mail" não abre conversa.
        if donation_email_id is None:
            print("Cenário 2c pulado: nenhuma doação com contato por E-mail informada.")
        else:
            r = iniciar(interessada, donation_email_id)
            registrar(
                "2c. Interessada inicia conversa em doação com contato por E-mail → 404",
                r.status_code == 404,
                f"HTTP {r.status_code}",
                r,
            )

        # 3. Mensagem com acento.
        r3 = enviar(interessada, conversa_id, MENSAGEM_ACENTUADA)
        d = json_ou_none(r3)
        texto_ok = isinstance(d, dict) and d.get("text") == MENSAGEM_ACENTUADA
        registrar(
            "3. Interessada envia mensagem acentuada → sucesso",
            r3.status_code == 200 and texto_ok,
            f"HTTP {r3.status_code}, texto preservado: {'sim' if texto_ok else 'não'}",
            r3,
        )

        # 3b. Conteúdo parecido com HTML volta literal, sem alteração.
        r3b = enviar(interessada, conversa_id, MENSAGEM_HTML)
        d = json_ou_none(r3b)
        html_ok = isinstance(d, dict) and d.get("text") == MENSAGEM_HTML
        registrar(
            "3b. POST devolve o texto com HTML idêntico",
            r3b.status_code == 200 and html_ok,
            f"HTTP {r3b.status_code}, idêntico: {'sim' if html_ok else 'não'}",
            r3b,
        )

        # 4. Dona lista conversas e lê mensagens, sem e-mail nem sobrenome.
        rl = listar(dona)
        dl = json_ou_none(rl)
        conversas = dl.get("conversations") if isinstance(dl, dict) else None
        tem_conversa = isinstance(conversas, list) and any(
            isinstance(c, dict) and c.get("conversation_id") == conversa_id for c in conversas
        )
        registrar(
            "4a. Dona lista conversas e vê a conversa",
            rl.status_code == 200 and tem_conversa,
            f"HTTP {rl.status_code}",
            rl,
        )
        rm = ler(dona, conversa_id)
        dm = json_ou_none(rm)
        mensagens = dm.get("messages") if isinstance(dm, dict) else None
        viu = isinstance(mensagens, list) and any(
            isinstance(m, dict) and m.get("text") == MENSAGEM_ACENTUADA for m in mensagens
        )
        registrar(
            "4b. Dona lê mensagens e vê a mensagem",
            rm.status_code == 200 and viu,
            f"HTTP {rm.status_code}",
            rm,
        )
        # 4c. Checa os 4 endpoints: start (2a/2b), POST messages (3/3b), lista e leitura.
        checadas = {
            "start 2a": r1,
            "start 2b": r2,
            "POST messages 3": r3,
            "POST messages 3b": r3b,
            "GET conversations": rl,
            "GET messages": rm,
        }
        problemas = [
            f"{nome}: {p}"
            for nome, resp in checadas.items()
            if (p := vaza_dados(resp, proibidos))
        ]
        registrar(
            "4c. Respostas dos 4 endpoints sem '@' e sem sobrenome",
            not problemas,
            "nada encontrado" if not problemas else "; ".join(problemas),
        )
        html_no_get = MENSAGEM_HTML in textos(rm)
        registrar(
            "4e. GET devolve o texto com HTML idêntico",
            rm.status_code == 200 and html_no_get,
            f"HTTP {rm.status_code}, idêntico: {'sim' if html_no_get else 'não'}",
            rm,
        )
        rs = ler_sem_limite(dona, conversa_id)
        ds = json_ou_none(rs)
        lista = ds.get("messages") if isinstance(ds, dict) else None
        viu_sem_limite = isinstance(lista, list) and any(
            isinstance(m, dict) and m.get("text") == MENSAGEM_ACENTUADA for m in lista
        )
        registrar(
            "4d. Dona lê mensagens sem o parâmetro limit → 200",
            rs.status_code == 200 and viu_sem_limite,
            f"HTTP {rs.status_code}, vê a mensagem: {'sim' if viu_sem_limite else 'não'}",
            rs,
        )

        # 5. Não participante tenta ler e enviar.
        r = ler(estranha, conversa_id)
        registrar("5a. Não participante lê a conversa → 404", r.status_code == 404, f"HTTP {r.status_code}", r)
        r = enviar(estranha, conversa_id, "teste")
        registrar("5b. Não participante envia na conversa → 404", r.status_code == 404, f"HTTP {r.status_code}", r)

        # 6. Limites de tamanho.
        r = enviar(interessada, conversa_id, "")
        registrar("6a. Mensagem vazia → 400", r.status_code == 400, f"HTTP {r.status_code}", r)
        r = enviar(interessada, conversa_id, "a" * 1001)
        registrar("6b. Mensagem com 1001 caracteres → 400", r.status_code == 400, f"HTTP {r.status_code}", r)
        r = enviar(interessada, conversa_id, "á" * 1000)
        registrar("6c. Mensagem com 1000 'á' → sucesso", r.status_code == 200, f"HTTP {r.status_code}", r)

        # 7. Não participante sem conversas.
        r = listar(estranha)
        d = json_ou_none(r)
        vazia = isinstance(d, dict) and d.get("conversations") == []
        registrar(
            "7. Não participante lista conversas → lista vazia",
            r.status_code == 200 and vazia,
            f"HTTP {r.status_code}, lista vazia: {'sim' if vazia else 'não'}",
            r,
        )

        # 8. Rate limit: envia até o primeiro 429.
        print(
            f"\nCenário 8: enviando mensagens a cada {PAUSA_RATE_LIMIT_SEGUNDOS} s "
            "(envios aceitos antes nesta execução: até 3)..."
        )
        primeiro_429 = None
        r = None
        for n in range(1, LIMITE_TENTATIVAS_RATE_LIMIT + 1):
            time.sleep(PAUSA_RATE_LIMIT_SEGUNDOS)
            r = enviar(interessada, conversa_id, f"Teste de limite {n}", pausar=False)
            if r.status_code == 429:
                primeiro_429 = n
                break
            if r.status_code != 200:
                break
        if primeiro_429 is not None:
            dados = json_ou_none(r)
            mensagem = dados.get("message") if isinstance(dados, dict) else None
            do_chat = isinstance(mensagem, str) and MENSAGEM_LIMITE_CHAT in mensagem
            registrar(
                "8. Rate limit do chat → 429",
                do_chat,
                f"HTTP 429 no envio nº {primeiro_429} deste cenário"
                + ("" if do_chat else " (não é o 429 do endpoint; provável limite da plataforma)"),
                r,
            )
        else:
            registrar(
                "8. Rate limit do chat → 429",
                False,
                f"sem 429; último HTTP {r.status_code if r else '-'} após {n} envio(s)",
                r,
            )

        # 8b. O envio recusado com 429 não foi gravado.
        if primeiro_429 is None:
            print("Cenário 8b pulado: não houve 429.")
        else:
            recusado = f"Teste de limite {primeiro_429}"
            aceito = f"Teste de limite {primeiro_429 - 1}" if primeiro_429 > 1 else None
            r = ler(interessada, conversa_id)
            gravados = textos(r)
            nao_gravou = recusado not in gravados
            aceito_ok = aceito is None or aceito in gravados
            registrar(
                "8b. Mensagem recusada com 429 não foi gravada",
                r.status_code == 200 and nao_gravou and aceito_ok,
                f"HTTP {r.status_code}, recusada ausente: {'sim' if nao_gravou else 'não'}, "
                f"anterior aceita presente: {'sim' if aceito_ok else 'não'}",
                r,
            )

        # 9. (Opcional) Status: reservada permite envio; concluída só leitura.
        resposta = input(
            "\nMarcar a doação como reservada e depois concluída? "
            "Concluída não volta a outro status. (s/N) "
        ).strip().lower()
        if resposta != "s":
            print("Cenário 9 pulado: status mantido.")
        else:
            print(f"Aguardando {ESPERA_JANELA_SEGUNDOS} s para a janela do limite do chat esvaziar...")
            time.sleep(ESPERA_JANELA_SEGUNDOS)

            r = mudar_status("reservada")
            registrar("9a. Dona marca a doação como reservada → 200", r.status_code == 200, f"HTTP {r.status_code}", r)
            r = enviar(interessada, conversa_id, "Mensagem com a doação reservada")
            registrar("9b. Interessada envia com a doação reservada → 200", r.status_code == 200, f"HTTP {r.status_code}", r)

            r = mudar_status("concluída")
            registrar("9c. Dona marca a doação como concluída → 200", r.status_code == 200, f"HTTP {r.status_code}", r)
            r = enviar(interessada, conversa_id, "Mensagem com a doação concluída")
            registrar("9d. Interessada envia com a doação concluída → 404", r.status_code == 404, f"HTTP {r.status_code}", r)
            r = ler(interessada, conversa_id)
            registrar("9e. Interessada lê com a doação concluída → 200", r.status_code == 200, f"HTTP {r.status_code}", r)

        # 10. (Opcional) Dona apaga a doação; a conversa some para a interessada.
        resposta = input("\nApagar a doação de teste agora? (s/N) ").strip().lower()
        if resposta != "s":
            print("Cenário 10 pulado: doação mantida.")
        else:
            time.sleep(PAUSA_SEGUNDOS)
            rd = cliente.delete(
                f"{api}/catalog/donations",
                params={"donation_id": donation_id},
                headers=dona.headers,
            )
            dd = json_ou_none(rd)
            apagou = isinstance(dd, dict) and dd.get("deleted") is True
            registrar(
                "10a. Dona apaga a doação → sucesso",
                rd.status_code == 200 and apagou,
                f"HTTP {rd.status_code}",
                rd,
            )

            r = ler(interessada, conversa_id)
            registrar(
                "10b. Interessada lê a conversa da doação apagada → 404",
                r.status_code == 404,
                f"HTTP {r.status_code}",
                r,
            )

            r = listar(interessada)
            d = json_ou_none(r)
            conversas = d.get("conversations") if isinstance(d, dict) else None
            sumiu = isinstance(conversas, list) and not any(
                isinstance(c, dict) and c.get("conversation_id") == conversa_id for c in conversas
            )
            registrar(
                "10c. Interessada lista conversas → a conversa não aparece",
                r.status_code == 200 and sumiu,
                f"HTTP {r.status_code}, conversa ausente: {'sim' if sumiu else 'não'}",
                r,
            )

    resumo()


def resumo() -> None:
    falhas = [nome for nome, ok in resultados if not ok]
    print(f"\n=== Resumo: {len(resultados) - len(falhas)}/{len(resultados)} OK ===")
    for nome in falhas:
        print(f"  FALHOU: {nome}")


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido.")
