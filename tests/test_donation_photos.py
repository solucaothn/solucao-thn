"""Fotos do cadastro de doação (change fotos-formulario-doacao): funções puras
de doafacil/fotos_doacao.py, o estado das fotos e o passo 3."""

import asyncio
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from doafacil.fotos_doacao import (
    EMPTY_MESSAGE,
    FORMAT_MESSAGE,
    MAX_PHOTO_BYTES,
    READ_ERROR_MESSAGE,
    SIZE_MESSAGE,
    PhotoImageError,
    check_file,
    make_cover,
    move,
    process_photo,
    rejection_message,
    remove,
)

EXIF_ORIENTATION = 0x0112


def solid(color: tuple, size: tuple[int, int] = (400, 300), mode: str = "RGB") -> Image.Image:
    return Image.new(mode, size, color)


def encode(image: Image.Image, fmt: str, **params) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format=fmt, **params)
    return buffer.getvalue()


def jpeg_with_metadata(image: Image.Image, orientation: int = 1) -> bytes:
    exif = Image.Exif()
    exif[EXIF_ORIENTATION] = orientation
    exif[0x010F] = "MarcaDoacaoTeste"
    exif[0x0110] = "ModeloDoacaoTeste"
    gps = exif.get_ifd(0x8825)
    gps[1] = "S"
    gps[2] = (23.0, 32.0, 45.0)
    return encode(image, "JPEG", quality=95, exif=exif.tobytes())


def photos(*ids: str) -> list[dict]:
    return [{"id": photo_id, "thumb": f"t-{photo_id}", "name": f"{photo_id}.png"} for photo_id in ids]


def ids(order: list[dict]) -> list[str]:
    return [photo["id"] for photo in order]


class CheckFileTests(unittest.TestCase):
    def test_accepted_types_and_size_limit(self) -> None:
        self.assertEqual(check_file("a.jpg", "image/jpeg", 10), "")
        self.assertEqual(check_file("a.JPEG", "", 10), "")
        self.assertEqual(check_file("a.png", "image/png", MAX_PHOTO_BYTES), "")
        self.assertEqual(check_file("a.png", "image/png", MAX_PHOTO_BYTES + 1), SIZE_MESSAGE)
        self.assertEqual(MAX_PHOTO_BYTES, 5 * 1024 * 1024)
        self.assertEqual(SIZE_MESSAGE, "A foto pode ter no máximo 5 MB.")

    def test_refused_types_and_empty(self) -> None:
        for name, mime in (("doc.pdf", "application/pdf"), ("a.png", "image/jpeg"), ("sem-extensao", ""), ("a.heic", "image/heic")):
            with self.subTest(name=name):
                self.assertEqual(check_file(name, mime, 10), FORMAT_MESSAGE)
        self.assertEqual(check_file("a.png", "image/png", 0), EMPTY_MESSAGE)
        self.assertEqual(FORMAT_MESSAGE, "Selecione até cinco imagens JPEG, PNG, GIF ou WEBP.")


