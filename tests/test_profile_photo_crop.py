"""Recorte da foto de perfil (change recorte-foto-perfil): funções puras de
doafacil/recorte_foto.py, com imagens geradas na memória."""

import base64
import math
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image

from doafacil.recorte_foto import (
    CROPPER_LIBRARY,
    CROPPER_VERSION,
    MAX_PIXELS,
    OUTPUT_SIZE,
    PREVIEW_MAX_SIDE,
    CropAreaError,
    ImageCropper,
    PhotoImageError,
    crop_box,
    encode_square,
    image_cropper,
    make_preview,
    prepare_source,
)

RED = (220, 20, 20)
GREEN = (20, 160, 60)
BLUE = (20, 40, 220)
YELLOW = (240, 220, 20)
EXIF_ORIENTATION = 0x0112


def quadrants(width: int = 800, height: int = 600, mode: str = "RGB") -> Image.Image:
    """Quatro quadrantes: vermelho (sup. esq.), verde (sup. dir.), azul (inf.
    esq.) e amarelo (inf. dir.)."""
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


def with_orientation(image: Image.Image, orientation: int) -> bytes:
    exif = Image.Exif()
    exif[EXIF_ORIENTATION] = orientation
    # Make/Model e GPS para conferir a remoção dos metadados.
    exif[0x010F] = "CameraTeste"
    exif[0x0110] = "ModeloTeste"
    return encode(image, "JPEG", quality=95, exif=exif.tobytes())


def close_to(color: tuple, expected: tuple, tolerance: int = 40) -> bool:
    return all(abs(a - b) <= tolerance for a, b in zip(color[:3], expected[:3]))


