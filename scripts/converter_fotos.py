"""Converte fotos PNG do site para JPEG (change fotos-site).

Uso, na raiz do projeto, com o .venv ativo:

    python scripts/converter_fotos.py assets/sobre/quem-somos.png [outros.png ...]

Para cada PNG, grava um .jpg com o mesmo nome, na mesma pasta e com o mesmo
tamanho em pixels: qualidade 82, sem EXIF, ICC nem textos. Partes
transparentes (como os cantos arredondados exportados do Figma) ficam
brancas, a cor do fundo das páginas; os cantos arredondados vêm do CSS.
O PNG original não é alterado nem apagado.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

QUALITY = 82
BACKGROUND = (255, 255, 255)


def convert(png: Path) -> Path:
    """Converte um PNG e devolve o caminho do .jpg gravado."""
    jpg = png.with_suffix(".jpg")
    with Image.open(png) as source:
        image = source.convert("RGBA")
    flat = Image.new("RGB", image.size, BACKGROUND)
    flat.paste(image, mask=image.getchannel("A"))
    # Sem exif/icc_profile: o JPEG sai sem metadados.
    flat.save(jpg, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    return jpg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Converte fotos PNG do site para JPEG (qualidade 82, sem metadados).")
    parser.add_argument("pngs", nargs="+", type=Path, help="arquivos .png a converter")
    args = parser.parse_args(argv)
    for png in args.pngs:
        if png.suffix.lower() != ".png" or not png.is_file():
            print(f"Ignorado (não é um arquivo .png): {png}", file=sys.stderr)
            return 1
        jpg = convert(png)
        with Image.open(jpg) as out:
            size = out.size
        print(f"{png} -> {jpg} ({size[0]}x{size[1]}, {jpg.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