class ProcessPhotoTests(unittest.TestCase):
    def test_orientation_applied_and_metadata_removed(self) -> None:
        # 400x300 com orientação 6 → em pé (300x400).
        processed = process_photo(jpeg_with_metadata(solid((20, 160, 60)), 6))
        result = Image.open(BytesIO(processed.contents))
        self.assertEqual(result.size, (300, 400))
        self.assertEqual(dict(result.getexif()), {})
        for marker in (b"MarcaDoacaoTeste", b"ModeloDoacaoTeste", b"GPS"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, processed.contents)
        self.assertNotIn("icc_profile", result.info)
        self.assertEqual((processed.mime, processed.extension), ("image/jpeg", "jpg"))

    def test_output_formats(self) -> None:
        transparent = solid((0, 0, 0, 0), mode="RGBA")
        # PNG só quando há transparência real; nos outros casos, JPEG.
        cases = {
            "JPEG": (encode(solid((1, 2, 3)), "JPEG"), "JPEG", "jpg"),
            "PNG sem transparência": (encode(solid((1, 2, 3)), "PNG"), "JPEG", "jpg"),
            "PNG com transparência": (encode(transparent, "PNG"), "PNG", "png"),
            "GIF sem transparência": (encode(solid((1, 2, 3)).convert("P"), "GIF"), "JPEG", "jpg"),
            "WEBP sem transparência": (encode(solid((1, 2, 3)), "WEBP"), "JPEG", "jpg"),
            "WEBP com transparência": (encode(transparent, "WEBP"), "PNG", "png"),
        }
        for label, (content, fmt, extension) in cases.items():
            with self.subTest(case=label):
                processed = process_photo(content)
                self.assertEqual(Image.open(BytesIO(processed.contents)).format, fmt)
                self.assertEqual(processed.extension, extension)
        transparent_png = process_photo(encode(transparent, "PNG"))
        self.assertEqual(Image.open(BytesIO(transparent_png.contents)).convert("RGBA").getpixel((5, 5))[3], 0)

    def test_max_1600_without_enlarging(self) -> None:
        big = process_photo(encode(solid((9, 9, 9), (3000, 1500)), "PNG"))
        self.assertEqual(Image.open(BytesIO(big.contents)).size, (1600, 800))
        small = process_photo(encode(solid((9, 9, 9), (640, 480)), "PNG"))
        self.assertEqual(Image.open(BytesIO(small.contents)).size, (640, 480))

    def test_thumbnail_up_to_240(self) -> None:
        processed = process_photo(encode(solid((9, 9, 9), (1200, 600)), "PNG"))
        self.assertTrue(processed.thumb.startswith("data:image/"))
        import base64

        thumb = Image.open(BytesIO(base64.b64decode(processed.thumb.split(",", 1)[1])))
        self.assertEqual(thumb.size, (240, 120))

    def test_unreadable_image(self) -> None:
        for content in (b"nao e imagem", encode(solid((1, 2, 3)), "PNG")[:100]):
            with self.subTest(size=len(content)):
                with self.assertRaises(PhotoImageError):
                    process_photo(content)


class RejectionMessageTests(unittest.TestCase):
    def test_messages(self) -> None:
        self.assertEqual(rejection_message([{"errors": [{"code": "file-too-large"}]}]), SIZE_MESSAGE)
        self.assertEqual(rejection_message([{"errors": [{"code": "file-invalid-type"}]}]), FORMAT_MESSAGE)
        self.assertEqual(rejection_message([{"errors": [{"code": "too-many-files"}]}]), FORMAT_MESSAGE)
        self.assertEqual(rejection_message(None), FORMAT_MESSAGE)


class OrderTests(unittest.TestCase):
    def test_remove_keeps_relative_order(self) -> None:
        self.assertEqual(ids(remove(photos("a", "b", "c"), "b")), ["a", "c"])
        self.assertEqual(ids(remove(photos("a", "b", "c"), "a")), ["b", "c"])
        self.assertEqual(ids(remove(photos("a"), "x")), ["a"])

    def test_move_swaps_with_neighbor_and_respects_ends(self) -> None:
        order = photos("a", "b", "c")
        self.assertEqual(ids(move(order, "b", -1)), ["b", "a", "c"])
        self.assertEqual(ids(move(order, "b", 1)), ["a", "c", "b"])
        self.assertEqual(ids(move(order, "a", -1)), ["a", "b", "c"])
        self.assertEqual(ids(move(order, "c", 1)), ["a", "b", "c"])
        self.assertEqual(ids(move(order, "b", 2)), ["a", "b", "c"])
        self.assertEqual(ids(order), ["a", "b", "c"])  # não altera a lista recebida

    def test_make_cover_moves_to_front_keeping_others(self) -> None:
        order = photos("a", "b", "c", "d")
        self.assertEqual(ids(make_cover(order, "c")), ["c", "a", "b", "d"])
        self.assertEqual(ids(make_cover(order, "a")), ["a", "b", "c", "d"])
        self.assertEqual(ids(make_cover(order, "x")), ["a", "b", "c", "d"])


