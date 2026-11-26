"""Explorar doações (change explorar-categorias, spec donation-explore):
filtros da URL, busca paginada, “Carregar mais”, estado vazio, falhas,
título, cabeçalho com busca e layout."""

import asyncio
import re
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx

from doafacil.explorar import (
    BRAZILIAN_STATES,
    EMPTY_TEXT,
    GRID_COLUMNS,
    LOAD_ERROR_TEXT,
    LOAD_MORE_ERROR_TEXT,
    RECENT_TITLE,
    ExploreState,
    build_explore_url,
    category_icon,
    explore_page,
    explore_title,
    fetch_search_page,
    parse_explore_filters,
)

CATEGORIES = [{"id": "4", "name": "Livros", "icon": "book-open"}, {"id": "7", "name": "Roupas", "icon": "shirt"}]
NOW = datetime.now(timezone.utc).isoformat()


def _card(donation_id: int) -> dict:
    return {"id": donation_id, "created_at": NOW, "title": f"Doação {donation_id}", "photo": None, "condition": "Bom"}


def _page(ids: list[int], total: int, page_total: int) -> dict:
    return {"items": [_card(i) for i in ids], "total": total, "page_total": page_total}


class _State(SimpleNamespace):
    """Estado de teste com os campos do ExploreState."""


def _state(params: dict | None = None, path: str = "/explorar", **fields) -> _State:
    base = dict(
        # RouterData.url: os parâmetros da query string e o caminho.
        router=SimpleNamespace(url=SimpleNamespace(query_parameters=params or {}, path=path)),
        search_text="antigo",
        category_id="",
        category_label="antigo",
        state_label="",
        items=[],
        page=0,
        page_total=0,
        total=0,
        loading=True,
        loading_more=False,
        error="",
        load_more_error="",
    )
    base.update(fields)
    state = _State(**base)
    state._filters = lambda: ExploreState._filters(state)
    return state


def _run(generator) -> None:
    async def consume() -> None:
        async for _ in generator:
            pass

    asyncio.run(consume())


def _load(params: dict, page=None, categories=CATEGORIES, page_error=None, category_error=None):
    state = _state(params)
    with (
        patch("doafacil.explorar.fetch_categories", new_callable=AsyncMock, return_value=categories, side_effect=category_error) as fetch_categories,
        patch("doafacil.explorar.fetch_search_page", new_callable=AsyncMock, return_value=page or _page([], 0, 0), side_effect=page_error) as fetch_page,
    ):
        _run(ExploreState.load_filters.fn(state))
    return state, fetch_categories, fetch_page


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

    def test_build_url(self) -> None:
        self.assertEqual(build_explore_url("cadeira azul", "7", "rj"), "/explorar?q=cadeira+azul&categoria=7&uf=RJ")
        self.assertEqual(build_explore_url("", "todas", "todas"), "/explorar")

    def test_category_icons_by_name(self) -> None:
        for name, icon in (
            ("Eletrônicos", "smartphone"),
            ("eletronicos", "smartphone"),
            ("ROUPAS", "shirt"),
            (" Livros ", "book-open"),
            ("Brinquedos", "bike"),
            ("Móveis", "sofa"),
            ("moveis", "sofa"),
            ("Ferramentas", "tag"),
            (None, "tag"),
        ):
            with self.subTest(name=name):
                self.assertEqual(category_icon(name), icon)

    def test_title_from_filters(self) -> None:
        self.assertEqual(explore_title("", "", "", ""), RECENT_TITLE)
        self.assertEqual(explore_title("", "", "", "SP"), f"{RECENT_TITLE} em SP")
        self.assertEqual(explore_title("", "7", "Roupas", ""), "Categoria “Roupas”")
        self.assertEqual(explore_title("cadeira", "", "", ""), "Resultados para “cadeira”")
        self.assertEqual(
            explore_title("cadeira", "7", "Roupas", "RJ"),
            "Categoria “Roupas” · Resultados para “cadeira” em RJ",
        )
        self.assertEqual(explore_title("", "99", "", ""), "Categoria")


