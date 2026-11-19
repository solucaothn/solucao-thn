"""Vídeos dos cartões institucionais da home (change videos-home): os
arquivos de assets/landing/ conferidos sem ffprobe, lendo as caixas do MP4."""

import struct
import unittest
from pathlib import Path

from PIL import Image

LANDING = Path(__file__).resolve().parent.parent / "assets" / "landing"
NAMES = ("solidariedade", "seguranca", "missao", "passo-a-passo")
SIZE = 490
MAX_SECONDS = 8.0
# Caixas que contêm outras caixas (o resto é lido como folha).
CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"edts", b"dinf", b"udta"}


def _boxes(data: bytes, start: int = 0, end: int | None = None):
    """(tipo, início do conteúdo, fim) de cada caixa, recursivamente."""
    end = len(data) if end is None else end
    offset = start
    while offset + 8 <= end:
        size, kind = struct.unpack(">I4s", data[offset : offset + 8])
        header = 8
        if size == 1:
            size = struct.unpack(">Q", data[offset + 8 : offset + 16])[0]
            header = 16
        elif size == 0:
            size = end - offset
        if size < header:
            break
        body = offset + header
        yield kind, body, offset + size
        if kind in CONTAINERS:
            yield from _boxes(data, body, offset + size)
        offset += size


def describe_mp4(path: Path) -> dict:
    """Marca, duração, codecs de vídeo, tipos de faixa e tamanho da faixa de vídeo."""
    data = path.read_bytes()
    info = {"brand": b"", "seconds": None, "handlers": [], "codecs": [], "sizes": []}
    for kind, body, end in _boxes(data):
        if kind == b"ftyp":
            info["brand"] = data[body : body + 4]
        elif kind == b"mvhd":
            version = data[body]
            if version == 1:
                timescale, duration = struct.unpack(">IQ", data[body + 20 : body + 32])
            else:
                timescale, duration = struct.unpack(">II", data[body + 12 : body + 20])
            info["seconds"] = duration / timescale if timescale else None
        elif kind == b"hdlr":
            info["handlers"].append(data[body + 8 : body + 12])
        elif kind == b"stsd":
            # Primeira entrada: tamanho (4) + formato (4), depois do cabeçalho de 8.
            info["codecs"].append(data[body + 12 : body + 16])
        elif kind == b"tkhd":
            # Largura e altura (16.16) nos últimos 8 bytes da caixa.
            width, height = struct.unpack(">II", data[end - 8 : end])
            info["sizes"].append((width >> 16, height >> 16))
    return info


class LandingFilesTests(unittest.TestCase):
    def test_videos_h264_without_audio_short_and_490(self) -> None:
        for name in NAMES:
            with self.subTest(video=name):
                info = describe_mp4(LANDING / f"{name}.mp4")
                self.assertTrue(info["brand"], "sem caixa ftyp")
                self.assertIn(b"avc1", info["codecs"])  # H.264
                self.assertIn(b"vide", info["handlers"])
                self.assertNotIn(b"soun", info["handlers"])  # sem som
                self.assertIsNotNone(info["seconds"])
                self.assertLessEqual(info["seconds"], MAX_SECONDS)
                self.assertGreater(info["seconds"], 0)
                self.assertIn((SIZE, SIZE), info["sizes"])

    def test_posters_are_490_jpeg(self) -> None:
        for name in NAMES:
            with self.subTest(capa=name), Image.open(LANDING / f"{name}.jpg") as poster:
                self.assertEqual(poster.format, "JPEG")
                self.assertEqual(poster.size, (SIZE, SIZE))


if __name__ == "__main__":
    unittest.main()