class _FakeUpload:
    def __init__(self, name: str, content_type: str, contents: bytes | None = None, *, fail: bool = False) -> None:
        self.name = name
        self.content_type = content_type
        self._contents = contents
        self._fail = fail

    async def read(self) -> bytes:
        if self._fail:
            raise OSError("leitura falhou")
        return self._contents or b""


def _png(color: tuple = (20, 160, 60)) -> bytes:
    return encode(solid(color), "PNG")


def _state(**fields) -> SimpleNamespace:
    base = dict(
        photos=[],
        photos_busy=False,
        photo_notice="",
        _photo_files={},
        is_publishing=False,
        published=False,
        donation_error_message="",
    )
    base.update(fields)
    return SimpleNamespace(**base)


def _add(state, files) -> list:
    from doafacil.cadastro_doacao import DonationCreateState

    async def run() -> list:
        return [event async for event in DonationCreateState.add_photos.fn(state, files)]

    return asyncio.run(run())


class PhotoStateTests(unittest.TestCase):
    def test_add_sums_with_previous_choices_and_keeps_only_prepared_versions(self) -> None:
        state = _state()
        events = _add(state, [_FakeUpload("a.png", "image/png", _png()), _FakeUpload("b.jpg", "image/jpeg", encode(solid((1, 2, 3)), "JPEG"))])
        self.assertEqual(len(state.photos), 2)
        # Sem limpar o upload (change navegacao-celular): o on_drop não guarda
        # seleção, e o clear_selected_files quebrava no navegador.
        self.assertNotIn("clear", [str(event) for event in events])
        _add(state, [_FakeUpload("c.webp", "image/webp", encode(solid((5, 5, 5)), "WEBP"))])
        self.assertEqual(len(state.photos), 3)
        self.assertEqual(set(state._photo_files), {photo["id"] for photo in state.photos})
        self.assertEqual(state.photo_notice, "Foto adicionada.")
        self.assertFalse(state.photos_busy)
        # Só a versão preparada fica guardada: sem os bytes originais, sem o
        # nome original, e o WEBP sem transparência virou JPEG.
        kinds = [state._photo_files[photo["id"]][1:] for photo in state.photos]
        # Sem transparência, tudo vira JPEG (PNG só com transparência real).
        self.assertEqual(kinds, [("image/jpeg", "jpg"), ("image/jpeg", "jpg"), ("image/jpeg", "jpg")])
        self.assertNotIn(_png(), [value[0] for value in state._photo_files.values()])
        self.assertTrue(all(set(photo) == {"id", "thumb"} for photo in state.photos))
        self.assertTrue(all(photo["thumb"].startswith("data:image/") for photo in state.photos))

    def test_limit_of_five_keeps_already_accepted(self) -> None:
        state = _state()
        _add(state, [_FakeUpload(f"{i}.png", "image/png", _png((i, i, i))) for i in range(3)])
        first_ids = [photo["id"] for photo in state.photos]
        _add(state, [_FakeUpload(f"n{i}.png", "image/png", _png((9, 9, i))) for i in range(4)])
        self.assertEqual(len(state.photos), 5)
        self.assertEqual([photo["id"] for photo in state.photos][:3], first_ids)
        self.assertEqual(state.donation_error_message, FORMAT_MESSAGE)
        self.assertEqual(len(state._photo_files), 5)

    def test_invalid_files_show_current_messages_and_keep_accepted(self) -> None:
        cases = (
            ("doc.pdf", "application/pdf", b"%PDF-1.4", FORMAT_MESSAGE),
            ("grande.png", "image/png", b"0" * (MAX_PHOTO_BYTES + 1), SIZE_MESSAGE),
            ("vazia.png", "image/png", b"", EMPTY_MESSAGE),
            ("falsa.png", "image/png", b"isto nao e imagem", FORMAT_MESSAGE),
        )
        for name, mime, contents, message in cases:
            with self.subTest(name=name):
                state = _state()
                _add(state, [_FakeUpload("ok.png", "image/png", _png())])
                _add(state, [_FakeUpload(name, mime, contents)])
                self.assertEqual(len(state.photos), 1)
                self.assertEqual(state.donation_error_message, message)
        state = _state()
        _add(state, [_FakeUpload("x.png", "image/png", fail=True)])
        self.assertEqual((state.photos, state.donation_error_message), ([], READ_ERROR_MESSAGE))

    def test_add_ignored_while_busy_or_published(self) -> None:
        for field in ("photos_busy", "is_publishing", "published"):
            with self.subTest(field=field):
                state = _state(**{field: True})
                _add(state, [_FakeUpload("a.png", "image/png", _png())])
                self.assertEqual(state.photos, [])

    def test_rejected_by_component(self) -> None:
        from doafacil.cadastro_doacao import DonationCreateState

        state = _state(photos=photos("a"), photo_notice="Foto adicionada.")
        DonationCreateState.photos_rejected.fn(state, [{"errors": [{"code": "file-too-large"}]}])
        self.assertEqual(state.donation_error_message, SIZE_MESSAGE)
        self.assertEqual(state.photo_notice, "")
        self.assertEqual(ids(state.photos), ["a"])

    def test_remove_deletes_stored_file_and_moves_focus(self) -> None:
        from doafacil.cadastro_doacao import PHOTO_UPLOAD_ID, DonationCreateState

        files = {key: (b"x", "image/png", "png") for key in "abc"}
        state = _state(photos=photos("a", "b", "c"), _photo_files=dict(files))
        with patch("doafacil.cadastro_doacao.rx.call_script", side_effect=lambda script: script) as script:
            event = DonationCreateState.remove_photo.fn(state, "b")
        self.assertEqual(ids(state.photos), ["a", "c"])
        self.assertEqual(set(state._photo_files), {"a", "c"})
        self.assertIn("photo-c-remove", event)
        self.assertEqual(state.photo_notice, "Foto removida.")
        with patch("doafacil.cadastro_doacao.rx.call_script", side_effect=lambda script: script):
            DonationCreateState.remove_photo.fn(state, "a")
            event = DonationCreateState.remove_photo.fn(state, "c")
        self.assertEqual((state.photos, state._photo_files), ([], {}))
        self.assertIn(PHOTO_UPLOAD_ID, event)
        script.assert_called()

    def test_move_and_make_cover_keep_files_and_focus(self) -> None:
        from doafacil.cadastro_doacao import DonationCreateState

        files = {key: (b"x", "image/png", "png") for key in "abc"}
        state = _state(photos=photos("a", "b", "c"), _photo_files=dict(files))
        with patch("doafacil.cadastro_doacao.rx.call_script", side_effect=lambda script: script):
            event = DonationCreateState.move_photo.fn(state, "b", -1)
            self.assertEqual(ids(state.photos), ["b", "a", "c"])
            # Chegou à primeira posição: o foco vai a “Mover para a direita”.
            self.assertIn("photo-b-right", event)
            self.assertEqual(state.photo_notice, "Foto movida para a posição 1.")
            event = DonationCreateState.move_photo.fn(state, "a", 1)
            self.assertEqual(ids(state.photos), ["b", "c", "a"])
            self.assertIn("photo-a-left", event)
            self.assertIsNone(DonationCreateState.move_photo.fn(state, "a", 1))
            event = DonationCreateState.make_cover.fn(state, "c")
            self.assertEqual(ids(state.photos), ["c", "b", "a"])
            self.assertIn("photo-c-right", event)
            self.assertEqual(state.photo_notice, "Foto definida como capa.")
            self.assertIsNone(DonationCreateState.make_cover.fn(state, "c"))
        self.assertEqual(state._photo_files, files)

    def test_photo_actions_ignored_while_publishing(self) -> None:
        from doafacil.cadastro_doacao import DonationCreateState

        state = _state(photos=photos("a", "b"), _photo_files={"a": (b"", "", ""), "b": (b"", "", "")}, is_publishing=True)
        DonationCreateState.remove_photo.fn(state, "a")
        DonationCreateState.move_photo.fn(state, "b", -1)
        DonationCreateState.make_cover.fn(state, "b")
        self.assertEqual(ids(state.photos), ["a", "b"])


