"""Roteiro de verificação manual da foto de perfil contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e as variáveis XANO_API_URL e XANO_AUTH_API_URL
definidas no ambiente):

    python scripts/teste_foto_perfil_real.py

Pede o e-mail e a senha de duas contas: a dona de uma doação disponível com
contato por “Chat do DoaFácil” e outra pessoa (que inicia ou reabre a conversa
sobre essa doação). Pede também o ID da doação. As credenciais ficam só em
memória. O script gera as imagens de teste na memória (PNG pequeno, PNG com
mais de 5 MB, .txt e PDF), não grava nada em arquivo e não imprime nomes,
e-mails, URLs nem corpos de resposta: só status HTTP, chaves e sim/não.

O script ALTERA a foto de perfil da dona e, no fim, deixa a conta como estava:
sem foto, ou com a foto original reenviada (baixada antes do teste).
O início da conversa (FP10) cria a conversa se ela ainda não existir.

Cenários FP1 a FP12 (decisão 5 do design da change foto-perfil).
"""

from __future__ import annotations

import os
import struct
import sys
import time
import zlib
from typing import Any
from urllib.parse import urlsplit

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

PAUSA_SEGUNDOS = float(os.getenv("TESTE_FOTO_PAUSA", "2.5"))
LIMITE_BYTES = 5 * 1024 * 1024
MENSAGEM_FORMATO = "Envie uma imagem JPG, PNG, GIF ou WEBP."
MENSAGEM_TAMANHO = "A foto pode ter no máximo 5 MB."
# O selo e os contadores entraram na change perfil-credibilidade.
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


def png(largura: int, altura: int, nivel: int = 9) -> bytes:
    """PNG RGB de verdade, todo verde. Com nível 0 (sem compressão), o
    tamanho fica perto de largura × altura × 3 bytes."""

    def bloco(tipo: bytes, dados: bytes) -> bytes:
        return (
            struct.pack(">I", len(dados))
            + tipo
            + dados
            + struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF)
        )

    linha = b"\x00" + bytes((0, 122, 66)) * largura
    cabecalho = struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + bloco(b"IHDR", cabecalho)
        + bloco(b"IDAT", zlib.compress(linha * altura, nivel))
        + bloco(b"IEND", b"")
    )


PNG_PEQUENO = png(8, 8)
PNG_GRANDE = png(1400, 1300, nivel=0)
PDF_MINIMO = b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n"
TXT = "isto não é uma imagem".encode("utf-8")


def campo(resposta: httpx.Response, *caminho: str) -> object:
    dados: object = json_ou_none(resposta)
    for chave in caminho:
        if not isinstance(dados, dict):
            return None
        dados = dados.get(chave)
    return dados


def eh_url(valor: object) -> bool:
    return isinstance(valor, str) and urlsplit(valor).scheme in {"http", "https"}


