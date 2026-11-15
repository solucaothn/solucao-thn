"""Fotos do cadastro de doação (change fotos-formulario-doacao): funções puras.

- ``check_file``: o tipo (extensão e tipo do arquivo) e o limite de 5 MB, com as
  mensagens atuais.
- ``process_photo``: prepara a foto antes do envio, com as funções do recorte
  da foto de perfil (doafacil/recorte_foto.py): orientação EXIF aplicada,
  nenhum metadado, no máximo 1600 px no lado maior (sem ampliar), PNG só
  quando há transparência real e JPEG (qualidade 82, optimize) nos outros
  casos, e a
  miniatura de até 240 px.
- ``remove``, ``move`` e ``make_cover``: mudam a ordem; a primeira foto é a capa.

O Xano grava as fotos na ordem do envio e usa a primeira como capa; por isso
a ordem desta lista é a ordem salva.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from typing import Any

from doafacil.recorte_foto import PhotoImageError, encode_limited, make_preview, prepare_source


MAX_PHOTOS = 5
MAX_PHOTO_BYTES = 5 * 1024 * 1024
THUMB_MAX_SIDE = 240
IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
FORMAT_MESSAGE = "Selecione até cinco imagens JPEG, PNG, GIF ou WEBP."
SIZE_MESSAGE = "A foto pode ter no máximo 5 MB."
READ_ERROR_MESSAGE = "Não foi possível ler uma das imagens. Remova-a e tente novamente."
EMPTY_MESSAGE = "Uma das imagens está vazia. Remova-a e tente novamente."


@dataclass
class ProcessedPhoto:
    contents: bytes
    mime: str
    extension: str
    thumb: str


def check_file(filename: str, content_type: str, size: int) -> str:
    """Mensagem de erro atual para o arquivo, ou "" quando ele é aceito."""
    expected = IMAGE_TYPES.get(PurePath(filename or "").suffix.lower())
    if expected is None or (content_type and content_type != expected):
        return FORMAT_MESSAGE
    if size <= 0:
        return EMPTY_MESSAGE
    if size > MAX_PHOTO_BYTES:
        return SIZE_MESSAGE
    return ""


def process_photo(contents: bytes) -> ProcessedPhoto:
    """Prepara a foto para o envio. Gera ``PhotoImageError`` para uma imagem
    ilegível (mensagem de formato)."""
    source = prepare_source(contents)
    prepared, mime, extension = encode_limited(source)
    thumb, _, _ = make_preview(source.image, THUMB_MAX_SIDE)
    return ProcessedPhoto(contents=prepared, mime=mime, extension=extension, thumb=thumb)


def rejection_message(rejections: object) -> str:
    """Mensagem para arquivos recusados pelo próprio componente de upload:
    tamanho quando algum passou de 5 MB; nos outros casos, formato e limite."""
    codes: set[str] = set()
    for item in rejections if isinstance(rejections, list) else []:
        errors = item.get("errors") if isinstance(item, dict) else None
        for error in errors if isinstance(errors, list) else []:
            if isinstance(error, dict) and isinstance(error.get("code"), str):
                codes.add(error["code"])
    if "file-too-large" in codes:
        return SIZE_MESSAGE
    return FORMAT_MESSAGE


def _index(order: list[dict[str, Any]], photo_id: str) -> int:
    for position, photo in enumerate(order):
        if photo.get("id") == photo_id:
            return position
    return -1


def remove(order: list[dict[str, Any]], photo_id: str) -> list[dict[str, Any]]:
    return [photo for photo in order if photo.get("id") != photo_id]


def move(order: list[dict[str, Any]], photo_id: str, delta: int) -> list[dict[str, Any]]:
    """Troca a foto com a vizinha (delta -1: esquerda; +1: direita). Nas pontas
    ou com id desconhecido, a ordem não muda."""
    position = _index(order, photo_id)
    target = position + delta
    if position < 0 or delta not in (-1, 1) or not 0 <= target < len(order):
        return list(order)
    result = list(order)
    result[position], result[target] = result[target], result[position]
    return result


def make_cover(order: list[dict[str, Any]], photo_id: str) -> list[dict[str, Any]]:
    """Leva a foto para a primeira posição; as outras mantêm a ordem relativa."""
    position = _index(order, photo_id)
    if position <= 0:
        return list(order)
    return [order[position], *order[:position], *order[position + 1:]]


__all__ = [
    "MAX_PHOTOS",
    "MAX_PHOTO_BYTES",
    "PhotoImageError",
    "ProcessedPhoto",
    "check_file",
    "make_cover",
    "move",
    "process_photo",
    "rejection_message",
    "remove",
]