def _luminance(color: str) -> float:
    channels = [int(color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground: str, background: str) -> float:
    a, b = _luminance(foreground), _luminance(background)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


class PhotoStepTests(unittest.TestCase):
    def _rendered(self) -> str:
        from doafacil.cadastro_doacao import _step_three

        return str(_step_three())

    def test_text_upload_and_count(self) -> None:
        from doafacil.cadastro_doacao import PHOTO_STEP_TEXT

        rendered = self._rendered()
        self.assertEqual(PHOTO_STEP_TEXT, "Adicione de 1 a 5 fotos. A primeira foto é a capa da doação.")
        self.assertNotIn("Voc\\u00ea pode publicar sem fotos", rendered)
        self.assertIn("Limite de 5 fotos atingido", rendered)
        self.assertIn("photos_full_rx_state_", rendered)
        self.assertIn(" de 5 fotos", rendered)
        self.assertIn('"aria-live":"polite"', rendered)
        self.assertIn("Preparando fotos...", rendered)
        # Sem a lista de nomes e sem “Remover todas”.
        self.assertNotIn("Remover todas", rendered)
        self.assertNotIn("Pronta para enviar", rendered)

    def test_upload_limits_on_screen(self) -> None:
        from doafacil.cadastro_doacao import _step_three

        upload = next(node for node in _all_nodes(_step_three()) if type(node).__name__ == "StyledUpload")
        hooks = "\n".join(upload.children[0].special_props[0]._get_all_var_data().hooks)
        self.assertIn(f'["maxSize"] : {MAX_PHOTO_BYTES}', hooks)
        self.assertIn('["maxFiles"] : 5', hooks)
        # Cada escolha vai na hora ao servidor (soma) e as recusas da tela
        # mostram a mensagem atual.
        self.assertIn("donation_create_state.add_photos", hooks)
        self.assertIn("donation_create_state.photos_rejected", hooks)
        for mime in ("image/jpeg", "image/png", "image/gif", "image/webp"):
            with self.subTest(mime=mime):
                self.assertIn(f'["{mime}"]', hooks)

    def test_row_has_thumbnail_cover_badge_and_labelled_buttons(self) -> None:
        rendered = self._rendered()
        self.assertIn('("Foto "+', rendered)
        self.assertIn('" de "', rendered)
        self.assertIn('["objectFit"] : "cover"', rendered)
        self.assertIn('"72px"', rendered)
        self.assertIn("donation-photo-cover", rendered)
        self.assertIn('"Capa"', rendered)
        for label in ('("Mover foto "+', '+" para a esquerda")', '+" para a direita")', '("Tornar foto "+', '+" a capa")', '("Remover foto "+'):
            with self.subTest(label=label):
                self.assertIn(label, rendered)
        for suffix in ("-left", "-right", "-cover", "-remove"):
            with self.subTest(suffix=suffix):
                self.assertIn(f'"{suffix}"', rendered)
        for icon in ("LucideChevronLeft", "LucideChevronRight", "LucideStar", "LucideTrash2"):
            with self.subTest(icon=icon):
                self.assertIn(icon, rendered)
        self.assertEqual(rendered.count('["width"] : "44px"'), 4)
        self.assertEqual(rendered.count('["height"] : "44px"'), 4)
        self.assertIn("move_photo", rendered)
        self.assertIn("make_cover", rendered)
        self.assertIn("remove_photo", rendered)

    def test_buttons_disabled_at_ends_and_on_cover(self) -> None:
        rendered = self._rendered()
        # Primeira foto (índice 0): esquerda e capa desativadas; última: direita.
        self.assertIn("=== 0", rendered)
        self.assertIn("photo_count_rx_state_ - 1", rendered)

    def test_no_horizontal_overflow_and_contrast(self) -> None:
        rendered = self._rendered()
        self.assertIn('wrap:"wrap"', rendered)
        self.assertNotIn("nowrap", rendered)
        self.assertGreaterEqual(_contrast("#166B3B", "#E8F5EC"), 4.5)  # selo “Capa”
        self.assertGreaterEqual(_contrast("#B42318", "#FFFFFF"), 4.5)  # remover
        self.assertGreaterEqual(_contrast("#333333", "#FFFFFF"), 4.5)  # ícones
        self.assertGreaterEqual(_contrast("#168447", "#F9FCF9"), 3)  # ícone da área
        self.assertGreaterEqual(_contrast("#555555", "#F9FCF9"), 4.5)  # ajuda


def _all_nodes(component) -> list:
    nodes: list = []

    def collect(value) -> None:
        if hasattr(value, "children"):
            nodes.append(value)
            collect(value.children)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(component)
    return nodes


class PublishedNoticeTests(unittest.TestCase):
    def setUp(self) -> None:
        # Cache dos dados públicos (change navegacao-celular): validade zero,
        # para cada chamada destes testes ir ao cliente falso.
        from unittest.mock import patch as _patch

        from doafacil import cache_publico

        cache_publico.clear()
        no_cache = _patch("doafacil.cache_publico.PUBLIC_CACHE_SECONDS", 0.0)
        no_cache.start()
        self.addCleanup(no_cache.stop)

    def _load(self, route_id: str, notice_id: int) -> SimpleNamespace:
        from doafacil.detalhe_doacao import DonationDetailState

        state = SimpleNamespace(
            router=SimpleNamespace(url=SimpleNamespace(path=f"/doacao/{route_id}", query_parameters={})),
            published_notice_id=notice_id,
            show_published_notice=False,
        )
        with patch("doafacil.detalhe_doacao._fetch_donation_detail", side_effect=ValueError):
            asyncio.run(DonationDetailState.load_donation.fn(state))
        return state

    def test_notice_only_on_arrival_for_that_donation(self) -> None:
        from doafacil.detalhe_doacao import DonationDetailState

        state = SimpleNamespace(published_notice_id=0)
        DonationDetailState.set_published_notice.fn(state, 12)
        self.assertEqual(state.published_notice_id, 12)

        arrived = self._load("12", 12)
        self.assertTrue(arrived.show_published_notice)
        self.assertEqual(arrived.published_notice_id, 0)  # consumido
        # Recarregar a página (o id já foi consumido): sem aviso.
        arrived.router = SimpleNamespace(url=SimpleNamespace(path="/doacao/12", query_parameters={}))
        reloaded = self._load("12", arrived.published_notice_id)
        self.assertFalse(reloaded.show_published_notice)
        # Outra doação: sem aviso.
        other = self._load("13", 12)
        self.assertFalse(other.show_published_notice)
        invalid = self._load("abc", 12)
        self.assertFalse(invalid.show_published_notice)

    def test_notice_component(self) -> None:
        from doafacil.detalhe_doacao import _donation_content, _published_notice

        rendered = str(_published_notice())
        self.assertIn("show_published_notice_rx_state_", rendered)
        self.assertIn("Doa\\u00e7\\u00e3o publicada!", rendered)
        self.assertIn("Minhas doa\\u00e7\\u00f5es", rendered)
        self.assertIn('to:"/minhas-doacoes"', rendered)
        self.assertIn('role:"status"', rendered)
        self.assertIn('["minHeight"] : "44px"', rendered)
        self.assertIn('wrap:"wrap"', rendered)
        self.assertIn("(jsx(Fragment,{},))", rendered)  # sem o aviso, nada
        self.assertNotIn("Fechar", rendered)
        self.assertGreaterEqual(_contrast("#166B3B", "#E8F5EC"), 4.5)
        self.assertGreaterEqual(_contrast("#007A42", "#E8F5EC"), 4.5)
        self.assertIn("detail-published-notice", str(_donation_content()))


if __name__ == "__main__":
    unittest.main()