def main() -> None:
    api = base_url("XANO_API_URL")
    auth = base_url("XANO_AUTH_API_URL")
    if len(PNG_GRANDE) <= LIMITE_BYTES:
        sys.exit("O PNG grande de teste precisa passar de 5 MB.")

    with httpx.Client(timeout=httpx.Timeout(60.0)) as cliente:
        dona = login(cliente, auth, "dona da doação")
        outra = login(cliente, auth, "outra pessoa")
        try:
            doacao_id = int(input("\nID de uma doação DISPONÍVEL da dona, com contato pelo chat: ").strip())
        except ValueError:
            sys.exit("O ID da doação precisa ser um inteiro.")

        def pedir(metodo: str, url: str, conta: Conta | None, **kwargs: Any) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            headers = conta.headers if conta else {}
            return cliente.request(metodo, url, headers=headers, **kwargs)

        def enviar(conta: Conta | None, nome: str, conteudo: bytes, tipo: str) -> httpx.Response:
            return pedir("POST", f"{auth}/auth/profile/photo", conta, files={"photo": (nome, conteudo, tipo)})

        def remover(conta: Conta | None) -> httpx.Response:
            return pedir("DELETE", f"{auth}/auth/profile/photo", conta)

        def perfil(conta: Conta) -> httpx.Response:
            return pedir("GET", f"{auth}/auth/profile", conta)

        def baixar(url: str) -> httpx.Response | None:
            """Segue os redirecionamentos (o armazenamento responde 303). None
            quando a requisição falha (rede, redirecionamento inválido)."""
            time.sleep(PAUSA_SEGUNDOS)
            try:
                return cliente.get(url, follow_redirects=True)
            except httpx.HTTPError:
                return None

        def abre(resposta: httpx.Response | None) -> bool:
            return resposta is not None and resposta.status_code == 200

        def nao_abre(resposta: httpx.Response | None) -> bool:
            return resposta is None or resposta.status_code in {403, 404, 410}

        def status(resposta: httpx.Response | None) -> str:
            return "erro" if resposta is None else f"HTTP {resposta.status_code}"

        print("\n=== Preparação ===")
        r = perfil(dona)
        foto_original_url = campo(r, "photo")
        foto_original: tuple[str, bytes, str] | None = None
        if r.status_code != 200:
            sys.exit(f"Não foi possível ler o perfil da dona (HTTP {r.status_code}).")
        if eh_url(foto_original_url):
            rb = baixar(str(foto_original_url))
            if abre(rb) and rb.content:
                nome = urlsplit(str(foto_original_url)).path.rsplit("/", 1)[-1] or "foto.png"
                foto_original = (nome, rb.content, rb.headers.get("content-type", "image/png"))
                print("A dona já tem foto; ela será reenviada no fim.")
            else:
                print(f"Aviso: não deu para baixar a foto original ({status(rb)}); no fim, a conta ficará sem foto.")
        else:
            print("A dona está sem foto; no fim, a conta ficará sem foto.")

        try:
            print("\n=== Envio (FP1 a FP6) ===")

            # FP1. Sem token → 401.
            r = enviar(None, "foto.png", PNG_PEQUENO, "image/png")
            registrar("FP1. Envio sem token → 401", r.status_code == 401, f"HTTP {r.status_code}", r)

            # FP2. PNG válido → 200 com a URL.
            r = enviar(dona, "foto-teste.png", PNG_PEQUENO, "image/png")
            url_1 = campo(r, "photo")
            ok = r.status_code == 200 and eh_url(url_1) and set(json_ou_none(r) or {}) == {"photo"}
            registrar("FP2. PNG válido → 200 só com a URL da foto", ok, f"HTTP {r.status_code}", r)
            if not ok:
                print("\nSem a primeira foto não dá para seguir. Encerrando.")
                return

            # FP3. GET auth/profile traz a mesma URL.
            r = perfil(dona)
            d = json_ou_none(r)
            ok = r.status_code == 200 and isinstance(d, dict) and set(d) == CHAVES_PERFIL and d.get("photo") == url_1
            registrar("FP3. GET auth/profile traz a mesma URL e só as chaves do perfil", ok, f"HTTP {r.status_code}", r)

            # FP4. Sem arquivo → 400 (o Xano recusa antes do stack, com a própria
            # mensagem, como “Missing param: photo”; a tela só envia com arquivo
            # escolhido); .txt e PDF → 400 com a mensagem de formato; a foto não muda.
            r_vazio = pedir("POST", f"{auth}/auth/profile/photo", dona, data={"sem_arquivo": "1"})
            r_txt = enviar(dona, "nota.txt", TXT, "text/plain")
            r_pdf = enviar(dona, "documento.pdf", PDF_MINIMO, "application/pdf")
            r_check = perfil(dona)
            ok = (
                r_vazio.status_code == 400
                and r_txt.status_code == 400
                and r_pdf.status_code == 400
                and campo(r_txt, "message") == MENSAGEM_FORMATO
                and campo(r_pdf, "message") == MENSAGEM_FORMATO
                and campo(r_check, "photo") == url_1
            )
            registrar(
                "FP4. Sem arquivo → 400; .txt e PDF → 400 com a mensagem de formato; foto mantida",
                ok,
                f"HTTP {r_vazio.status_code} / {r_txt.status_code} / {r_pdf.status_code}, "
                f"foto mantida: {'sim' if campo(r_check, 'photo') == url_1 else 'não'}",
                r_vazio if r_vazio.status_code != 400 else (r_txt if r_txt.status_code != 400 else r_pdf),
            )

            # FP5. Mais de 5 MB → 400 com a mensagem de tamanho, sem trocar a foto.
            r = enviar(dona, "grande.png", PNG_GRANDE, "image/png")
            r_check = perfil(dona)
            ok = r.status_code == 400 and campo(r, "message") == MENSAGEM_TAMANHO and campo(r_check, "photo") == url_1
            registrar(
                f"FP5. PNG de {len(PNG_GRANDE) / 1024 / 1024:.1f} MB → 400 com a mensagem de tamanho, sem trocar a foto",
                ok,
                f"HTTP {r.status_code}, foto mantida: {'sim' if campo(r_check, 'photo') == url_1 else 'não'}",
                r,
            )

            # FP6. Trocar a foto: URL nova, e o arquivo antigo é apagado.
            r = enviar(dona, "foto-teste-2.png", PNG_PEQUENO, "image/png")
            url_2 = campo(r, "photo")
            r_antiga = baixar(str(url_1))
            r_nova = baixar(str(url_2)) if eh_url(url_2) else None
            ok = (
                r.status_code == 200
                and eh_url(url_2)
                and url_2 != url_1
                and nao_abre(r_antiga)
                and abre(r_nova)
            )
            registrar(
                "FP6. Trocar a foto dá URL nova; a antiga deixa de abrir e a nova abre",
                ok,
                f"HTTP {r.status_code}, antiga: {status(r_antiga)}, nova: {status(r_nova)}",
                r,
            )
            url_atual = url_2 if eh_url(url_2) else url_1

            print("\n=== A foto nas outras respostas (FP7 a FP10) ===")

            # FP7. Minhas doações.
            r = pedir("GET", f"{api}/catalog/donations/mine", dona)
            ok = r.status_code == 200 and campo(r, "owner", "photo") == url_atual
            registrar("FP7. GET donations/mine traz owner.photo", ok, f"HTTP {r.status_code}", r)

            # FP8. Perfil público.
            r = pedir("GET", f"{api}/catalog/donations/donor", None, params={"donation_id": doacao_id})
            ok = r.status_code == 200 and campo(r, "donor", "photo") == url_atual and "@" not in r.text
            registrar("FP8. GET donations/donor traz donor.photo, sem e-mail", ok, f"HTTP {r.status_code}", r)

            # FP9. Detalhe da doação.
            r = pedir("GET", f"{api}/catalog/donations/detail", None, params={"donation_id": doacao_id})
            ok = r.status_code == 200 and campo(r, "donor_photo") == url_atual and "@" not in r.text
            registrar("FP9. GET donations/detail traz donor_photo, sem e-mail", ok, f"HTTP {r.status_code}", r)

            # FP10. A outra pessoa vê a foto no chat (lista e leitura); a dona não vê a própria.
            r_start = pedir("POST", f"{api}/catalog/chat/conversations/start", outra, json={"donation_id": doacao_id})
            conversa_id = campo(r_start, "conversation_id")
            if r_start.status_code != 200 or not isinstance(conversa_id, int):
                registrar(
                    "FP10. Foto da outra pessoa no chat",
                    False,
                    f"não foi possível iniciar a conversa (HTTP {r_start.status_code}); a doação aceita chat?",
                    r_start,
                )
            else:
                r_lista = pedir("GET", f"{api}/catalog/chat/conversations", outra, params={"limit": 50})
                itens = campo(r_lista, "conversations")
                item = next(
                    (i for i in itens if isinstance(i, dict) and i.get("conversation_id") == conversa_id),
                    None,
                ) if isinstance(itens, list) else None
                na_lista = isinstance(item, dict) and item.get("other_user_photo") == url_atual
                r_msgs = pedir("GET", f"{api}/catalog/chat/messages", outra, params={"conversation_id": conversa_id, "limit": 1})
                na_leitura = campo(r_msgs, "other_user_photo") == url_atual
                r_dona = pedir("GET", f"{api}/catalog/chat/messages", dona, params={"conversation_id": conversa_id, "limit": 1})
                nao_e_a_propria = r_dona.status_code == 200 and campo(r_dona, "other_user_photo") != url_atual
                registrar(
                    "FP10. A outra pessoa vê a foto na lista e na leitura; a dona não recebe a própria foto",
                    na_lista and na_leitura and nao_e_a_propria,
                    f"lista: {'sim' if na_lista else 'não'}, leitura: {'sim' if na_leitura else 'não'}, "
                    f"dona sem a própria: {'sim' if nao_e_a_propria else 'não'}",
                    r_lista if not na_lista else r_msgs,
                )

            print("\n=== Remoção (FP11 e FP12) ===")

            # FP11. DELETE: tudo volta nulo e o arquivo deixa de abrir. Para não
            # confundir com cache, a foto removida é uma nova, NUNCA aberta antes.
            r_nova_foto = enviar(dona, "foto-teste-3.png", PNG_PEQUENO, "image/png")
            url_nunca_aberta = campo(r_nova_foto, "photo")
            r = remover(dona)
            r_perfil = perfil(dona)
            r_mine = pedir("GET", f"{api}/catalog/donations/mine", dona)
            r_donor = pedir("GET", f"{api}/catalog/donations/donor", None, params={"donation_id": doacao_id})
            r_detail = pedir("GET", f"{api}/catalog/donations/detail", None, params={"donation_id": doacao_id})
            r_arquivo = baixar(str(url_nunca_aberta)) if eh_url(url_nunca_aberta) else None
            nulos = (
                campo(r, "photo") is None
                and campo(r_perfil, "photo") is None
                and campo(r_mine, "owner", "photo") is None
                and campo(r_donor, "donor", "photo") is None
                and campo(r_detail, "donor_photo") is None
            )
            registrar(
                "FP11. DELETE → 200; perfil, mine, donor e detail com a foto nula; o arquivo (nunca aberto antes) deixa de abrir",
                r_nova_foto.status_code == 200 and r.status_code == 200 and nulos and nao_abre(r_arquivo),
                f"envio HTTP {r_nova_foto.status_code}, DELETE HTTP {r.status_code}, tudo nulo: "
                f"{'sim' if nulos else 'não'}, arquivo depois: {status(r_arquivo)}",
                r,
            )

            # FP12. DELETE sem foto → 200.
            r = remover(dona)
            registrar("FP12. DELETE sem foto → 200", r.status_code == 200 and campo(r, "photo") is None, f"HTTP {r.status_code}", r)
        finally:
            print("\n=== Restauração ===")
            if foto_original is not None:
                nome, conteudo, tipo = foto_original
                r = enviar(dona, nome, conteudo, tipo)
                registrar("Restauração: a foto original foi reenviada", r.status_code == 200 and eh_url(campo(r, "photo")), f"HTTP {r.status_code}", r)
            else:
                r = remover(dona)
                registrar("Restauração: a conta ficou sem foto, como estava", r.status_code == 200, f"HTTP {r.status_code}", r)

    resumo()


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido.")
