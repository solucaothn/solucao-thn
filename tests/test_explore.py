"""Página provisória Explorar doações (change landing-nova, spec
donation-explore): filtros da URL, nome da categoria e conteúdo da página."""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx

from doafacil.explorar import (
    ALL_CATEGORIES_LABEL,
    BRAZILIAN_STATES,
    NO_FILTERS_TEXT,
    UNDER_CONSTRUCTION_TEXT,
    ExploreState,
    build_explore_url,
    explore_page,
    parse_explore_filters,
)

CATEGORIES = [{"id": "4", "name": "Livros"}, {"id": "7", "name": "Roupas"}]


def _state(params: dict) -> SimpleNamespace:
    return SimpleNamespace(
        router=SimpleNamespace(page=SimpleNamespace(params=params)),
        search_text="antigo",
        category_label="antigo",
        state_label="antigo",
    )


def _load(params: dict, categories=CATEGORIES, error=None) -> tuple[SimpleNamespace, AsyncMock]:
    state = _state(params)
    with patch(
        "doafacil.explorar.fetch_categories",
        new_callable=AsyncMock,
        return_value=categories,
        side_effect=error,
    ) as fetch:
        asyncio.run(ExploreState.load_filters.fn(state))
    return state, fetch


class FilterTests(unittest.TestCase):
    def test_states_are_the_27_ufs(self) -> None:
        self.assertEqual(len(BRAZILIAN_STATES), 27)
        self.assertEqual(len(set(BRAZILIAN_STATES)), 27)

    def test_parse_keeps_valid_and_drops_invalid(self) -> None:
        self.assertEqual(
            parse_explore_filters({"q": "  mesa ", "categoria": "4", "uf": "sp"}),
            {"q": "mesa", "categoria": "4", "uf": "SP"},
        )
        for categoria in ("abc", "0", "-3", "4.5", "", None):
            with self.subTest(categoria=categoria):
                self.assertEqual(parse_explore_filters({"categoria": categoria})["categoria"], "")
        for uf in ("XX", "São Paulo", "", None):
            with self.subTest(uf=uf):
                self.assertEqual(parse_explore_filters({"uf": uf})["uf"], "")

    def test_build_and_parse_round_trip(self) -> None:
        url = build_explore_url("cadeira azul", "7", "rj")
        self.assertEqual(url, "/explorar?q=cadeira+azul&categoria=7&uf=RJ")
        self.assertEqual(build_explore_url("", "todas", "todas"), "/explorar")


class LoadFiltersTests(unittest.TestCase):
    def test_valid_filters_and_category_name(self) -> None:
        state, fetch = _load({"q": " mesa ", "categoria": "4", "uf": "mg"})
        self.assertEqual((state.search_text, state.category_label, state.state_label), ("mesa", "Livros", "MG"))
        fetch.assert_awaited_once()

    def test_unknown_category_shows_all_categories(self) -> None:
        state, _ = _load({"categoria": "99"})
        self.assertEqual(state.category_label, ALL_CATEGORIES_LABEL)

    def test_category_service_failure_shows_all_categories(self) -> None:
        state, _ = _load({"categoria": "4"}, error=httpx.ConnectError("offline"))
        self.assertEqual(state.category_label, ALL_CATEGORIES_LABEL)

    def test_invalid_params_are_ignored_without_request(self) -> None:
        state, fetch = _load({"categoria": "abc", "uf": "XX"})
        self.assertEqual((state.search_text, state.category_label, state.state_label), ("", "", ""))
        fetch.assert_not_called()

    def test_no_params(self) -> None:
        state, fetch = _load({})
        self.assertEqual((state.search_text, state.category_label, state.state_label), ("", "", ""))
        fetch.assert_not_called()


class ExplorePageTests(unittest.TestCase):
    def test_page_content_links_and_animation(self) -> None:
        rendered = str(explore_page())
        self.assertIn("Explorar doa\\u00e7\\u00f5es", rendered)
        self.assertIn("em constru\\u00e7\\u00e3o", rendered)
        self.assertTrue(UNDER_CONSTRUCTION_TEXT)
        self.assertIn("Nenhum filtro foi escolhido.", NO_FILTERS_TEXT)
        self.assertIn('to:"/"', rendered)
        self.assertIn('"/#doacoes-recentes"', rendered)
        self.assertIn('className:"page-fade-enter"', rendered)
        self.assertIn('role:"status"', rendered)
        # Sem resultados fictícios nem o botão flutuante do chat.
        for absent in ("Acessar", "chat-fab", "resultado"):
            self.assertNotIn(absent, rendered)

    def test_route_is_registered_with_loader(self) -> None:
        from doafacil.doafacil import app

        page = app._unevaluated_pages["explorar"]
        handlers = page.on_load if isinstance(page.on_load, list) else [page.on_load]
        self.assertEqual([handler.fn for handler in handlers], [ExploreState.load_filters.fn])


if __name__ == "__main__":
    unittest.main()
