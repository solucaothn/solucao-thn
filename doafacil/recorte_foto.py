"""Enquadramento da foto de perfil (change recorte-foto-perfil).

- Funções puras do recorte, com o Pillow: abrir e reorientar (EXIF), gerar a
  prévia, calcular a área quadrada dentro da imagem e gerar o quadrado de
  512 × 512 sem metadados, sempre em JPEG ou PNG.
- O componente ``ImageCropper``: envolve o ``assets/recorte/image_cropper.jsx``
  (react-easy-crop). O enquadramento e o zoom ficam só no navegador; o Reflex
  recebe apenas a área final (``croppedAreaPixels``) no fim de cada gesto.

O Xano continua sendo a validação de segurança (formato e tamanho do arquivo
guardado). O recorte é conveniência.
"""

from __future__ import annotations

import base64
import math
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import reflex as rx
from PIL import Image, ImageOps, UnidentifiedImageError


OUTPUT_SIZE = 512
PREVIEW_MAX_SIDE = 1024
# Limite contra bombas de descompressão (o padrão do Pillow é maior).
MAX_PIXELS = 40_000_000
MIN_ZOOM = 1.0
MAX_ZOOM = 3.0
ZOOM_STEP = 0.1
CROPPER_VERSION = "react-easy-crop@6.2.4"
CROPPER_LIBRARY = "$/public/recorte/image_cropper.jsx"

# Formato real (do Pillow) → formato de saída. GIF vira PNG estático (1º quadro).
# WEBP nunca é enviado como WEBP: vira PNG com transparência e JPEG sem ela
# (decisão 4a do design), para o resultado não depender do Xano.
OUTPUT_FORMATS = {
    "JPEG": "JPEG",
    "MPO": "JPEG",  # fotos de algumas câmeras: JPEG com várias imagens
    "PNG": "PNG",
    "WEBP": "WEBP",  # resolvido em prepare_source: PNG ou JPEG
    "GIF": "PNG",
}
# Formato de saída → (nome fixo do arquivo, tipo).
OUTPUT_FILES = {
    "JPEG": ("foto.jpg", "image/jpeg"),
    "PNG": ("foto.png", "image/png"),
}


def _has_transparency(image: Image.Image) -> bool:
    """Há pelo menos um pixel não totalmente opaco."""
    if image.mode == "P" and "transparency" in image.info:
        image = image.convert("RGBA")
    if image.mode not in {"RGBA", "LA", "PA"}:
        return False
    alpha_min, _ = image.getchannel("A").getextrema()
    return alpha_min < 255

AREA_LABEL = (
    "Área de enquadramento. Use as setas para mover e as teclas mais e menos "
    "para o zoom."
)
ZOOM_LABEL = "Zoom"
ZOOM_OUT_LABEL = "Diminuir zoom"
ZOOM_IN_LABEL = "Aumentar zoom"


class PhotoImageError(Exception):
    """O arquivo não pode ser lido como imagem aceita (mensagem de formato)."""


class CropAreaError(Exception):
    """A área recebida não forma um recorte válido."""


@dataclass
class SourceImage:
    image: Image.Image
    output_format: str


def prepare_source(contents: bytes) -> SourceImage:
    """Abre a imagem, recusa formatos e tamanhos absurdos, usa o primeiro
    quadro do GIF e corrige a orientação EXIF. A imagem devolvida não tem
    metadados de origem."""
    try:
        opened = Image.open(BytesIO(contents))
        output_format = OUTPUT_FORMATS.get(opened.format or "")
        if output_format is None:
            raise PhotoImageError
        width, height = opened.size
        if width < 1 or height < 1 or width * height > MAX_PIXELS:
            raise PhotoImageError
        opened.seek(0)
        opened.load()
        oriented = ImageOps.exif_transpose(opened)
    except PhotoImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError) as error:
        raise PhotoImageError from error

    has_alpha = oriented.mode in {"RGBA", "LA", "PA"} or (
        oriented.mode == "P" and "transparency" in oriented.info
    )
    if output_format == "WEBP":
        # WEBP: PNG se algum pixel for transparente; senão, JPEG.
        output_format = "PNG" if _has_transparency(oriented) else "JPEG"
    mode = "RGBA" if has_alpha and output_format != "JPEG" else "RGB"
    converted = oriented.convert(mode)
    # Uma imagem nova, só com os pixels: nenhum EXIF, ICC ou texto de origem.
    clean = Image.new(mode, converted.size)
    clean.paste(converted)
    return SourceImage(image=clean, output_format=output_format)


def make_preview(image: Image.Image, max_side: int = PREVIEW_MAX_SIDE) -> tuple[str, int, int]:
    """Prévia para o navegador: no máximo ``max_side`` px no lado maior, como
    ``data:`` URL (JPEG sem transparência; PNG com). Devolve também o tamanho."""
    preview = image.copy()
    preview.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    if preview.mode == "RGBA":
        preview.save(buffer, format="PNG", optimize=True)
        mime = "image/png"
    else:
        preview.save(buffer, format="JPEG", quality=85)
        mime = "image/jpeg"
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:{mime};base64,{data}", preview.width, preview.height


def _number(area: Any, key: str) -> float:
    value = area.get(key) if isinstance(area, dict) else None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CropAreaError
    return float(value)


