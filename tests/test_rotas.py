"""Parâmetros da página pelo router.url (change navegacao-celular; o
router.page está obsoleto no Reflex)."""

import unittest
from pathlib import Path
from types import SimpleNamespace

from doafacil.rotas import path_segment_after, query_parameter

ROOT = Path(__file__).resolve().parent.parent


def _router(path: str = "", query: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(url=SimpleNamespace(path=path, query_parameters=query or {}))


class RouteTests(unittest.TestCase):
    def test_segment_after(self) -> None:
        self.assertEqual(path_segment_after(_router("/doacao/17"), "doacao"), "17")
        self.assertEqual(path_segment_after(_router("/doacao/17/quem-doa"), "doacao"), "17")
        self.assertEqual(path_segment_after(_router("/minhas-doacoes/9/editar"), "minhas-doacoes"), "9")
        self.assertEqual(path_segment_after(_router("/doacao/"), "doacao"), "")
        self.assertEqual(path_segment_after(_router("/outra/1"), "doacao"), "")
        self.assertEqual(path_segment_after(_router("/doacao/a%20b"), "doacao"), "a b")
        self.assertEqual(path_segment_after(SimpleNamespace(), "doacao"), "")

    def test_query_parameter(self) -> None:
        self.assertEqual(query_parameter(_router("/chat", {"conversa": "7"}), "conversa"), "7")
        self.assertEqual(query_parameter(_router("/chat"), "conversa"), "")

    def test_no_router_page_left(self) -> None:
        for path in sorted((ROOT / "doafacil").glob("*.py")):
            if path.name == "rotas.py":
                continue  # a docstring explica a troca
            source = path.read_text(encoding="utf-8")
            code = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))
            with self.subTest(module=path.name):
                self.assertNotIn("router.page", code)


if __name__ == "__main__":
    unittest.main()
