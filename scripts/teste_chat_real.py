"""Roteiro de verificação manual do backend do chat contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e as variáveis XANO_API_URL e XANO_AUTH_API_URL
definidas no ambiente):

    python scripts/teste_chat_real.py

As credenciais são pedidas no terminal e mantidas só em memória. O script não
grava nada em arquivo e não imprime tokens, e-mails nem corpos de resposta.

Atenção: o script cria dados reais (conversa e mensagens) na doação informada.
A paginação (8c-8h) usa as mensagens já criadas pela própria execução.
Os cenários de não lidas (NL1-NL8) rodam nos dois modos, inclusive no rápido
(TESTE_CHAT_RAPIDO=1); o unread_total é comparado com uma base medida antes
dos envios, porque soma todas as conversas da conta.
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
MENSAGEM_DONA = "Olá! Sim, ainda está disponível."
# Mensagens mínimas na conversa para os cenários de paginação (8d-8g):
# 3 últimas + 3 anteriores + 1 para has_older continuar verdadeiro.
MINIMO_PAGINACAO = 7
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


def estrutura(dados: object) -> str:
    """Só as chaves e o tamanho das listas; nunca valores nem textos."""
    if isinstance(dados, list):
        return f"lista({len(dados)})"
    if not isinstance(dados, dict):
        return type(dados).__name__
    partes = []
    for chave, valor in dados.items():
        if isinstance(valor, list):
            item = valor[0] if valor and isinstance(valor[0], dict) else None
            chaves_item = f" itens com [{', '.join(item)}]" if item else ""
            partes.append(f"{chave}: lista({len(valor)}){chaves_item}")
        else:
            partes.append(f"{chave}: {type(valor).__name__}")
    return "{" + "; ".join(partes) + "}"


def erro_resumido(resposta: httpx.Response | None) -> str:
    """Erro: só code e message. Resposta 2xx inesperada: só a estrutura.

    Nunca imprime o corpo inteiro, textos de mensagens, nomes ou tokens.
    """
    if resposta is None:
        return ""
    dados = json_ou_none(resposta)
    if 200 <= resposta.status_code < 300:
        return " | estrutura: " + estrutura(dados)
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

    rapido = os.getenv("TESTE_CHAT_RAPIDO", "").strip() == "1"
    if rapido:
        print("Modo rápido (TESTE_CHAT_RAPIDO=1): login, 2a, 3, 3c, duas leituras e não lidas (NL).")

    with httpx.Client(timeout=TIMEOUT) as cliente:
        dona = login(cliente, auth, "dona da doação")
        interessada = login(cliente, auth, "interessada")
        estranha = None if rapido else login(cliente, auth, "não participante")

        try:
            donation_id = int(input("\nID da doação (da dona, disponível, contato por chat): ").strip())
        except ValueError:
            sys.exit("ID da doação precisa ser um inteiro.")

        texto_email = "" if rapido else input(
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

        def ler_com(conta: Conta, conversa: int, **parametros: int) -> httpx.Response:
            # Leitura com cursores (before_message_id / after_message_id) e limit.
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.get(
                f"{api}/catalog/chat/messages",
                params={"conversation_id": conversa, **parametros},
                headers=conta.headers,
            )

        def lista_de_mensagens(resposta: httpx.Response) -> list[dict]:
            dados = json_ou_none(resposta)
            lista = dados.get("messages") if isinstance(dados, dict) else None
            if not isinstance(lista, list):
                return []
            return [m for m in lista if isinstance(m, dict)]

        def ids(mensagens: list[dict]) -> list[object]:
            return [m.get("id") for m in mensagens]

        def dados_da_doacao_ok(dados: object, status: str = "disponível") -> bool:
            return (
                isinstance(dados, dict)
                and isinstance(dados.get("donation_title"), str)
                and dados["donation_title"].strip() != ""
                and dados.get("donation_status") == status
            )

        def listar(conta: Conta) -> httpx.Response:
            # Sem parâmetros de propósito: é o caso do bug 1.
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.get(
                f"{api}/catalog/chat/conversations", headers=conta.headers
            )

        def total(conta: Conta | None) -> httpx.Response:
            # Sem conta: chamada sem token, para o cenário do 401.
            time.sleep(PAUSA_SEGUNDOS)
            return cliente.get(
                f"{api}/catalog/chat/unread_total",
                headers=conta.headers if conta else {},
            )

        if rapido:
            modo_rapido(
                iniciar, enviar, ler_com, lista_de_mensagens, listar, total, dona, interessada
            )
            return

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
        registrar(
            "2d. start devolve donation_title e donation_status “disponível”",
            dados_da_doacao_ok(d1) and dados_da_doacao_ok(d2),
            "campos presentes" if dados_da_doacao_ok(d1) and dados_da_doacao_ok(d2) else "campos ausentes ou inesperados",
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

        # 3c. A dona responde: o POST marca sent_by_me verdadeiro.
        r3c = enviar(dona, conversa_id, MENSAGEM_DONA)
        d = json_ou_none(r3c)
        proprio = isinstance(d, dict) and d.get("sent_by_me") is True
        registrar(
            "3c. Dona envia; POST devolve sent_by_me = true",
            r3c.status_code == 200 and proprio,
            f"HTTP {r3c.status_code}, sent_by_me verdadeiro: {'sim' if proprio else 'não'}",
            r3c,
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
            "POST messages 3c": r3c,
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

        # 4f. Título e status na lista de conversas e na leitura.
        item = next(
            (c for c in (conversas or []) if isinstance(c, dict) and c.get("conversation_id") == conversa_id),
            None,
        )
        campos_ok = dados_da_doacao_ok(item) and dados_da_doacao_ok(dm)
        registrar(
            "4f. Lista e leitura trazem donation_title e donation_status",
            campos_ok,
            "campos presentes" if campos_ok else "campos ausentes ou inesperados",
        )

        # 4g. sent_by_me depende de quem lê: a mesma mensagem muda de lado.
        ri = ler(interessada, conversa_id)
        por_dona = {m.get("text"): m.get("sent_by_me") for m in lista_de_mensagens(rm)}
        por_interessada = {m.get("text"): m.get("sent_by_me") for m in lista_de_mensagens(ri)}
        autoria_ok = (
            por_dona.get(MENSAGEM_DONA) is True
            and por_dona.get(MENSAGEM_ACENTUADA) is False
            and por_interessada.get(MENSAGEM_DONA) is False
            and por_interessada.get(MENSAGEM_ACENTUADA) is True
        )
        sem_sender_id = all("sender_id" not in m for m in lista_de_mensagens(rm) + lista_de_mensagens(ri))
        registrar(
            "4g. sent_by_me correto para cada leitor e sem sender_id",
            ri.status_code == 200 and autoria_ok and sem_sender_id,
            f"HTTP {ri.status_code}, autoria: {'ok' if autoria_ok else 'errada'}, "
            f"sem sender_id: {'sim' if sem_sender_id else 'não'}",
            ri,
        )

        # NL. Mensagens não lidas (antes do cenário 8, que esgota o limite de envio).
        cenarios_nao_lidas(
            conversa_id, dona, interessada, enviar, ler_com, lista_de_mensagens, listar, total
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
            "(envios aceitos antes nesta execução: até 6)..."
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

        # 8c-8h. Paginação do GET messages, usando as mensagens já criadas
        # (sem novos envios). Precisa de pelo menos MINIMO_PAGINACAO mensagens.
        rf = ler_com(dona, conversa_id, limit=100)
        todas = lista_de_mensagens(rf)
        todos_ids = ids(todas)
        crescente = todos_ids == sorted(todos_ids, key=lambda v: v if isinstance(v, int) else -1)
        registrar(
            "8c. Leitura com limit=100 vem em ordem cronológica",
            rf.status_code == 200 and len(todas) > 0 and crescente,
            f"HTTP {rf.status_code}, {len(todas)} mensagem(ns), crescente: {'sim' if crescente else 'não'}",
            rf,
        )
        if len(todas) < MINIMO_PAGINACAO or not crescente:
            print(
                f"Cenários 8d-8g pulados: a conversa tem {len(todas)} mensagem(ns) "
                f"e são necessárias pelo menos {MINIMO_PAGINACAO}."
            )
        else:
            # Últimas N: limit=3 sem cursor devolve as 3 mais recentes, em ordem crescente.
            r = ler_com(dona, conversa_id, limit=3)
            d = json_ou_none(r)
            ultimas = ids(lista_de_mensagens(r))
            ok = (
                r.status_code == 200
                and ultimas == todos_ids[-3:]
                and isinstance(d, dict)
                and d.get("has_older") is True
                and d.get("has_newer") is False
            )
            registrar(
                "8d. Sem cursor: últimas 3 em ordem crescente, has_older = true",
                ok,
                f"HTTP {r.status_code}, últimas corretas: {'sim' if ultimas == todos_ids[-3:] else 'não'}",
                r,
            )

            # Página anterior: before_message_id = a mais antiga das 3 últimas.
            r = ler_com(dona, conversa_id, before_message_id=todos_ids[-3], limit=3)
            d = json_ou_none(r)
            anteriores = ids(lista_de_mensagens(r))
            ainda_ha = len(todos_ids) > 6
            ok = (
                r.status_code == 200
                and anteriores == todos_ids[-6:-3]
                and isinstance(d, dict)
                and d.get("has_older") is ainda_ha
                and d.get("has_newer") is False
            )
            registrar(
                "8e. before_message_id: as 3 anteriores, has_older correto",
                ok,
                f"HTTP {r.status_code}, página anterior correta: {'sim' if anteriores == todos_ids[-6:-3] else 'não'}",
                r,
            )

            # Mensagens novas com mais do que o limite: has_newer = true.
            r = ler_com(dona, conversa_id, after_message_id=todos_ids[-6], limit=2)
            d = json_ou_none(r)
            novas = ids(lista_de_mensagens(r))
            ok = (
                r.status_code == 200
                and novas == todos_ids[-5:-3]
                and isinstance(d, dict)
                and d.get("has_newer") is True
                and d.get("has_older") is False
            )
            registrar(
                "8f. after_message_id com mais novas que o limite: has_newer = true",
                ok,
                f"HTTP {r.status_code}, novas corretas: {'sim' if novas == todos_ids[-5:-3] else 'não'}",
                r,
            )

            # Só a última é nova: has_newer = false.
            r = ler_com(dona, conversa_id, after_message_id=todos_ids[-2])
            d = json_ou_none(r)
            novas = ids(lista_de_mensagens(r))
            ok = (
                r.status_code == 200
                and novas == todos_ids[-1:]
                and isinstance(d, dict)
                and d.get("has_newer") is False
            )
            registrar(
                "8g. after_message_id da penúltima: só a última, has_newer = false",
                ok,
                f"HTTP {r.status_code}, só a última: {'sim' if novas == todos_ids[-1:] else 'não'}",
                r,
            )

        # Dois cursores juntos são recusados.
        primeiro_id = todos_ids[0] if todos_ids and isinstance(todos_ids[0], int) else 1
        r = ler_com(dona, conversa_id, before_message_id=primeiro_id + 1, after_message_id=primeiro_id)
        registrar(
            "8h. before_message_id e after_message_id juntos → 400",
            r.status_code == 400,
            f"HTTP {r.status_code}",
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
            concluida = dados_da_doacao_ok(json_ou_none(r), "concluída")
            registrar(
                "9e. Interessada lê com a doação concluída → 200 e donation_status “concluída”",
                r.status_code == 200 and concluida,
                f"HTTP {r.status_code}, status concluída: {'sim' if concluida else 'não'}",
                r,
            )

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


def contador_da_conversa(resposta: httpx.Response, conversa_id: int) -> object:
    """unread_count do item da conversa na lista, ou None se não aparecer."""
    dados = json_ou_none(resposta)
    conversas = dados.get("conversations") if isinstance(dados, dict) else None
    for item in conversas if isinstance(conversas, list) else []:
        if isinstance(item, dict) and item.get("conversation_id") == conversa_id:
            return item.get("unread_count")
    return None


def valor_total(resposta: httpx.Response) -> int | None:
    """unread_total, só se a resposta for exatamente {unread_total: int}."""
    dados = json_ou_none(resposta)
    if resposta.status_code != 200 or not isinstance(dados, dict) or set(dados) != {"unread_total"}:
        return None
    valor = dados["unread_total"]
    return valor if isinstance(valor, int) and not isinstance(valor, bool) else None


def cenarios_nao_lidas(
    conversa_id, dona, interessada, enviar, ler_com, lista_de_mensagens, listar, total
) -> None:
    """Contador de não lidas (chat-nao-lidas): unread_count, unread_total e leitura.

    O unread_total soma todas as conversas da conta, inclusive de testes
    anteriores; por isso é comparado com uma base medida antes dos envios.
    Imprime só status HTTP e números.
    """
    print("\n--- Não lidas ---")
    # Preparação: as duas leem a conversa inteira, o que zera a leitura de ambas.
    for conta in (dona, interessada):
        r = ler_com(conta, conversa_id, limit=100)
        if r.status_code != 200:
            registrar(f"NL0. {conta.papel} lê a conversa antes dos envios", False, f"HTTP {r.status_code}", r)
            return

    r_base_dona = total(dona)
    r_base_interessada = total(interessada)
    base_dona = valor_total(r_base_dona)
    base_interessada = valor_total(r_base_interessada)
    registrar(
        "NL1. unread_total responde só {unread_total: int} para as duas contas",
        base_dona is not None and base_interessada is not None,
        f"HTTP {r_base_dona.status_code} / {r_base_interessada.status_code}, "
        f"base da dona: {base_dona}, base da interessada: {base_interessada}",
        r_base_dona if base_dona is None else r_base_interessada,
    )
    if base_dona is None or base_interessada is None:
        return

    # A interessada envia 2 mensagens.
    envios = [enviar(interessada, conversa_id, f"Teste de não lidas {n}") for n in (1, 2)]
    enviou = all(r.status_code == 200 for r in envios)
    registrar(
        "NL2. Interessada envia 2 mensagens → sucesso",
        enviou,
        "HTTP " + " / ".join(str(r.status_code) for r in envios),
        next((r for r in envios if r.status_code != 200), None),
    )
    if not enviou:
        return

    # A dona vê 2 não lidas na conversa e no total.
    rl = listar(dona)
    contador = contador_da_conversa(rl, conversa_id)
    registrar(
        "NL3. Dona: unread_count da conversa = 2",
        rl.status_code == 200 and contador == 2,
        f"HTTP {rl.status_code}, unread_count: {contador}",
        rl,
    )
    rt = total(dona)
    valor = valor_total(rt)
    registrar(
        "NL4. Dona: unread_total = base + 2",
        valor == base_dona + 2,
        f"HTTP {rt.status_code}, total: {valor} (base {base_dona})",
        rt,
    )

    # Mensagens da própria pessoa não contam para quem enviou.
    rl = listar(interessada)
    contador = contador_da_conversa(rl, conversa_id)
    rt = total(interessada)
    valor = valor_total(rt)
    registrar(
        "NL5. Mensagens próprias não contam: interessada com unread_count 0 e total = base",
        rl.status_code == 200 and contador == 0 and valor == base_interessada,
        f"HTTP {rl.status_code} / {rt.status_code}, unread_count: {contador}, "
        f"total: {valor} (base {base_interessada})",
        rl if contador != 0 else rt,
    )

    # A dona lê: a conversa volta a 0 e o total volta à base.
    rm = ler_com(dona, conversa_id, limit=100)
    ids_lidos = [m.get("id") for m in lista_de_mensagens(rm)]
    rl = listar(dona)
    contador = contador_da_conversa(rl, conversa_id)
    rt = total(dona)
    valor = valor_total(rt)
    registrar(
        "NL6. Dona lê: unread_count 0 e unread_total = base",
        rm.status_code == 200 and contador == 0 and valor == base_dona,
        f"HTTP {rm.status_code} / {rl.status_code} / {rt.status_code}, "
        f"unread_count: {contador}, total: {valor} (base {base_dona})",
        rl if contador != 0 else rt,
    )

    # Carregar anteriores não volta a leitura: se voltasse para a penúltima,
    # a última mensagem (da interessada) voltaria a contar.
    if len(ids_lidos) >= 2 and isinstance(ids_lidos[-1], int):
        ra = ler_com(dona, conversa_id, before_message_id=ids_lidos[-1], limit=1)
        rl = listar(dona)
        contador = contador_da_conversa(rl, conversa_id)
        registrar(
            "NL7. Carregar anteriores não volta a leitura: unread_count continua 0",
            ra.status_code == 200 and rl.status_code == 200 and contador == 0,
            f"HTTP {ra.status_code} / {rl.status_code}, unread_count: {contador}",
            rl,
        )
    else:
        print("Cenário NL7 pulado: a leitura não trouxe ao menos 2 mensagens.")

    # Total sem sessão.
    r = total(None)
    registrar("NL8. unread_total sem token → 401", r.status_code == 401, f"HTTP {r.status_code}", r)


def modo_rapido(
    iniciar, enviar, ler_com, lista_de_mensagens, listar, total, dona, interessada
) -> None:
    """Checagem rápida: 2a, 3, 3c, duas leituras e não lidas, sem status nem exclusão.

    Imprime só status HTTP e tamanho da lista.
    Pode ser repetido com a mesma doação (respeitando 1 minuto entre execuções).
    """
    print("\n=== Modo rápido ===")
    r1 = iniciar(interessada)
    d1 = json_ou_none(r1)
    conversa_id = d1.get("conversation_id") if isinstance(d1, dict) else None
    registrar(
        "2a. Interessada inicia ou reabre a conversa → sucesso",
        r1.status_code == 200 and isinstance(conversa_id, int),
        f"HTTP {r1.status_code}",
        r1,
    )
    if not isinstance(conversa_id, int):
        resumo()
        return

    r3 = enviar(interessada, conversa_id, MENSAGEM_ACENTUADA)
    registrar("3. Interessada envia mensagem → sucesso", r3.status_code == 200, f"HTTP {r3.status_code}", r3)
    r3c = enviar(dona, conversa_id, MENSAGEM_DONA)
    registrar("3c. Dona envia mensagem → sucesso", r3c.status_code == 200, f"HTTP {r3c.status_code}", r3c)

    for rotulo, parametros in (("sem limit", {}), ("limit=100", {"limit": 100})):
        r = ler_com(dona, conversa_id, **parametros)
        tamanho = len(lista_de_mensagens(r))
        print(f"Leitura {rotulo}: HTTP {r.status_code}, messages={tamanho}")
        registrar(
            f"Leitura {rotulo} → ao menos 2 mensagens",
            r.status_code == 200 and tamanho >= 2,
            f"HTTP {r.status_code}, {tamanho} mensagem(ns)",
            r,
        )
    cenarios_nao_lidas(
        conversa_id, dona, interessada, enviar, ler_com, lista_de_mensagens, listar, total
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
