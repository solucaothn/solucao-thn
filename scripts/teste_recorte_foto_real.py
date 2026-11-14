"""Roteiro de verificação manual do recorte da foto de perfil contra o Xano real.

Fica fora de tests/ de propósito: o unittest não deve executá-lo.

Uso (com o .venv ativo e as variáveis XANO_API_URL e XANO_AUTH_API_URL
definidas no ambiente):

    python scripts/teste_recorte_foto_real.py

Pede o e-mail e a senha de uma conta. As credenciais ficam só em memória. O
script gera as imagens de teste na memória, recorta com as mesmas funções do
modal “Ajustar foto” (doafacil/recorte_foto.py) e envia com o mesmo cliente da
página (upload_profile_photo). Não grava nada em arquivo e não imprime nomes,
e-mails, URLs nem corpos de resposta: só status HTTP, formatos, tamanhos e
sim/não.

O script ALTERA a foto de perfil da conta e, no fim, deixa a conta como estava:
sem foto, ou com a foto original reenviada (baixada antes do teste).

Cenários RC1 a RC8, mais o RC4b (decisões 4a e 7 do design da change
recorte-foto-perfil).
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from PIL import Image

# A raiz do projeto, para importar o doafacil (o script roda de scripts/).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doafacil.editar_perfil import (  # noqa: E402
    ProfileError,
    remove_profile_photo,
    upload_profile_photo,
)
from doafacil.recorte_foto import (  # noqa: E402
    OUTPUT_SIZE,
    crop_box,
    encode_square,
    make_preview,
    prepare_source,
)

# Reaproveita os auxiliares do teste do chat (mesma pasta scripts/).
from teste_chat_real import (  # noqa: E402
    Conta,
    base_url,
    json_ou_none,
    login,
    registrar,
    resumo,
)

PAUSA_SEGUNDOS = float(os.getenv("TESTE_RECORTE_PAUSA", "2.5"))
RED = (220, 20, 20)
GREEN = (20, 160, 60)
BLUE = (20, 40, 220)
YELLOW = (240, 220, 20)
EXIF_ORIENTATION = 0x0112
MARCA_EXIF = b"CameraRecorteTeste"


def quadrants(width: int, height: int, mode: str = "RGB") -> Image.Image:
    """Vermelho (sup. esq.), verde (sup. dir.), azul (inf. esq.), amarelo (inf. dir.)."""
    image = Image.new(mode, (width, height))
    half_w, half_h = width // 2, height // 2
    for color, box in (
        (RED, (0, 0, half_w, half_h)),
        (GREEN, (half_w, 0, width, half_h)),
        (BLUE, (0, half_h, half_w, height)),
        (YELLOW, (half_w, half_h, width, height)),
    ):
        image.paste(color if mode == "RGB" else color + (255,), box)
    return image


def encode(image: Image.Image, fmt: str, **params) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format=fmt, **params)
    return buffer.getvalue()


def jpeg_with_exif(image: Image.Image, orientation: int) -> bytes:
    """JPEG com orientação, marca/modelo e localização (GPS) de mentira."""
    exif = Image.Exif()
    exif[EXIF_ORIENTATION] = orientation
    exif[0x010F] = MARCA_EXIF.decode()
    exif[0x0110] = "ModeloRecorteTeste"
    gps = exif.get_ifd(0x8825)
    gps[1] = "S"
    gps[2] = (23.0, 32.0, 45.0)
    gps[3] = "W"
    gps[4] = (46.0, 38.0, 10.0)
    return encode(image, "JPEG", quality=95, exif=exif.tobytes())


def recorte(contents: bytes, area_relativa: tuple[float, float, float]) -> tuple[bytes, str, str]:
    """Faz o que o modal faz: prévia, área em pixels da prévia (x, y e lado,
    em frações da prévia) e o quadrado de 512 px."""
    source = prepare_source(contents)
    _, width, height = make_preview(source.image)
    fx, fy, fside = area_relativa
    side = fside * min(width, height)
    area = {"x": fx * width, "y": fy * height, "width": side, "height": side}
    box = crop_box(source.image.size, area, (width, height))
    return encode_square(source, box)


def perto(cor: tuple, esperada: tuple, tolerancia: int = 45) -> bool:
    return all(abs(a - b) <= tolerancia for a, b in zip(cor[:3], esperada[:3]))


def main() -> None:
    base_url("XANO_API_URL")
    auth = base_url("XANO_AUTH_API_URL")

    with httpx.Client(timeout=httpx.Timeout(60.0)) as cliente:
        conta = login(cliente, auth, "da pessoa")

        def pausa() -> None:
            time.sleep(PAUSA_SEGUNDOS)

        def perfil(c: Conta) -> httpx.Response:
            pausa()
            return cliente.get(f"{auth}/auth/profile", headers=c.headers)

        def baixar(url: str) -> httpx.Response | None:
            pausa()
            try:
                return cliente.get(url, follow_redirects=True)
            except httpx.HTTPError:
                return None

        def enviar(conteudo: bytes, nome: str, tipo: str) -> str | None:
            """Envia pelo mesmo cliente da página. Devolve a URL ou None."""
            pausa()

            async def run() -> str:
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as async_client:
                    return await upload_profile_photo(async_client, conta.token, nome, conteudo, tipo)

            try:
                return asyncio.run(run())
            except (ProfileError, httpx.HTTPError, ValueError) as erro:
                print(f"  envio falhou: {type(erro).__name__}")
                return None

        def remover() -> bool:
            pausa()

            async def run() -> None:
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as async_client:
                    await remove_profile_photo(async_client, conta.token)

            try:
                asyncio.run(run())
                return True
            except (ProfileError, httpx.HTTPError):
                return False

        def imagem_enviada(url: str | None) -> tuple[Image.Image | None, bytes, str]:
            if not url:
                return None, b"", "sem URL"
            resposta = baixar(url)
            if resposta is None or resposta.status_code != 200:
                return None, b"", "erro" if resposta is None else f"HTTP {resposta.status_code}"
            try:
                imagem = Image.open(BytesIO(resposta.content))
                imagem.load()
            except Exception:  # noqa: BLE001 - qualquer falha vira “não abre”
                return None, resposta.content, "não abre como imagem"
            return imagem, resposta.content, "HTTP 200"

        print("\n=== Preparação ===")
        r = perfil(conta)
        if r.status_code != 200:
            sys.exit(f"Não foi possível ler o perfil (HTTP {r.status_code}).")
        dados = json_ou_none(r)
        url_original = dados.get("photo") if isinstance(dados, dict) else None
        original: tuple[str, bytes, str] | None = None
        if isinstance(url_original, str) and urlsplit(url_original).scheme in {"http", "https"}:
            rb = baixar(url_original)
            if rb is not None and rb.status_code == 200 and rb.content:
                nome = urlsplit(url_original).path.rsplit("/", 1)[-1] or "foto.png"
                original = (nome, rb.content, rb.headers.get("content-type", "image/png"))
                print("A conta já tem foto; ela será reenviada no fim.")
            else:
                print("Aviso: não deu para baixar a foto original; no fim, a conta ficará sem foto.")
        else:
            print("A conta está sem foto; no fim, a conta ficará sem foto.")

        ultima_url: str | None = None
        try:
            print("\n=== Recorte e envio (RC1 a RC6) ===")

            # RC1. Quadrante superior direito (verde) de uma imagem 1600x1200.
            conteudo, nome, tipo = recorte(encode(quadrants(1600, 1200), "PNG"), (0.55, 0.05, 0.40))
            url = enviar(conteudo, nome, tipo)
            imagem, _, status = imagem_enviada(url)
            ok = (
                imagem is not None
                and imagem.size == (OUTPUT_SIZE, OUTPUT_SIZE)
                and perto(imagem.convert("RGB").getpixel((256, 256)), GREEN)
                and perto(imagem.convert("RGB").getpixel((10, 10)), GREEN)
                and perto(imagem.convert("RGB").getpixel((500, 500)), GREEN)
            )
            registrar("RC1. A área enquadrada (quadrante verde) vira 512 x 512 só com ela", ok, f"{status}, cor e tamanho certos: {'sim' if ok else 'não'}")
            ultima_url = url or ultima_url

            # RC2. JPEG com orientação EXIF 6 sai em pé (o sup. esq. vira azul).
            conteudo, nome, tipo = recorte(jpeg_with_exif(quadrants(1600, 1200), 6), (0.0, 0.0, 0.40))
            url = enviar(conteudo, nome, tipo)
            imagem, _, status = imagem_enviada(url)
            ok = (
                imagem is not None
                and imagem.format == "JPEG"
                and imagem.size == (OUTPUT_SIZE, OUTPUT_SIZE)
                and perto(imagem.convert("RGB").getpixel((256, 256)), BLUE)
            )
            registrar("RC2. Foto JPEG com orientação EXIF 6 sai em pé", ok, f"{status}, em pé: {'sim' if ok else 'não'}")
            ultima_url = url or ultima_url

            # RC3. PNG com transparência continua PNG com transparência.
            transparente = Image.new("RGBA", (800, 800), (0, 0, 0, 0))
            transparente.paste((20, 160, 60, 255), (300, 300, 500, 500))
            conteudo, nome, tipo = recorte(encode(transparente, "PNG"), (0.0, 0.0, 1.0))
            url = enviar(conteudo, nome, tipo)
            imagem, _, status = imagem_enviada(url)
            ok = (
                imagem is not None
                and imagem.format == "PNG"
                and imagem.convert("RGBA").getpixel((5, 5))[3] == 0
                and imagem.convert("RGBA").getpixel((256, 256))[3] == 255
            )
            registrar("RC3. PNG com transparência continua PNG com transparência", ok, f"{status}, transparência: {'sim' if ok else 'não'}")
            ultima_url = url or ultima_url

            # RC4. WEBP sem transparência vira JPEG antes do envio (decisão 4a).
            conteudo, nome, tipo = recorte(encode(quadrants(1000, 1000), "WEBP"), (0.1, 0.1, 0.3))
            url = enviar(conteudo, nome, tipo)
            imagem, _, status = imagem_enviada(url)
            ok = (
                tipo == "image/jpeg"
                and imagem is not None
                and imagem.format == "JPEG"
                and imagem.size == (OUTPUT_SIZE, OUTPUT_SIZE)
                and perto(imagem.convert("RGB").getpixel((256, 256)), RED)
            )
            registrar("RC4. WEBP sem transparência vira JPEG", ok, f"{status}, JPEG: {'sim' if ok else 'não'}")
            ultima_url = url or ultima_url

            # RC4b. WEBP com transparência vira PNG, com a transparência.
            transparente_webp = Image.new("RGBA", (800, 800), (0, 0, 0, 0))
            transparente_webp.paste((20, 40, 220, 255), (300, 300, 500, 500))
            conteudo, nome, tipo = recorte(encode(transparente_webp, "WEBP", lossless=True), (0.0, 0.0, 1.0))
            url = enviar(conteudo, nome, tipo)
            imagem, _, status = imagem_enviada(url)
            ok = (
                tipo == "image/png"
                and imagem is not None
                and imagem.format == "PNG"
                and imagem.convert("RGBA").getpixel((5, 5))[3] == 0
                and imagem.convert("RGBA").getpixel((256, 256))[3] == 255
            )
            registrar("RC4b. WEBP com transparência vira PNG com transparência", ok, f"{status}, PNG transparente: {'sim' if ok else 'não'}")
            ultima_url = url or ultima_url

            # RC5. GIF vira PNG estático.
            conteudo, nome, tipo = recorte(encode(quadrants(600, 600).convert("P"), "GIF"), (0.0, 0.0, 1.0))
            url = enviar(conteudo, nome, tipo)
            imagem, _, status = imagem_enviada(url)
            ok = tipo == "image/png" and imagem is not None and imagem.format == "PNG"
            registrar("RC5. GIF vira PNG", ok, f"{status}, PNG: {'sim' if ok else 'não'}")
            ultima_url = url or ultima_url

            # RC6. Os metadados (marca, modelo e localização) não chegam ao Xano.
            conteudo, nome, tipo = recorte(jpeg_with_exif(quadrants(1200, 1200), 1), (0.25, 0.25, 0.5))
            url = enviar(conteudo, nome, tipo)
            imagem, bruto, status = imagem_enviada(url)
            sem_metadados = (
                imagem is not None
                and dict(imagem.getexif()) == {}
                and MARCA_EXIF not in bruto
                and b"ModeloRecorteTeste" not in bruto
            )
            registrar("RC6. Sem EXIF, marca, modelo e localização no arquivo guardado", sem_metadados, f"{status}, sem metadados: {'sim' if sem_metadados else 'não'}")
            ultima_url = url or ultima_url

            print("\n=== Perfil (RC7) ===")
            # RC7. O GET auth/profile traz a URL do último envio.
            r = perfil(conta)
            atual = (json_ou_none(r) or {}).get("photo") if r.status_code == 200 else None
            ok = r.status_code == 200 and ultima_url is not None and atual == ultima_url
            registrar("RC7. GET auth/profile traz a URL da última foto enviada", ok, f"HTTP {r.status_code}, igual: {'sim' if ok else 'não'}", r)
        finally:
            print("\n=== Restauração (RC8) ===")
            if original is not None:
                nome, conteudo, tipo = original
                url = enviar(conteudo, nome, tipo)
                registrar("RC8. A foto original foi reenviada", url is not None, f"reenviada: {'sim' if url else 'não'}")
            else:
                registrar("RC8. A conta ficou sem foto, como estava", remover(), "removida")

    resumo()


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as erro:
        sys.exit(f"Erro de rede: {type(erro).__name__}")
    except KeyboardInterrupt:
        sys.exit("\nInterrompido.")
