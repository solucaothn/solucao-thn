"""Change fotos-site: conversão das fotos PNG para JPEG."""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("converter_fotos", ROOT / "scripts" / "converter_fotos.py")
converter_fotos = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(converter_fotos)


class ConvertTests(unittest.TestCase):
    def test_png_with_transparent_corner_becomes_clean_jpeg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "foto.png"
            image = Image.new("RGBA", (40, 30), (20, 120, 60, 255))
            # Canto transparente do tamanho de um bloco do JPEG (16 x 16),
            # para a compressão não misturar o canto com o verde.
            image.paste((0, 0, 0, 0), (0, 0, 16, 16))
            image.save(png, pnginfo=None, exif=b"Exif\x00\x00MM\x00*\x00\x00\x00\x08\x00\x00")

            jpg = converter_fotos.convert(png)

            self.assertEqual(jpg, Path(tmp) / "foto.jpg")
            self.assertTrue(png.is_file())  # o original fica
            with Image.open(jpg) as out:
                self.assertEqual(out.format, "JPEG")
                self.assertEqual(out.size, (40, 30))
                self.assertEqual(out.mode, "RGB")
                corner = out.getpixel((0, 0))
                self.assertTrue(all(channel > 200 for channel in corner), corner)
                self.assertNotIn("exif", out.info)
                self.assertNotIn("icc_profile", out.info)
                self.assertEqual(len(out.getexif()), 0)

    def test_main_rejects_non_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "foto.jpg"
            Image.new("RGB", (4, 4)).save(other)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(converter_fotos.main([str(other)]), 1)


if __name__ == "__main__":
    unittest.main()
