"""Categorias (change explorar-categorias, spec donation-categories): a lista
com ícones, a página /categorias e a gaveta da home."""

import asyncio
import re
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx

from doafacil.categorias import (
    CATEGORIES_ERROR_TEXT,
    CategoriesState,
    categories_drawer,
    categories_page,
    category_list,
)
from doafacil.explorar import CATEGORY_ICONS, fetch_categories

CATEGORIES = [{"id": "4", "name": "Livros", "icon": "book-open"}, {"id": "7", "name": "Roupas", "icon": "shirt"}]


class FetchCategoriesTests(unittest.TestCase):
    def test_adds_icon_and_applies_creation_exclusions(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json=[
                    {"id": 1, "name": "Eletrônicos"},
                    {"id": 2, "name": "Móveis"},
                    {"id": 3, "name": "Alimentos"},
                    {"id": 4, "name": "Ferramentas"},
                ],
            )

        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
                return await fetch_categories(client)

        with patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api:catalog"}):
            categories = asyncio.run(run())
        self.assertEqual(
            categories,
            [
                {"id": "1", "name": "Eletrônicos", "icon": "smartphone"},
                {"id": "4", "name": "Ferramentas", "icon": "tag"},
            ],
        )


class CategoriesStateTests(unittest.TestCase):
    def _load(self, result=None, error=None):
        state = SimpleNamespace(categories=[], loading=True, drawer_open=False)
        with patch("doafacil.categorias.fetch_categories", new_callable=AsyncMock, return_value=result, side_effect=error):
            asyncio.run(CategoriesState.load_categories.fn(state))
        return state

    def test_loads_categories(self) -> None:
        state = self._load(CATEGORIES)
        self.assertEqual((state.categories, state.loading), (CATEGORIES, False))

    def test_failure_leaves_empty_list(self) -> None:
        state = self._load(error=httpx.ConnectError("off"))
        self.assertEqual((state.categories, state.loading), ([], False))

    def test_drawer_open_and_close(self) -> None:
        state = SimpleNamespace(drawer_open=False)
        CategoriesState.set_drawer_open.fn(state, True)
        self.assertTrue(state.drawer_open)
        CategoriesState.close_drawer.fn(state)
        self.assertFalse(state.drawer_open)


class CategoryListTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rendered = str(category_list(CategoriesState.categories, CategoriesState.loading))

    def test_links_to_filtered_explore_with_icons(self) -> None:
        r = self.rendered
        self.assertIn('("/explorar?categoria="+', r)
        self.assertIn('className:"category-link"', r)
        self.assertIn("LucideChevronRight", r)
        for icon in set(CATEGORY_ICONS.values()) | {"tag"}:
            lucide = "Lucide" + "".join(part.capitalize() for part in icon.split("-"))
            with self.subTest(icon=icon):
                self.assertIn(lucide, r)
        # 56 px de altura em cada categoria (mais que os 44 px mínimos).
        self.assertIn('["minHeight"] : "56px"', r)

    def test_loading_and_failure(self) -> None:
        r = self.rendered
        self.assertIn("Carregando categorias...", r)
        self.assertEqual(CATEGORIES_ERROR_TEXT, "Não foi possível carregar as categorias.")
        self.assertIn("N\\u00e3o foi poss\\u00edvel carregar as categorias.", r)
        self.assertIn('"Explorar doa\\u00e7\\u00f5es"', r)
        self.assertGreaterEqual(r.count('role:"status"'), 2)


class CategoriesPageTests(unittest.TestCase):
    def test_page_title_back_link_animation_and_chat(self) -> None:
        r = str(categories_page())
        self.assertIn('"Categorias"', r)
        self.assertIn('className:"explore-back-link"', r)
        self.assertEqual(r.count('className:"page-fade-enter"'), 1)
        self.assertEqual(r.count("chat-fab"), 1)
        self.assertIn("category-list", r)
        self.assertIsNone(re.search(r'\["(?:min)?[wW]idth"\] : "(3[7-9]\d|[4-9]\d\d|\d{4,})px"', r))

    def test_route_is_registered(self) -> None:
        from doafacil.doafacil import FUTURE_ROUTES, app

        self.assertNotIn("categorias", FUTURE_ROUTES)
        on_load = app._unevaluated_pages["categorias"].on_load
        handlers = on_load if isinstance(on_load, list) else [on_load]
        self.assertIn(CategoriesState.load_categories.fn, [h.fn for h in handlers])


class CategoriesDrawerTests(unittest.TestCase):
    def setUp(self) -> None:
        import reflex as rx

        self.drawer = categories_drawer(CategoriesState.categories, rx.button("Categorias"))
        self.rendered = str(self.drawer)

    def test_dialog_on_the_left_with_title_and_close(self) -> None:
        r = self.rendered
        self.assertIn("RadixThemesDialog.Root", r)
        self.assertIn('className:"categories-drawer"', r)
        self.assertIn('["left"] : "0"', r)
        self.assertIn('["height"] : "100dvh"', r)
        self.assertIn('["width"] : "min(500px, 100vw)"', r)
        self.assertIn("RadixThemesDialog.Title", r)
        self.assertIn('"aria-label":"Fechar"', r)
        self.assertIn("RadixThemesDialog.Close", r)
        self.assertIn("categories_state.drawer_open", r)

    def test_choosing_a_category_closes_the_drawer(self) -> None:
        self.assertIn("categories_state.close_drawer", self.rendered)
        self.assertIn('("/explorar?categoria="+', self.rendered)
        self.assertIn("on_open_change", self.drawer.event_triggers)

    def test_home_trigger(self) -> None:
        from doafacil.doafacil import index

        header = str(index().children[0].children[0])
        self.assertIn('className:"home-categories-trigger"', header)
        self.assertIn('"aria-haspopup":"dialog"', header)
        self.assertIn('["minHeight"] : "44px"', header)
        self.assertIn("home_state.categories", header)

    def test_home_trigger_looks_like_the_menu_links(self) -> None:
        """Um <button> HTML puro, com o mesmo visual de “Explorar Doações” e
        “Como funciona” (sem o fundo, a borda e a altura do botão do Radix)."""
        from doafacil.doafacil import _categories_trigger, _nav_link

        trigger = str(_categories_trigger())
        link = str(_nav_link("Como funciona", "/como-funciona"))
        self.assertTrue(trigger.startswith('jsx("button"'))
        self.assertNotIn("RadixThemesButton", trigger)
        self.assertIn('type:"button"', trigger)
        for rule in ('["border"] : "none"', '["background"] : "transparent"', '["padding"] : "0"', '["fontFamily"] : "inherit"'):
            self.assertIn(rule, trigger)
        # Mesmas cor, peso, tamanho (responsivo), altura e alinhamento.
        for rule in (
            '["color"] : "#168447"',
            '["fontWeight"] : "700"',
            '["whiteSpace"] : "nowrap"',
            '["display"] : "inline-flex"',
            '["alignItems"] : "center"',
            '["minHeight"] : "44px"',
            '["@media screen and (min-width: 0px)"] : ({ ["fontSize"] : "0.875rem" })',
            '["@media screen and (min-width: 80em)"] : ({ ["fontSize"] : "1rem" })',
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, trigger)
                self.assertIn(rule, link)


if __name__ == "__main__":
    unittest.main()