def crop_box(
    image_size: tuple[int, int],
    area: Any,
    preview_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    """Converte a área da prévia (``croppedAreaPixels``) para o original e
    devolve a caixa quadrada ``(esquerda, topo, direita, base)``.

    - Uma área não quadrada vira o maior quadrado centrado nela.
    - A área é limitada à imagem: deslocada para dentro e, se for maior que a
      imagem, reduzida ao menor lado dela.
    - Valores não numéricos, infinitos, ou largura ou altura menores que 1 px
      geram ``CropAreaError``.
    """
    image_width, image_height = image_size
    preview_width, preview_height = preview_size
    if min(image_width, image_height, preview_width, preview_height) < 1:
        raise CropAreaError
    scale_x = image_width / preview_width
    scale_y = image_height / preview_height

    x = _number(area, "x") * scale_x
    y = _number(area, "y") * scale_y
    width = _number(area, "width") * scale_x
    height = _number(area, "height") * scale_y
    if width < 1 or height < 1:
        raise CropAreaError

    side = min(width, height, image_width, image_height)
    # Centra o quadrado na área recebida.
    left = x + (width - side) / 2
    top = y + (height - side) / 2
    side_px = max(1, int(round(side)))
    left_px = min(max(int(round(left)), 0), image_width - side_px)
    top_px = min(max(int(round(top)), 0), image_height - side_px)
    return left_px, top_px, left_px + side_px, top_px + side_px


def _encode(
    image: Image.Image,
    output_format: str,
    jpeg_quality: int = 90,
    jpeg_optimize: bool = False,
) -> bytes:
    """Codifica sem metadados: copia só os pixels para uma imagem nova e salva
    em JPEG (RGB) ou PNG otimizado (mantém a transparência)."""
    clean = Image.new(image.mode, image.size)
    clean.paste(image)
    buffer = BytesIO()
    if output_format == "JPEG":
        clean.convert("RGB").save(
            buffer, format="JPEG", quality=jpeg_quality, optimize=jpeg_optimize
        )
    else:
        clean.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def encode_square(source: SourceImage, box: tuple[int, int, int, int]) -> tuple[bytes, str, str]:
    """Recorta a caixa, gera 512 × 512 e codifica no formato de saída, sem
    metadados. Devolve ``(conteúdo, nome fixo do arquivo, tipo)``."""
    square = source.image.crop(box).resize(
        (OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS
    )
    filename, mime = OUTPUT_FILES[source.output_format]
    return _encode(square, source.output_format), filename, mime


LIMITED_MAX_SIDE = 1600
LIMITED_JPEG_QUALITY = 82


def encode_limited(
    source: SourceImage,
    max_side: int = LIMITED_MAX_SIDE,
    jpeg_quality: int = LIMITED_JPEG_QUALITY,
) -> tuple[bytes, str, str]:
    """Imagem inteira com o lado maior de no máximo ``max_side`` px (mantém a
    proporção e nunca amplia), sem metadados. Usada nas fotos de doação
    (change fotos-formulario-doacao): PNG só quando há algum pixel
    transparente; sem transparência, JPEG (qualidade ``jpeg_quality``, com
    ``optimize``), mesmo que o original seja PNG ou GIF. Devolve
    ``(conteúdo, tipo, extensão)``."""
    image = source.image.copy()
    image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    output_format = "PNG" if _has_transparency(image) else "JPEG"
    filename, mime = OUTPUT_FILES[output_format]
    extension = filename.rsplit(".", 1)[1]
    content = _encode(image, output_format, jpeg_quality=jpeg_quality, jpeg_optimize=True)
    return content, mime, extension


# Componente --------------------------------------------------------------------


class ImageCropper(rx.NoSSRComponent):
    """Moldura circular do react-easy-crop, com o controle de zoom e os
    botões “Diminuir zoom” e “Aumentar zoom” (assets/recorte/image_cropper.jsx).

    O arraste, a roda do mouse, a pinça, as setas e as teclas + e - ficam no
    navegador. Só a área final vai ao estado, pelo ``on_crop_complete``.
    """

    library = CROPPER_LIBRARY
    lib_dependencies: list[str] = [CROPPER_VERSION]
    tag = "ImageCropper"
    is_default = True

    image: rx.Var[str]
    min_zoom: rx.Var[float]
    max_zoom: rx.Var[float]
    zoom_step: rx.Var[float]
    area_label: rx.Var[str]
    zoom_label: rx.Var[str]
    zoom_out_label: rx.Var[str]
    zoom_in_label: rx.Var[str]

    on_crop_complete: rx.EventHandler[lambda pixels: [pixels]]


def image_cropper(image: rx.Var, on_crop_complete: Any, **props: Any) -> rx.Component:
    return ImageCropper.create(
        image=image,
        min_zoom=MIN_ZOOM,
        max_zoom=MAX_ZOOM,
        zoom_step=ZOOM_STEP,
        area_label=AREA_LABEL,
        zoom_label=ZOOM_LABEL,
        zoom_out_label=ZOOM_OUT_LABEL,
        zoom_in_label=ZOOM_IN_LABEL,
        on_crop_complete=on_crop_complete,
        **props,
    )
