"""Roteiro de verificação manual das fotos do cadastro de doação contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e as variáveis XANO_API_URL e XANO_AUTH_API_URL
definidas no ambiente):

    python scripts/teste_fotos_formulario_real.py

Pede o e-mail e a senha de uma conta com cidade e estado no perfil. As
credenciais ficam só em memória. O script gera três fotos de cores diferentes
na memória (vermelha, verde e azul; a verde é um JPEG com EXIF de orientação,
marca, modelo e GPS), prepara cada uma com as mesmas funções do cadastro
(doafacil/fotos_doacao.py), muda a ordem com “Tornar capa” e “Mover” para
azul, vermelha, verde e publica pelo mesmo cliente da página
(_publish_donation). Não grava nada em arquivo e não imprime nomes, e-mails,
URLs, títulos nem corpos de resposta: só status HTTP, cores, tamanhos e
sim/não.

O script CRIA uma doação de teste e a APAGA no fim, mesmo se der erro no meio.
A medição FF8 cria mais duas doações (5 fotos de celular com a regra antiga e
com a nova, para comparar o tempo da publicação) e também as apaga.

Cenários FF1 a FF8 (decisões 7 e 4c do design da change fotos-formulario-doacao).
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image

# A raiz do projeto, para importar o doafacil (o script roda de scripts/).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doafacil.cadastro_doacao import (  # noqa: E402
    DonationServiceError,
    _photos_payload,
    _publish_donation,
)
from doafacil.fotos_doacao import make_cover, move, process_photo  # noqa: E402

# Reaproveita os auxiliares do teste do chat (mesma pasta scripts/).
from teste_chat_real import (  # noqa: E402
    base_url,
    json_ou_none,
    login,
    registrar,
    resumo,
)

PAUSA_SEGUNDOS = float(os.getenv("TESTE_FOTOS_FORMULARIO_PAUSA", "2.5"))
RED = (220, 20, 20)
GREEN = (20, 160, 60)
BLUE = (20, 40, 220)
EXIF_ORIENTATION = 0x0112
MARCA = b"MarcaFormularioTeste"
MODELO = b"ModeloFormularioTeste"


def encode(image: Image.Image, fmt: str, **params) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format=fmt, **params)
    return buffer.getvalue()


def jpeg_com_metadados(image: Image.Image) -> bytes:
    """JPEG com orientação 6 (girado), marca, modelo e GPS de mentira."""
    exif = Image.Exif()
    exif[EXIF_ORIENTATION] = 6
    exif[0x010F] = MARCA.decode()
    exif[0x0110] = MODELO.decode()
    gps = exif.get_ifd(0x8825)
    gps[1] = "S"
    gps[2] = (23.0, 32.0, 45.0)
    gps[3] = "W"
    gps[4] = (46.0, 38.0, 10.0)
    return encode(image, "JPEG", quality=95, exif=exif.tobytes())


def perto(cor: tuple, esperada: tuple, tolerancia: int = 45) -> bool:
    return all(abs(a - b) <= tolerancia for a, b in zip(cor[:3], esperada[:3]))


def nome_da_cor(cor: tuple) -> str:
    for nome, referencia in (("vermelha", RED), ("verde", GREEN), ("azul", BLUE)):
        if perto(cor, referencia):
            return nome
    return "outra"


def preparar_fotos() -> tuple[list[dict], dict[str, tuple[bytes, str, str]]]:
    """As três fotos como o cadastro as guarda, já na ordem azul, vermelha,
    verde (montada com make_cover e move, como na tela)."""
    originais = {
        "vermelha": encode(Image.new("RGB", (800, 600), RED), "PNG"),
        "verde": jpeg_com_metadados(Image.new("RGB", (400, 300), GREEN)),
        "azul": encode(Image.new("RGB", (900, 600), BLUE), "PNG"),
    }
    fotos: list[dict] = []
    arquivos: dict[str, tuple[bytes, str, str]] = {}
    for nome, conteudo in originais.items():
        preparada = process_photo(conteudo)
        fotos.append({"id": nome, "thumb": preparada.thumb})
        arquivos[nome] = (preparada.contents, preparada.mime, preparada.extension)
    # Escolha: vermelha, verde, azul → tornar a azul capa → azul, vermelha, verde.
    fotos = make_cover(fotos, "azul")
    fotos = move(fotos, "verde", 1)  # já é a última: a ordem não muda
    return fotos, arquivos


def foto_realista(largura: int, altura: int, semente: int) -> bytes:
    """JPEG com textura (ruído, desfoque e gradiente), que comprime como uma
    foto de celular, e não como uma cor lisa."""
    from PIL import ImageFilter

    ruido = Image.effect_noise((largura // 4, altura // 4), 60 + semente).convert("L")
    ruido = ruido.resize((largura, altura), Image.Resampling.BICUBIC)
    base = Image.merge("RGB", (
        Image.linear_gradient("L").resize((largura, altura)),
        ruido,
        Image.linear_gradient("L").rotate(90).resize((largura, altura)),
    ))
    detalhe = Image.effect_noise((largura, altura), 25).convert("RGB")
    return encode(Image.blend(base, detalhe, 0.25).filter(ImageFilter.SMOOTH), "JPEG", quality=92)


def preparar_regra_antiga(conteudo: bytes) -> tuple[bytes, str, str]:
    """A regra anterior ao ajuste, só para a medição: lado maior de 2048 px,
    JPEG com qualidade 90 sem optimize e PNG mantido como PNG."""
    from doafacil.recorte_foto import OUTPUT_FILES, _encode, prepare_source

    fonte = prepare_source(conteudo)
    imagem = fonte.image.copy()
    imagem.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
    nome, tipo = OUTPUT_FILES[fonte.output_format]
    return _encode(imagem, fonte.output_format), tipo, nome.rsplit(".", 1)[1]


def main() -> None:
    api = base_url("XANO_API_URL")
    auth = base_url("XANO_AUTH_API_URL")

    with httpx.Client(timeout=httpx.Timeout(60.0)) as cliente:
        conta = login(cliente, auth, "da pessoa")

        def pedir(metodo: str, url: str, autenticado: bool = False, **kwargs) -> httpx.Response:
            time.sleep(PAUSA_SEGUNDOS)
            headers = conta.headers if autenticado else {}
            return cliente.request(metodo, url, headers=headers, **kwargs)

        def baixar(url: object) -> Image.Image | None:
            if not isinstance(url, str) or not url.startswith("http"):
                return None
            time.sleep(PAUSA_SEGUNDOS)
            try:
                resposta = cliente.get(url, follow_redirects=True)
            except httpx.HTTPError:
                return None
            if resposta.status_code != 200:
                return None
            try:
                imagem = Image.open(BytesIO(resposta.content))
                imagem.load()
            except Exception:  # noqa: BLE001 - qualquer falha vira “não abre”
                return None
            imagem.info["_bytes"] = resposta.content
            return imagem

        def cor_central(imagem: Image.Image | None) -> tuple:
            if imagem is None:
                return (-999, -999, -999)
            rgb = imagem.convert("RGB")
            return rgb.getpixel((rgb.width // 2, rgb.height // 2))

        print("\n=== Preparação ===")
        r = pedir("GET", f"{api}/catalog/categories")
        categorias = json_ou_none(r)
        categoria = next(
            (c.get("id") for c in categorias or [] if isinstance(c, dict) and isinstance(c.get("id"), int)
             and str(c.get("name", "")).strip().casefold() not in {"alimentos", "móveis"}),
            None,
        )
        if r.status_code != 200 or categoria is None:
            sys.exit(f"Não foi possível ler as categorias (HTTP {r.status_code}).")
        fotos, arquivos = preparar_fotos()
        ordem = [foto["id"] for foto in fotos]
        print(f"Ordem escolhida: {', '.join(ordem)}")

        doacao_id: int | None = None
        extras: list[int] = []
        try:
            print("\n=== Publicação (FF1) ===")
            payload = {
                "category_id": categoria,
                "title": "Teste de fotos do formulário",
                "description": "Doação de teste criada e apagada pelo script.",
                "condition": "Bom",
                "delivery_method": "A combinar",
                "contact_preference": "Chat do DoaFácil",
            }
            enviadas = _photos_payload(fotos, arquivos)
            # Fotos sem transparência vão em JPEG, mesmo as que eram PNG.
            nomes_ok = [nome for nome, _, _ in enviadas] == ["foto-1.jpg", "foto-2.jpg", "foto-3.jpg"]

            async def publicar() -> dict:
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as async_client:
                    return await _publish_donation(
                        async_client, f"{api}/catalog/donations/publish", conta.token, payload, enviadas
                    )

            time.sleep(PAUSA_SEGUNDOS)
            try:
                doacao = asyncio.run(publicar())
                doacao_id = doacao.get("id")
            except DonationServiceError as erro:
                registrar("FF1. Publicação com três fotos na ordem escolhida", False, f"falhou: {type(erro).__name__}")
                return
            registrar(
                "FF1. Publicação com três fotos na ordem escolhida → doação disponível",
                isinstance(doacao_id, int) and nomes_ok,
                f"criada: {'sim' if isinstance(doacao_id, int) else 'não'}, nomes foto-N: {'sim' if nomes_ok else 'não'}",
            )

            print("\n=== Ordem e capa (FF2 a FF4) ===")
            r_detalhe = pedir("GET", f"{api}/catalog/donations/detail", params={"donation_id": doacao_id})
            urls = (json_ou_none(r_detalhe) or {}).get("photos") if r_detalhe.status_code == 200 else None
            imagens = [baixar(url) for url in urls] if isinstance(urls, list) else []
            cores = [nome_da_cor(cor_central(imagem)) for imagem in imagens]
            registrar(
                "FF2. O detalhe traz as fotos na ordem escolhida (azul, vermelha, verde)",
                cores == ["azul", "vermelha", "verde"],
                f"HTTP {r_detalhe.status_code}, ordem: {', '.join(cores) or 'nenhuma'}",
                r_detalhe,
            )

            r_mine = pedir("GET", f"{api}/catalog/donations/mine", autenticado=True)
            itens = (json_ou_none(r_mine) or {}).get("items") if r_mine.status_code == 200 else None
            item = next((i for i in itens or [] if isinstance(i, dict) and i.get("id") == doacao_id), None)
            capa_mine = nome_da_cor(cor_central(baixar(item.get("photo")))) if item else "ausente"
            capa_detalhe = cores[0] if cores else "ausente"
            registrar(
                "FF3. A capa do detalhe e a do cartão em “Minhas doações” são a azul",
                capa_detalhe == "azul" and capa_mine == "azul",
                f"detalhe: {capa_detalhe}, Minhas doações: {capa_mine}",
                r_mine,
            )

            r_donor = pedir("GET", f"{api}/catalog/donations/donor", params={"donation_id": doacao_id})
            itens = (json_ou_none(r_donor) or {}).get("items") if r_donor.status_code == 200 else None
            item = next((i for i in itens or [] if isinstance(i, dict) and i.get("id") == doacao_id), None)
            capa_publica = nome_da_cor(cor_central(baixar(item.get("photo")))) if item else "ausente"
            registrar(
                "FF4. A capa no perfil público é a azul",
                capa_publica == "azul",
                f"HTTP {r_donor.status_code}, capa: {capa_publica}",
                r_donor,
            )

            print("\n=== Metadados (FF5) ===")
            verde = imagens[2] if len(imagens) == 3 else None
            bruto = verde.info.get("_bytes", b"") if verde is not None else b""
            sem_metadados = (
                verde is not None
                and dict(verde.getexif()) == {}
                and MARCA not in bruto
                and MODELO not in bruto
            )
            em_pe = verde is not None and verde.size == (300, 400)
            registrar(
                "FF5. A foto com EXIF e GPS chega sem metadados e em pé",
                sem_metadados and em_pe,
                f"sem metadados: {'sim' if sem_metadados else 'não'}, em pé: {'sim' if em_pe else 'não'}",
            )

            print("\n=== Medição: 5 fotos de celular, regra antiga x nova (FF8) ===")
            originais = [foto_realista(4032, 3024, semente) for semente in range(5)]
            medidas: dict[str, tuple[float, float, float]] = {}
            for regra in ("antiga", "nova"):
                inicio = time.perf_counter()
                if regra == "antiga":
                    preparadas = [preparar_regra_antiga(conteudo) for conteudo in originais]
                else:
                    preparadas = [
                        (p.contents, p.mime, p.extension)
                        for p in (process_photo(conteudo) for conteudo in originais)
                    ]
                tempo_preparo = time.perf_counter() - inicio
                lista = [{"id": str(n)} for n in range(5)]
                arquivos_medicao = {str(n): preparadas[n] for n in range(5)}
                envio = _photos_payload(lista, arquivos_medicao)
                kb = sum(len(conteudo) for _, conteudo, _ in envio) / 1024

                async def publicar_medicao(fotos_envio=envio) -> dict:
                    async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as async_client:
                        return await _publish_donation(
                            async_client, f"{api}/catalog/donations/publish", conta.token,
                            {**payload, "title": "Teste de tempo de publicação"}, fotos_envio,
                        )

                time.sleep(PAUSA_SEGUNDOS)
                inicio = time.perf_counter()
                try:
                    criada = asyncio.run(publicar_medicao())
                except DonationServiceError:
                    criada = {}
                tempo_xano = time.perf_counter() - inicio
                if isinstance(criada.get("id"), int):
                    extras.append(criada["id"])
                medidas[regra] = (tempo_preparo, kb, tempo_xano)
                print(
                    f"Regra {regra}: preparo {tempo_preparo:.1f} s (na escolha), "
                    f"enviado {kb:.0f} KB, requisição ao Xano {tempo_xano:.1f} s"
                )
            registrar(
                "FF8. Medição publicada com a regra antiga e a nova",
                len(extras) == 2,
                "tempos acima" if len(extras) == 2 else "uma das publicações falhou",
            )
        finally:
            for extra in extras:
                r = pedir("DELETE", f"{api}/catalog/donations", autenticado=True, params={"donation_id": extra})
                print(f"Doação da medição apagada: HTTP {r.status_code}")
            print("\n=== Limpeza (FF6 e FF7) ===")
            if isinstance(doacao_id, int):
                r = pedir("DELETE", f"{api}/catalog/donations", autenticado=True, params={"donation_id": doacao_id})
                registrar("FF6. A doação de teste foi apagada", r.status_code == 200, f"HTTP {r.status_code}", r)
                r = pedir("GET", f"{api}/catalog/donations/detail", params={"donation_id": doacao_id})
                registrar("FF7. O detalhe da doação apagada responde 404", r.status_code == 404, f"HTTP {r.status_code}", r)
            else:
                print("Nenhuma doação foi criada; nada a apagar.")

    resumo()


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido.")