class FetchSearchPageTests(unittest.TestCase):
    def setUp(self) -> None:
        # Cache dos dados públicos (change navegacao-celular): validade zero,
        # para cada chamada destes testes ir ao cliente falso.
        from unittest.mock import patch as _patch

        from doafacil import cache_publico

        cache_publico.clear()
        no_cache = _patch("doafacil.cache_publico.PUBLIC_CACHE_SECONDS", 0.0)
        no_cache.start()
        self.addCleanup(no_cache.stop)

    def _fetch(self, payload, filters=None, status=200):
        seen = {}

        def respond(request: httpx.Request) -> httpx.Response:
            seen["params"] = dict(request.url.params)
            seen["path"] = request.url.path
            return httpx.Response(status, json=payload)

        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
                return await fetch_search_page(client, filters or {}, 2)

        with patch.dict("os.environ", {"XANO_API_URL": "https://xano.example/api:catalog"}):
            return asyncio.run(run()), seen

    def test_sends_only_chosen_filters(self) -> None:
        result, seen = self._fetch(_page([1], 1, 1), {"q": "mesa", "categoria": "7", "uf": "SP"})
        self.assertTrue(seen["path"].endswith("/catalog/donations/search"))
        self.assertEqual(seen["params"], {"page": "2", "q": "mesa", "category_id": "7", "state": "SP"})
        self.assertEqual([item["id"] for item in result["items"]], [1])
        _, seen = self._fetch(_page([], 0, 0), {"q": "", "categoria": "", "uf": ""})
        self.assertEqual(seen["params"], {"page": "2"})

    def test_invalid_payload_raises(self) -> None:
        for payload in ([], {"items": [], "total": "1", "page_total": 1}, {"total": 0, "page_total": 0}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self._fetch(payload)


class LoadFiltersTests(unittest.TestCase):
    def setUp(self) -> None:
        # Cache de categorias do processo (change navegacao-celular).
        from doafacil.cadastro_doacao import clear_category_cache

        clear_category_cache()
        from doafacil import cache_publico

        cache_publico.clear()
        no_cache = patch("doafacil.cache_publico.PUBLIC_CACHE_SECONDS", 0.0)
        no_cache.start()
        self.addCleanup(no_cache.stop)

    def test_no_filters_loads_first_page(self) -> None:
        state, fetch_categories, fetch_page = _load({}, _page([3, 2, 1], 3, 1))
        self.assertEqual([item["id"] for item in state.items], [3, 2, 1])
        self.assertEqual((state.page, state.page_total, state.total, state.loading), (1, 1, 3, False))
        self.assertEqual(state.search_text, "")
        fetch_categories.assert_not_called()
        self.assertEqual(fetch_page.await_args.args[1:], ({"q": "", "categoria": "", "uf": ""}, 1))

    def test_filters_and_category_name(self) -> None:
        state, fetch_categories, fetch_page = _load({"q": " mesa ", "categoria": "7", "uf": "mg"}, _page([1], 1, 1))
        self.assertEqual((state.search_text, state.category_id, state.category_label, state.state_label), ("mesa", "7", "Roupas", "MG"))
        fetch_categories.assert_awaited_once()
        self.assertEqual(fetch_page.await_args.args[1], {"q": "mesa", "categoria": "7", "uf": "MG"})

    def test_unknown_category_searches_by_id_without_name(self) -> None:
        state, _, fetch_page = _load({"categoria": "99"})
        self.assertEqual((state.category_id, state.category_label), ("99", ""))
        self.assertEqual(fetch_page.await_args.args[1]["categoria"], "99")
        self.assertEqual(state.items, [])

    def test_categories_failure_still_searches(self) -> None:
        state, _, fetch_page = _load({"categoria": "7"}, _page([1], 1, 1), category_error=httpx.ConnectError("off"))
        self.assertEqual(state.category_label, "")
        self.assertEqual(len(state.items), 1)
        fetch_page.assert_awaited_once()

    def test_invalid_params_are_ignored(self) -> None:
        state, fetch_categories, fetch_page = _load({"categoria": "abc", "uf": "XX"})
        self.assertEqual((state.category_id, state.state_label), ("", ""))
        fetch_categories.assert_not_called()
        self.assertEqual(fetch_page.await_args.args[1], {"q": "", "categoria": "", "uf": ""})

    def test_search_failure_shows_error_without_cards(self) -> None:
        state, _, _ = _load({}, page_error=httpx.ConnectError("off"))
        self.assertEqual((state.error, state.items, state.loading), (LOAD_ERROR_TEXT, [], False))


class LoadMoreTests(unittest.TestCase):
    def setUp(self) -> None:
        # Cache dos dados públicos (change navegacao-celular): validade zero,
        # para cada chamada destes testes ir ao cliente falso.
        from unittest.mock import patch as _patch

        from doafacil import cache_publico

        cache_publico.clear()
        no_cache = _patch("doafacil.cache_publico.PUBLIC_CACHE_SECONDS", 0.0)
        no_cache.start()
        self.addCleanup(no_cache.stop)

    def _more(self, state, page=None, error=None):
        with patch("doafacil.explorar.fetch_search_page", new_callable=AsyncMock, return_value=page, side_effect=error) as fetch:
            _run(ExploreState.load_more.fn(state))
        return fetch

    def test_appends_next_page_without_duplicates(self) -> None:
        state = _state(items=[_card(i) for i in (30, 29)], page=1, page_total=3, total=30, loading=False, category_id="7", search_text="mesa", state_label="SP")
        fetch = self._more(state, _page([29, 28, 27], 30, 3))
        self.assertEqual([item["id"] for item in state.items], [30, 29, 28, 27])
        self.assertEqual((state.page, state.loading_more), (2, False))
        self.assertEqual(fetch.await_args.args[1:], ({"q": "mesa", "categoria": "7", "uf": "SP"}, 2))

    def test_no_request_at_the_end_or_while_loading(self) -> None:
        for fields in ({"page": 2, "page_total": 2}, {"page": 1, "page_total": 3, "loading_more": True}, {"page": 1, "page_total": 3, "loading": True}):
            with self.subTest(fields=fields):
                state = _state(items=[_card(1)], **{"loading": False, **fields})
                fetch = self._more(state, _page([2], 2, 2))
                fetch.assert_not_called()

    def test_failure_keeps_cards(self) -> None:
        state = _state(items=[_card(1)], page=1, page_total=2, total=13, loading=False)
        self._more(state, error=httpx.ConnectError("off"))
        self.assertEqual([item["id"] for item in state.items], [1])
        self.assertEqual((state.load_more_error, state.page, state.loading_more), (LOAD_MORE_ERROR_TEXT, 1, False))


class HeaderSearchTests(unittest.TestCase):
    def test_keeps_category_on_explore_only(self) -> None:
        with patch("doafacil.explorar.rx.redirect", side_effect=lambda url: url):
            on_explore = _state(category_id="7")
            self.assertEqual(ExploreState.search.fn(on_explore, {"q": " mesa ", "uf": "sp"}), "/explorar?q=mesa&categoria=7&uf=SP")
            elsewhere = _state(category_id="7", path="/categorias")
            self.assertEqual(ExploreState.search.fn(elsewhere, {"q": "mesa", "uf": "todas"}), "/explorar?q=mesa")


class ExplorePageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rendered = str(explore_page())

    def test_header_with_search_uf_and_auth(self) -> None:
        r = self.rendered
        self.assertIn('id:"explore-search"', r)
        self.assertIn('name:"q"', r)
        self.assertIn('name:"uf"', r)
        self.assertIn('placeholder:"Buscar"', r)
        self.assertIn('"aria-label":"Buscar doa\\u00e7\\u00f5es"', r)
        self.assertIn('"aria-label":"Localiza\\u00e7\\u00e3o"', r)
        self.assertIn('type:"submit"', r)
        self.assertIn("handleSubmit", r)
        for uf in ('"SP"', '"RJ"', '"TO"'):
            self.assertIn(uf, r)
        self.assertIn("home-account-menu", r)
        self.assertIn('"Quero Doar"', r.replace("Quero Doar", '"Quero Doar"'))
        # O campo e o seletor refletem a URL (remontados pela chave).
        self.assertIn("explore_state.search_text", r)
        self.assertIn("explore_state.state_select_value", r)

    def test_header_search_takes_its_own_line_below_992px(self) -> None:
        """Change correcoes-revisao: com `flex: 1` (base 0%), a busca ficava
        espremida ao lado do logotipo em 360 px, com o campo em 0 px. Abaixo
        de 992 px, a base é 100% (linha própria); a partir dela, 0% (divide a
        linha com o logotipo e a conta, até 620 px)."""
        r = self.rendered
        start = r.index('className:"Root explore-header-search"')
        form = r[start : r.index("onSubmit", start)]
        self.assertIn('(min-width: 0px)"] : ({ ["flex"] : "1 1 100%", ["order"] : "3" })', form)
        self.assertIn('(min-width: 62em)"] : ({ ["flex"] : "1 1 0%", ["order"] : "2" })', form)
        self.assertIn('["maxWidth"] : "620px"', form)
        self.assertNotIn('["width"]', form)

    def test_logo_same_size_as_home(self) -> None:
        from doafacil.doafacil import index

        logo = '["@media screen and (min-width: 0px)"] : ({ ["width"] : "100px" }), ["@media screen and (min-width: 62em)"] : ({ ["width"] : "190px" })'
        self.assertIn(logo, self.rendered)
        self.assertIn(logo, str(index().children[0].children[0]))
        self.assertIn('["height"] : "72px"', self.rendered)

    def test_uf_select_in_dark_gray_with_aa_contrast(self) -> None:
        r = self.rendered
        start = r.index('"aria-label":"Localiza\\u00e7\\u00e3o"')
        trigger = r[start : r.index("})", start)]
        self.assertIn('color:"gray"', r[r.rindex("RadixThemesSelect.Trigger", 0, start) : start + len(trigger)])
        self.assertIn('["color"] : "#333333"', trigger)

        def luminance(color: str) -> float:
            channels = [int(color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
            linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        high, low = sorted((luminance("#333333"), luminance("#EFEFEF")), reverse=True)
        self.assertGreaterEqual((high + 0.05) / (low + 0.05), 4.5)

    def test_links_title_and_chip(self) -> None:
        r = self.rendered
        self.assertIn('className:"explore-back-link"', r)
        self.assertIn("Voltar ao in\\u00edcio", r)
        self.assertIn('to:"/categorias"', r)
        self.assertIn("explore_state.title", r)
        self.assertIn("explore-category-chip", r)
        self.assertIn("explore_state.remove_category_url", r)
        self.assertIn('"aria-label":"Remover o filtro de categoria"', r)

    def test_results_states(self) -> None:
        r = self.rendered
        self.assertIn("explore-grid", r)
        self.assertIn(f'["gridTemplateColumns"] : "{GRID_COLUMNS}"', r)
        self.assertIn("Carregar mais", r)
        self.assertIn("explore-load-more", r)
        self.assertEqual(EMPTY_TEXT, "Nenhuma doação encontrada")
        self.assertIn("Nenhuma doa\\u00e7\\u00e3o encontrada", r)
        self.assertIn("explore-clear-filters", r)
        self.assertIn('to:"/explorar"', r)
        self.assertIn("Tentar de novo", r)
        self.assertGreaterEqual(r.count('role:"status"'), 3)

    def test_empty_without_filters_invites_to_donate(self) -> None:
        # Change correcoes-finais: sem filtros e sem resultados, o convite e o
        # “Quero Doar”; com filtros, o “Limpar filtros” no lugar dele.
        from doafacil.explorar import DONATE_LABEL, EMPTY_INVITE_TEXT, _donate_invite, _results

        invite = str(_donate_invite())
        self.assertEqual(DONATE_LABEL, "Quero Doar")
        self.assertIn("Que tal ser a primeira pessoa a doar?", EMPTY_INVITE_TEXT)
        self.assertIn('className:"explore-donate"', invite)
        # Com sessão, o cadastro; sem sessão, o login com next de volta a ele.
        self.assertIn("login_state.auth_token", invite)
        self.assertIn('"/cadastro-doacao"', invite)
        self.assertIn('"/login?next=/cadastro-doacao"', invite)
        self.assertIn('["minHeight"] : "44px"', invite)
        self.assertIn('"#166B3B"', invite)

        results = str(_results())
        cond_start = results.index("explore_state.has_filters")
        after = results[cond_start:]
        self.assertLess(after.index("explore-clear-filters"), after.index("explore-donate"))

    def test_animation_chat_and_layout(self) -> None:
        r = self.rendered
        # A animação só no conteúdo estático (link, título, chip), não na grade.
        self.assertEqual(r.count('className:"page-fade-enter"'), 1)
        fade_block = r[r.index('className:"page-fade-enter"') :]
        self.assertLess(fade_block.index("explore-category-chip"), fade_block.index("explore-grid"))
        self.assertEqual(r.count("chat-fab"), 1)
        self.assertIn('["paddingBottom"] : "88px"', r)
        self.assertGreaterEqual(r.count('["minHeight"] : "44px"'), 5)
        # Nenhuma largura fixa maior que 360 px.
        self.assertIsNone(re.search(r'\["(?:min)?[wW]idth"\] : "(3[7-9]\d|[4-9]\d\d|\d{4,})px"', r))
        self.assertIn("minmax(min(100%, 220px), 1fr)", GRID_COLUMNS)


if __name__ == "__main__":
    unittest.main()
