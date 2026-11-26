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
    def setUp(self) -> None:
        # Cache de categorias do processo (change navegacao-celular).
        from doafacil.cadastro_doacao import clear_category_cache

        clear_category_cache()

    def test_adds_icon_without_name_exclusions(self) -> None:
        # Change correcoes-finais: “Móveis” aparece, com o ícone de sofá; um
        # item inválido é ignorado sem quebrar a lista.
        def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json=[
                    {"id": 1, "name": "Eletrônicos"},
                    {"id": 2, "name": "Móveis"},
                    {"id": None, "name": "Alimentos"},
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
                {"id": "2", "name": "Móveis", "icon": "sofa"},
                {"id": "4", "name": "Ferramentas", "icon": "tag"},
            ],
        )


class CategoriesStateTests(unittest.TestCase):
    def setUp(self) -> None:
        # Cache de categorias do processo (change navegacao-celular).
        from doafacil.cadastro_doacao import clear_category_cache

        clear_category_cache()

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
        from doafacil.doafacil import INSTITUTIONAL_ROUTES, app

        self.assertNotIn("categorias", INSTITUTIONAL_ROUTES)
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


class CategoryCacheTests(unittest.TestCase):
    """Change navegacao-celular: categorias buscadas uma vez e reaproveitadas
    (limite do plano grátis do Xano: 10 pedidos a cada 20 s)."""

    ENV = {"XANO_API_URL": "https://xano.example/api:catalog"}
    PAYLOAD = [{"id": 1, "name": "Eletrônicos"}, {"id": 4, "name": "Ferramentas"}]

    def setUp(self) -> None:
        from doafacil.cadastro_doacao import clear_category_cache

        clear_category_cache()
        self.requests = 0
        self.status = 200

    def _respond(self, request: httpx.Request) -> httpx.Response:
        self.requests += 1
        return httpx.Response(self.status, json=self.PAYLOAD if self.status == 200 else {})

    def _run(self, *calls):
        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(self._respond)) as client:
                return [await call(client) for call in calls]

        with patch.dict("os.environ", self.ENV):
            return asyncio.run(run())

    def test_every_page_reuses_one_request(self) -> None:
        from doafacil.cadastro_doacao import CATALOG_API_ENV, _api_endpoint, _fetch_categories
        from doafacil.doafacil import _load_categories_result

        async def creation(client):  # cadastro e edição de doação
            return await _fetch_categories(client, _api_endpoint(CATALOG_API_ENV, "/catalog/categories"))

        # Home (busca e gaveta), /categorias e Explorar, cadastro de doação.
        home, page, explore, form = self._run(_load_categories_result, fetch_categories, fetch_categories, creation)
        self.assertEqual(self.requests, 1)
        self.assertEqual(home, page)
        self.assertEqual(page, explore)
        self.assertEqual([category["name"] for category in form], ["Eletrônicos", "Ferramentas"])

    def test_failure_is_not_cached(self) -> None:
        from doafacil.cadastro_doacao import DonationServiceError

        self.status = 500

        async def failing(client):
            try:
                return await fetch_categories(client)
            except DonationServiceError:
                return "falhou"

        self.assertEqual(self._run(failing), ["falhou"])
        self.status = 200
        (categories,) = self._run(fetch_categories)
        self.assertEqual(len(categories), 2)
        self.assertEqual(self.requests, 2)

    def test_expires_after_an_hour(self) -> None:
        from doafacil import cadastro_doacao

        with patch("doafacil.cadastro_doacao.time.monotonic", return_value=1000.0):
            self._run(fetch_categories)
        with patch("doafacil.cadastro_doacao.time.monotonic", return_value=1000.0 + cadastro_doacao.CATEGORY_CACHE_SECONDS - 1):
            self._run(fetch_categories)
        self.assertEqual(self.requests, 1)
        with patch("doafacil.cadastro_doacao.time.monotonic", return_value=1000.0 + cadastro_doacao.CATEGORY_CACHE_SECONDS + 1):
            self._run(fetch_categories)
        self.assertEqual(self.requests, 2)

    def test_callers_get_copies(self) -> None:
        from doafacil.cadastro_doacao import CATALOG_API_ENV, _api_endpoint, _fetch_categories

        async def creation(client):
            return await _fetch_categories(client, _api_endpoint(CATALOG_API_ENV, "/catalog/categories"))

        (first,) = self._run(creation)
        first[0]["name"] = "alterado"
        first.clear()
        (second,) = self._run(creation)
        self.assertEqual(second[0]["name"], "Eletrônicos")
        self.assertEqual(self.requests, 1)


class RetryTests(unittest.TestCase):
    def test_failure_offers_retry_on_page_and_drawer(self) -> None:
        page = str(categories_page())
        self.assertIn('"Tentar de novo"', page)
        # Change correcoes-revisao: a /categorias usa o retry_categories, que
        # mostra o carregando na hora.
        self.assertIn("retry_categories", page[page.index('className:"category-retry"') :][:600])
        from doafacil.doafacil import index

        home = str(index())
        retry = home[home.index('className:"category-retry"') :][:600]
        self.assertIn("reload_categories", retry)
        self.assertIn('["minHeight"] : "44px"', retry)

    def test_without_retry_handler_there_is_no_button(self) -> None:
        self.assertNotIn("Tentar de novo", str(category_list(CategoriesState.categories)))

    def test_home_reload_categories(self) -> None:
        """Change correcoes-revisao: a gaveta mostra o carregando antes do
        pedido (o primeiro `yield`), com um único pedido."""
        from doafacil.doafacil import HomeState

        state = SimpleNamespace(categories=[], categories_loading=False)
        seen: list[bool] = []

        async def load(client):
            seen.append(state.categories_loading)
            return CATEGORIES

        async def collect():
            return [(event, state.categories_loading) async for event in HomeState.reload_categories.fn(state)]

        with patch("doafacil.doafacil._load_categories_result", side_effect=load):
            steps = asyncio.run(collect())
        self.assertEqual(steps, [(None, True)])
        self.assertEqual(seen, [True])
        self.assertEqual(state.categories, CATEGORIES)
        self.assertFalse(state.categories_loading)

    def test_home_reload_failure_turns_loading_off(self) -> None:
        from doafacil.doafacil import HomeState

        state = SimpleNamespace(categories=[], categories_loading=False)

        async def collect():
            return [event async for event in HomeState.reload_categories.fn(state)]

        with patch("doafacil.doafacil._load_categories_result", new_callable=AsyncMock, return_value=[]):
            self.assertEqual(asyncio.run(collect()), [None])
        self.assertEqual(state.categories, [])
        self.assertFalse(state.categories_loading)

    def test_page_retry_shows_loading_and_reloads(self) -> None:
        state = SimpleNamespace(loading=False, categories=[])
        result = CategoriesState.retry_categories.fn(state)
        self.assertTrue(state.loading)
        self.assertIs(result, CategoriesState.load_categories)

    def test_drawer_shows_loading_while_retrying(self) -> None:
        from doafacil.doafacil import index

        home = str(index())
        start = home.index('className:"categories-drawer"')
        self.assertIn("categories_loading", home[start:])
        self.assertIn("Carregando categorias...", home)