def center_color(content: bytes) -> tuple:
    image = Image.open(BytesIO(content)).convert("RGBA")
    return image.getpixel((image.width // 2, image.height // 2))


def full_area(size: tuple[int, int]) -> dict:
    return {"x": 0, "y": 0, "width": size[0], "height": size[1]}


class PrepareSourceTests(unittest.TestCase):
    def test_formats_and_output_format(self) -> None:
        image = quadrants()
        cases = {
            "JPEG": ("JPEG", encode(image, "JPEG")),
            "PNG": ("PNG", encode(image, "PNG")),
            # WEBP nunca sai como WEBP (decisão 4a): sem transparência, JPEG.
            "WEBP": ("JPEG", encode(image, "WEBP")),
            "WEBP com transparência": (
                "PNG",
                encode(Image.new("RGBA", (800, 600), (20, 160, 60, 120)), "WEBP", lossless=True),
            ),
            "GIF": ("PNG", encode(image.convert("P"), "GIF")),
        }
        for label, (expected, content) in cases.items():
            with self.subTest(fmt=label):
                source = prepare_source(content)
                self.assertEqual(source.output_format, expected)
                self.assertEqual(source.image.size, (800, 600))

    def test_real_format_wins_over_extension(self) -> None:
        # O formato vem do conteúdo, nunca do nome do arquivo.
        self.assertEqual(prepare_source(encode(quadrants(), "JPEG")).output_format, "JPEG")

    def test_unreadable_or_unsupported_content(self) -> None:
        cases = {
            "texto": b"isto nao e imagem",
            "vazio": b"",
            "pdf": b"%PDF-1.4\n1 0 obj << >> endobj\n%%EOF\n",
            "png truncado": encode(quadrants(), "PNG")[:200],
            "bmp": encode(quadrants(), "BMP"),
        }
        for label, content in cases.items():
            with self.subTest(case=label):
                with self.assertRaises(PhotoImageError):
                    prepare_source(content)

    def test_pixel_limit_against_decompression_bombs(self) -> None:
        side = int(math.isqrt(MAX_PIXELS)) + 10
        content = encode(Image.new("1", (side, side)), "PNG")
        with self.assertRaises(PhotoImageError):
            prepare_source(content)

    def test_exif_orientation_is_applied(self) -> None:
        # Uma imagem 800x600 gravada com a orientação EXIF: o resultado é a
        # imagem como foi fotografada.
        base = quadrants(800, 600)
        expectations = {
            # 3 = girada 180°: o canto sup. esq. vira amarelo.
            3: ((800, 600), YELLOW),
            # 6 = girar 90° no sentido horário: o sup. esq. vira azul.
            6: ((600, 800), BLUE),
            # 8 = girar 90° no sentido anti-horário: o sup. esq. vira verde.
            8: ((600, 800), GREEN),
        }
        for orientation, (size, top_left) in expectations.items():
            with self.subTest(orientation=orientation):
                source = prepare_source(with_orientation(base, orientation))
                self.assertEqual(source.image.size, size)
                self.assertTrue(close_to(source.image.getpixel((20, 20)), top_left))

    def test_source_has_no_metadata(self) -> None:
        source = prepare_source(with_orientation(quadrants(), 6))
        self.assertNotIn("exif", source.image.info)
        self.assertNotIn("icc_profile", source.image.info)

    def test_transparency_kept_only_where_supported(self) -> None:
        transparent = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        self.assertEqual(prepare_source(encode(transparent, "PNG")).image.mode, "RGBA")
        self.assertEqual(prepare_source(encode(transparent, "WEBP")).image.mode, "RGBA")
        # Um WEBP com canal alfa, mas todo opaco, vira JPEG (RGB).
        opaque = Image.new("RGBA", (100, 100), (20, 160, 60, 255))
        source = prepare_source(encode(opaque, "WEBP", lossless=True))
        self.assertEqual((source.output_format, source.image.mode), ("JPEG", "RGB"))
        self.assertEqual(prepare_source(encode(quadrants(), "JPEG")).image.mode, "RGB")


class PreviewTests(unittest.TestCase):
    def test_preview_limited_to_max_side(self) -> None:
        source = prepare_source(encode(quadrants(3000, 1500), "PNG"))
        url, width, height = make_preview(source.image)
        self.assertEqual((width, height), (PREVIEW_MAX_SIDE, PREVIEW_MAX_SIDE // 2))
        self.assertTrue(url.startswith("data:image/jpeg;base64,"))
        decoded = Image.open(BytesIO(base64.b64decode(url.split(",", 1)[1])))
        self.assertEqual(decoded.size, (width, height))

    def test_small_image_is_not_enlarged_and_alpha_uses_png(self) -> None:
        source = prepare_source(encode(Image.new("RGBA", (300, 200), (0, 0, 0, 0)), "PNG"))
        url, width, height = make_preview(source.image)
        self.assertEqual((width, height), (300, 200))
        self.assertTrue(url.startswith("data:image/png;base64,"))


class CropBoxTests(unittest.TestCase):
    def test_area_in_preview_pixels_is_scaled_to_original(self) -> None:
        # Original 2000x1000, prévia 1000x500: escala 2.
        box = crop_box((2000, 1000), {"x": 100, "y": 50, "width": 300, "height": 300}, (1000, 500))
        self.assertEqual(box, (200, 100, 800, 700))

    def test_each_quadrant_comes_out_in_its_color(self) -> None:
        source = prepare_source(encode(quadrants(800, 600), "PNG"))
        preview_size = (800, 600)
        cases = {
            RED: {"x": 50, "y": 50, "width": 200, "height": 200},
            GREEN: {"x": 550, "y": 50, "width": 200, "height": 200},
            BLUE: {"x": 50, "y": 350, "width": 200, "height": 200},
            YELLOW: {"x": 550, "y": 350, "width": 200, "height": 200},
        }
        for color, area in cases.items():
            with self.subTest(color=color):
                content, _, _ = encode_square(source, crop_box(source.image.size, area, preview_size))
                result = Image.open(BytesIO(content)).convert("RGB")
                self.assertEqual(result.size, (OUTPUT_SIZE, OUTPUT_SIZE))
                for point in ((5, 5), (256, 256), (506, 506)):
                    self.assertTrue(close_to(result.getpixel(point), color), (color, point))

    def test_area_outside_image_is_moved_inside(self) -> None:
        size = (800, 600)
        self.assertEqual(crop_box(size, {"x": -50, "y": -30, "width": 200, "height": 200}, size), (0, 0, 200, 200))
        self.assertEqual(crop_box(size, {"x": 700, "y": 500, "width": 200, "height": 200}, size), (600, 400, 800, 600))

    def test_area_larger_than_image_shrinks_to_smaller_side(self) -> None:
        box = crop_box((800, 600), {"x": -100, "y": -100, "width": 1000, "height": 1000}, (800, 600))
        self.assertEqual(box[2] - box[0], 600)
        self.assertEqual(box[3] - box[1], 600)
        self.assertTrue(0 <= box[0] and box[2] <= 800 and 0 <= box[1] and box[3] <= 600)

    def test_non_square_area_becomes_centered_square(self) -> None:
        box = crop_box((800, 600), {"x": 100, "y": 100, "width": 400, "height": 200}, (800, 600))
        self.assertEqual(box, (200, 100, 400, 300))

    def test_invalid_areas_raise(self) -> None:
        cases = {
            "largura zero": {"x": 0, "y": 0, "width": 0, "height": 100},
            "altura negativa": {"x": 0, "y": 0, "width": 100, "height": -5},
            "NaN": {"x": math.nan, "y": 0, "width": 100, "height": 100},
            "infinito": {"x": 0, "y": 0, "width": math.inf, "height": 100},
            "texto": {"x": "0", "y": 0, "width": 100, "height": 100},
            "booleano": {"x": True, "y": 0, "width": 100, "height": 100},
            "faltando": {"x": 0, "y": 0, "width": 100},
            "não objeto": [0, 0, 100, 100],
        }
        for label, area in cases.items():
            with self.subTest(case=label):
                with self.assertRaises(CropAreaError):
                    crop_box((800, 600), area, (800, 600))
        with self.assertRaises(CropAreaError):
            crop_box((800, 600), full_area((800, 600)), (0, 0))


class EncodeSquareTests(unittest.TestCase):
    def _square(self, content: bytes) -> tuple[bytes, str, str]:
        source = prepare_source(content)
        return encode_square(source, crop_box(source.image.size, full_area(source.image.size), source.image.size))

    def test_output_format_name_and_type(self) -> None:
        image = quadrants()
        cases = {
            "JPEG": (encode(image, "JPEG"), "JPEG", "foto.jpg", "image/jpeg"),
            "PNG": (encode(image, "PNG"), "PNG", "foto.png", "image/png"),
            "WEBP sem transparência": (encode(image, "WEBP"), "JPEG", "foto.jpg", "image/jpeg"),
            "WEBP com transparência": (
                encode(Image.new("RGBA", (300, 300), (0, 0, 0, 0)), "WEBP"),
                "PNG",
                "foto.png",
                "image/png",
            ),
            "GIF": (encode(image.convert("P"), "GIF"), "PNG", "foto.png", "image/png"),
        }
        for label, (content, fmt, name, mime) in cases.items():
            with self.subTest(fmt=label):
                square, filename, mime_type = self._square(content)
                result = Image.open(BytesIO(square))
                self.assertEqual(result.format, fmt)
                self.assertEqual(result.size, (OUTPUT_SIZE, OUTPUT_SIZE))
                self.assertEqual((filename, mime_type), (name, mime))

    def test_small_area_is_enlarged_to_512(self) -> None:
        square, _, _ = self._square(encode(quadrants(120, 90), "PNG"))
        self.assertEqual(Image.open(BytesIO(square)).size, (OUTPUT_SIZE, OUTPUT_SIZE))

    def test_png_and_transparent_webp_keep_transparency_as_png(self) -> None:
        transparent = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        for fmt in ("PNG", "WEBP"):
            with self.subTest(fmt=fmt):
                square, filename, _ = self._square(encode(transparent, fmt))
                result = Image.open(BytesIO(square))
                self.assertEqual((result.format, filename), ("PNG", "foto.png"))
                self.assertEqual(result.convert("RGBA").getpixel((10, 10))[3], 0)

    def test_no_output_is_ever_webp(self) -> None:
        for image in (quadrants(), Image.new("RGBA", (200, 200), (0, 0, 0, 0))):
            with self.subTest(mode=image.mode):
                square, filename, mime = self._square(encode(image, "WEBP"))
                self.assertNotEqual(Image.open(BytesIO(square)).format, "WEBP")
                self.assertNotIn("webp", filename + mime)

    def test_metadata_is_removed(self) -> None:
        square, _, _ = self._square(with_orientation(quadrants(), 6))
        result = Image.open(BytesIO(square))
        self.assertEqual(dict(result.getexif()), {})
        self.assertNotIn(b"CameraTeste", square)
        self.assertNotIn(b"ModeloTeste", square)
        self.assertNotIn("icc_profile", result.info)

    def test_exif_rotation_survives_the_crop(self) -> None:
        # Orientação 6: o quadrante superior esquerdo da foto em pé é o azul.
        source = prepare_source(with_orientation(quadrants(800, 600), 6))
        box = crop_box(source.image.size, {"x": 0, "y": 0, "width": 250, "height": 250}, source.image.size)
        square, _, _ = encode_square(source, box)
        self.assertTrue(close_to(center_color(square), BLUE))


class ImageCropperComponentTests(unittest.TestCase):
    def test_component_wraps_local_jsx_and_pinned_package(self) -> None:
        self.assertEqual(CROPPER_VERSION, "react-easy-crop@6.2.4")
        self.assertEqual(ImageCropper.library, CROPPER_LIBRARY)
        self.assertIn(CROPPER_VERSION, ImageCropper.lib_dependencies)
        self.assertTrue(Path("assets/recorte/image_cropper.jsx").is_file())

    def test_props_and_crop_complete_event(self) -> None:
        from doafacil.editar_perfil import EditProfileState

        rendered = str(image_cropper(EditProfileState.crop_preview, on_crop_complete=EditProfileState.set_crop_area))
        self.assertIn("crop_preview_rx_state_", rendered)
        for prop in ('minZoom:1.0', 'maxZoom:3.0', 'zoomStep:0.1', 'zoomLabel:"Zoom"', 'zoomOutLabel:"Diminuir zoom"', 'zoomInLabel:"Aumentar zoom"'):
            with self.subTest(prop=prop):
                self.assertIn(prop, rendered)
        self.assertIn("areaLabel", rendered)
        self.assertIn("onCropComplete", rendered)
        self.assertIn("set_crop_area", rendered)

    def test_jsx_uses_round_square_cropper_and_keyboard(self) -> None:
        jsx = Path("assets/recorte/image_cropper.jsx").read_text(encoding="utf-8")
        for snippet in (
            'cropShape="round"',
            "aspect={1}",
            "restrictPosition={true}",
            "zoomWithScroll={true}",
            '"aria-label": areaLabel',
            'aria-label={zoomLabel}',
            'aria-label={zoomOutLabel}',
            'aria-label={zoomInLabel}',
            'event.key === "+"',
            'event.key === "-"',
            'width: "44px"',
            'height: "44px"',
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, jsx)
        # Só a área final vai ao Reflex: o crop e o zoom ficam no navegador.
        self.assertIn("useState", jsx)
        self.assertIn("onCropComplete({", jsx)

    def test_zoom_control_and_focus_follow_site_style(self) -> None:
        """Trilha cinza clara preenchida em verde, marcador redondo de 20 px
        branco com borda verde e anel de foco verde (não o azul padrão)."""
        jsx = Path("assets/recorte/image_cropper.jsx").read_text(encoding="utf-8")
        for snippet in (
            'const GREEN = "#007A42"',
            'const TRACK = "#C8C8C8"',
            "appearance: none;",
            "::-webkit-slider-runnable-track",
            "var(--fill, 0%)",
            "::-moz-range-progress",
            "::-webkit-slider-thumb",
            "::-moz-range-thumb",
            "width: 20px;",
            "height: 20px;",
            "border-radius: 50%;",
            "background: #FFFFFF;",
            "border: 2px solid ${GREEN};",
            ":focus-visible::-webkit-slider-thumb",
            ".image-cropper-button:focus-visible",
            ".reactEasyCrop_CropArea:focus-visible",
            "outline: 2px solid ${GREEN};",
            '"--fill": `${fill}%`',
            'className="image-cropper-zoom"',
            'className="image-cropper-button"',
            "<style>{STYLES}</style>",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, jsx)
        # O controle nativo sem estilo (accentColor) saiu.
        self.assertNotIn("accentColor", jsx)
        # O verde do marcador e do anel tem contraste de componente (>= 3:1)
        # sobre o branco do modal.
        def lum(color: str) -> float:
            channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
            linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        self.assertGreaterEqual((lum("#FFFFFF") + 0.05) / (lum("#007A42") + 0.05), 3)


if __name__ == "__main__":
    unittest.main()
