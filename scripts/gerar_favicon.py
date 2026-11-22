"""Gera o favicon do DoaFácil a partir do símbolo do assets/logo.svg
(change acabamento).

Precisa do PyMuPDF, que NÃO está no requirements.txt (o site não usa). Na
raiz do projeto, com o .venv ativo:

    pip install -r requirements-dev.txt
    python scripts/gerar_favicon.py

Grava, prontos para o commit:
- assets/favicon.ico (16, 32 e 48 px, fundo transparente);
- assets/favicon-32.png (32 px, fundo transparente);
- assets/apple-touch-icon.png (180 px, fundo branco: o iOS não usa
  transparência).

O símbolo é a maior mancha de tinta conectada do logotipo (ver
crop_symbol): a ponta da folha passa por cima do “d”, então não dá para
separar símbolo e texto por um vão entre colunas.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "logo.svg"
ICO = ROOT / "assets" / "favicon.ico"
PNG_32 = ROOT / "assets" / "favicon-32.png"
TOUCH = ROOT / "assets" / "apple-touch-icon.png"
SCALE = 8  # renderiza o SVG 8x maior que o tamanho original
PADDING = 0.08  # respiro do apple-touch-icon, em fração do lado
MIN_INSIDE = 0.5  # fração da caixa de uma mancha dentro do símbolo para ela entrar nele


def render_logo() -> Image.Image:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.exit("Instale o PyMuPDF: pip install -r requirements-dev.txt")
    document = fitz.open(str(LOGO))
    page = document.load_page(0)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=True)
    return Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGBA")


def ink_blobs(logo: Image.Image) -> list[tuple[list[int], tuple[int, int, int, int]]]:
    """Manchas de tinta conectadas (vizinhança 4): (índices dos pixels, caixa x0, y0, x1, y1)."""
    width, height = logo.size
    ink = bytearray(1 if value > 16 else 0 for value in logo.getchannel("A").tobytes())
    blobs = []
    for start in range(width * height):
        if not ink[start]:
            continue
        ink[start] = 0
        stack, pixels = [start], []
        x0, y0, x1, y1 = width, height, -1, -1
        while stack:
            index = stack.pop()
            pixels.append(index)
            y, x = divmod(index, width)
            x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
            neighbours = []
            if x > 0:
                neighbours.append(index - 1)
            if x < width - 1:
                neighbours.append(index + 1)
            if y > 0:
                neighbours.append(index - width)
            if y < height - 1:
                neighbours.append(index + width)
            for other in neighbours:
                if ink[other]:
                    ink[other] = 0
                    stack.append(other)
        blobs.append((pixels, (x0, y0, x1 + 1, y1 + 1)))
    return blobs


def inside_fraction(box: tuple[int, int, int, int], region: tuple[int, int, int, int]) -> float:
    """Fração da área de box que fica dentro de region."""
    width = min(box[2], region[2]) - max(box[0], region[0])
    height = min(box[3], region[3]) - max(box[1], region[1])
    if width <= 0 or height <= 0:
        return 0.0
    return width * height / ((box[2] - box[0]) * (box[3] - box[1]))


def crop_symbol(logo: Image.Image) -> Image.Image:
    """Parte da maior mancha de tinta (mão e folha) e junta as manchas com pelo
    menos MIN_INSIDE da caixa dentro da caixa do símbolo (o coração, os
    brilhos), até estabilizar. A ponta da folha passa por cima do “d”, então
    não há coluna vazia entre símbolo e texto: o recorte é por manchas, não
    por vão entre colunas. O “d” fica só ~1/3 dentro da caixa e sai."""
    blobs = ink_blobs(logo)
    blobs.sort(key=lambda blob: len(blob[0]), reverse=True)
    chosen = {0}
    region = blobs[0][1]
    grew = True
    while grew:
        grew = False
        for number, (_, box) in enumerate(blobs):
            if number not in chosen and inside_fraction(box, region) >= MIN_INSIDE:
                chosen.add(number)
                region = (min(region[0], box[0]), min(region[1], box[1]), max(region[2], box[2]), max(region[3], box[3]))
                grew = True
    left, top, right, bottom = region
    keep = bytearray(logo.width * logo.height)
    for number in chosen:
        for index in blobs[number][0]:
            keep[index] = 255
    mask = Image.frombytes("L", logo.size, bytes(keep))
    symbol = Image.new("RGBA", logo.size, (0, 0, 0, 0))
    symbol.paste(logo, (0, 0), mask)
    return symbol.crop((left, top, right, bottom))


def square(symbol: Image.Image, background: tuple[int, int, int, int], padding: float) -> Image.Image:
    side = int(max(symbol.size) * (1 + 2 * padding))
    canvas = Image.new("RGBA", (side, side), background)
    canvas.alpha_composite(symbol, ((side - symbol.width) // 2, (side - symbol.height) // 2))
    return canvas


def main() -> int:
    symbol = crop_symbol(render_logo())
    # Na aba do navegador o ícone vai de ponta a ponta: em 16/32 px qualquer
    # respiro encolhe o símbolo (que é vazado). O iOS arredonda os cantos do
    # apple-touch-icon, então ali o respiro fica.
    transparent = square(symbol, (0, 0, 0, 0), padding=0)
    transparent.resize((48, 48), Image.LANCZOS).save(ICO, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    transparent.resize((32, 32), Image.LANCZOS).save(PNG_32, format="PNG", optimize=True)
    white = square(symbol, (255, 255, 255, 255), padding=PADDING).convert("RGB")
    white.resize((180, 180), Image.LANCZOS).save(TOUCH, format="PNG", optimize=True)
    for path in (ICO, PNG_32, TOUCH):
        print(f"{path.relative_to(ROOT)} ({path.stat().st_size // 1024 or 1} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
