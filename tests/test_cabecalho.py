"""Cabeçalho compartilhado (change explorar-categorias): o menu da conta não
calcula a inicial no navegador, o que quebrava a página com o nome ainda
indefinido (“Cannot read properties of undefined (reading 'toUpperCase')”)."""

import unittest
from types import SimpleNamespace

from doafacil.cabecalho import HeaderState, account_menu


class AccountInitialTests(unittest.TestCase):
    def _initial(self, name: object) -> str:
        return HeaderState.computed_vars["account_initial"].fget(SimpleNamespace(account_name=name))

    def test_initial_from_name(self) -> None:
        self.assertEqual(self._initial("ana"), "A")
        self.assertEqual(self._initial("  Érica "), "É")
        self.assertEqual(self._initial("Minha conta"), "M")

    def test_no_name_means_no_initial(self) -> None:
        for name in ("", "   ", None, 5):
            with self.subTest(name=name):
                self.assertEqual(self._initial(name), "")


class AccountMenuTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rendered = str(account_menu())

    def test_initial_comes_from_the_server(self) -> None:
        # Nada de indexar ou pôr em maiúsculas o nome no navegador.
        self.assertNotIn("toUpperCase", self.rendered)
        self.assertNotIn('account_name_rx_state_?.at?.(0)', self.rendered)
        self.assertIn("header_state.account_initial", self.rendered)

    def test_person_icon_without_name(self) -> None:
        self.assertIn("LucideUser", self.rendered)
        self.assertIn('"aria-label":("Menu da conta de "+', self.rendered)
        self.assertIn('["minHeight"] : "44px"', self.rendered)

    def test_home_explore_and_categories_use_the_safe_menu(self) -> None:
        from doafacil.doafacil import categories_page, explore_page, index

        for name, page in (("home", index), ("explorar", explore_page), ("categorias", categories_page)):
            with self.subTest(page=name):
                rendered = str(page())
                self.assertIn("header_state.account_initial", rendered)
                self.assertNotIn("toUpperCase", rendered)


if __name__ == "__main__":
    unittest.main()
