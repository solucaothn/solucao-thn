"""Change endpoints-antigos: o site não usa o GET nem o POST de
catalog/donations, que são removidos do Xano. O caminho sem sufixo só pode
aparecer em chamadas PATCH (editar) e DELETE (apagar)."""

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BARE_PATH = "/catalog/donations"
ALLOWED_METHODS = {"patch", "delete"}
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "request", "stream"}


def _modules() -> list[Path]:
    return sorted((ROOT / "doafacil").glob("*.py"))


def _bare_path_names(tree: ast.AST) -> set[str]:
    """Nomes de constantes cujo valor é exatamente o caminho sem sufixo."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and node.value.value == BARE_PATH:
            names |= {target.id for target in node.targets if isinstance(target, ast.Name)}
    return names


def _mentions_bare_path(node: ast.AST, names: set[str]) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in names:
            return True
        if isinstance(child, ast.Constant) and isinstance(child.value, str) and child.value.rstrip("/").endswith(BARE_PATH):
            return True
    return False


def _calls_to_bare_path() -> list[tuple[str, str]]:
    """(módulo, método) de cada chamada HTTP que usa o caminho sem sufixo."""
    found = []
    for path in _modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = _bare_path_names(tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            method = node.func.attr
            if method not in HTTP_METHODS:
                continue
            if any(_mentions_bare_path(arg, names) for arg in [*node.args, *(kw.value for kw in node.keywords)]):
                found.append((path.name, method))
    return found


class FrontendUsageTests(unittest.TestCase):
    def test_bare_path_only_with_patch_and_delete(self) -> None:
        calls = _calls_to_bare_path()
        # O front edita e apaga por esse caminho (Minhas doações).
        self.assertEqual(sorted(calls), [("minhas_doacoes.py", "delete"), ("minhas_doacoes.py", "patch")])
        for module, method in calls:
            with self.subTest(module=module):
                self.assertIn(method, ALLOWED_METHODS)

    def test_detector_catches_get_and_post(self) -> None:
        # Garante que o teste acima não passa por não enxergar nada.
        source = (
            'P = "/catalog/donations"\n'
            "client.get(_endpoint(P))\n"
            'client.post(f"{base}/catalog/donations")\n'
            'client.get(f"{base}/catalog/donations/search")\n'
        )
        tree = ast.parse(source)
        names = _bare_path_names(tree)
        methods = [
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and any(_mentions_bare_path(arg, names) for arg in node.args)
        ]
        self.assertEqual(sorted(methods), ["get", "post"])


class XanoFilesTests(unittest.TestCase):
    CATALOG = ROOT / "xano" / "api" / "catalog" / "catalog"

    def test_get_and_post_files_removed(self) -> None:
        for name in ("donations_GET.xs", "donations_POST.xs"):
            with self.subTest(name=name):
                self.assertFalse((self.CATALOG / name).exists())

    def test_patch_and_delete_files_kept(self) -> None:
        for name in ("donations_PATCH.xs", "donations_DELETE.xs"):
            with self.subTest(name=name):
                self.assertTrue((self.CATALOG / name).is_file())


if __name__ == "__main__":
    unittest.main()
