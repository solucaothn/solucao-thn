"""Cache dos dados públicos de doações (change navegacao-celular): contagem,
recentes, busca e detalhe guardados por 60 s para todos, limpos quando uma
doação muda."""

import asyncio
import unittest
from unittest.mock import patch

import httpx

from doafacil import cache_publico

ENV = {"XANO_API_URL": "https://xano.example/api:catalog"}


class CachedTests(unittest.TestCase):
    def setUp(self) -> None:
        cache_publico.clear()
        self.loads = 0

    def _load(self, value=None, error=None):
        async def load():
            self.loads += 1
            if error is not None:
                raise error
            return value

        return load

    def _get(self, key="k", **kwargs):
        return asyncio.run(cache_publico.cached(cache_publico.COUNT, key, self._load(**kwargs)))

    def test_second_call_reuses(self) -> None:
        self.assertEqual(self._get(value=[1]), [1])
        self.assertEqual(self._get(value=[2]), [1])
        self.assertEqual(self.loads, 1)

    def test_failure_is_not_cached(self) -> None:
        with self.assertRaises(ValueError):
            self._get(error=ValueError("x"))
        self.assertEqual(self._get(value=[3]), [3])
        self.assertEqual(self.loads, 2)

    def test_expires_after_60_seconds(self) -> None:
        self.assertEqual(cache_publico.PUBLIC_CACHE_SECONDS, 60.0)
        with patch("doafacil.cache_publico.time.monotonic", return_value=100.0):
            self._get(value=[1])
        with patch("doafacil.cache_publico.time.monotonic", return_value=159.0):
            self._get(value=[2])
        self.assertEqual(self.loads, 1)
        with patch("doafacil.cache_publico.time.monotonic", return_value=161.0):
            self.assertEqual(self._get(value=[2]), [2])
        self.assertEqual(self.loads, 2)

    def test_callers_get_copies(self) -> None:
        first = self._get(value={"items": [1]})
        first["items"].append(99)
        self.assertEqual(self._get(value=None), {"items": [1]})

    def test_invalidate_donations(self) -> None:
        self._get(value=1)
        cache_publico.invalidate_donations()
        self._get(value=2)
        self.assertEqual(self.loads, 2)


class _Transport:
    """Cliente falso que conta os pedidos por caminho e guarda os cabeçalhos."""

    def __init__(self, respond):
        self.respond = respond
        self.paths: list[str] = []
        self.headers: list[httpx.Headers] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.paths.append(request.url.path)
        self.headers.append(request.headers)
        return self.respond(request)


def _run(transport, *calls):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            return [await call(client) for call in calls]

    with patch.dict("os.environ", ENV):
        return asyncio.run(run())




class PagesUseTheCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        cache_publico.clear()

    def test_search_cached_per_filters_and_page(self) -> None:
        from doafacil.explorar import fetch_search_page

        page = {"items": [], "total": 0, "page_total": 0}
        transport = _Transport(lambda r: httpx.Response(200, json=page))
        _run(
            transport,
            lambda c: fetch_search_page(c, {"q": "mesa"}, 1),
            lambda c: fetch_search_page(c, {"q": "mesa"}, 1),
            lambda c: fetch_search_page(c, {"q": "mesa"}, 2),
            lambda c: fetch_search_page(c, {"q": "cadeira"}, 1),
        )
        self.assertEqual(len(transport.paths), 3)

    def test_home_count_and_recent_cached(self) -> None:
        from doafacil.doafacil import _fetch_donation_counts, _fetch_recent_donations

        def respond(request):
            if request.url.path.endswith("count"):
                return httpx.Response(200, json={"count": 3, "completed": 1})
            return httpx.Response(200, json=[])

        transport = _Transport(respond)
        count_url = "https://xano.example/api:catalog/catalog/donations/count"
        recent_url = "https://xano.example/api:catalog/catalog/donations/recent"
        results = _run(
            transport,
            lambda c: _fetch_donation_counts(c, count_url),
            lambda c: _fetch_recent_donations(c, recent_url),
            lambda c: _fetch_donation_counts(c, count_url),
            lambda c: _fetch_recent_donations(c, recent_url),
        )
        self.assertEqual(results[0], (3, 1))
        self.assertEqual(results[2], (3, 1))
        self.assertEqual(len(transport.paths), 2)

    def test_detail_cached_per_id_without_private_data(self) -> None:
        from doafacil.detalhe_doacao import _fetch_donation_detail
        from tests.test_donation_detail import DETAIL_PAYLOAD

        def respond(request):
            donation_id = int(request.url.params["donation_id"])
            return httpx.Response(200, json={**DETAIL_PAYLOAD, "id": donation_id})

        transport = _Transport(respond)
        base = ENV["XANO_API_URL"]
        first, again, other = _run(
            transport,
            lambda c: _fetch_donation_detail(c, base, "42"),
            lambda c: _fetch_donation_detail(c, base, "42"),
            lambda c: _fetch_donation_detail(c, base, "43"),
        )
        self.assertEqual(len(transport.paths), 2)  # 42 uma vez e 43 uma vez
        self.assertEqual((first["id"], again["id"], other["id"]), (42, 42, 43))
        # Dado público: o pedido não leva credenciais, e o guardado não tem
        # os campos privados que a resposta trazia.
        for headers in transport.headers:
            self.assertNotIn("authorization", {key.lower() for key in headers})
        stored = repr(cache_publico._entries)
        for private in ("private@example.com", "owner_id", "Rua privada", "Silva", "00000-000"):
            self.assertNotIn(private, stored)


class WritesInvalidateTests(unittest.TestCase):
    def setUp(self) -> None:
        cache_publico.clear()

    def _seed(self) -> None:
        async def load():
            return [1]

        asyncio.run(cache_publico.cached(cache_publico.SEARCH, "chave", load))
        self.assertTrue(cache_publico._entries)

    def _write(self, call, status: int, payload: object) -> None:
        transport = _Transport(lambda r: httpx.Response(status, json=payload))
        try:
            _run(transport, call)
        except Exception:  # noqa: BLE001 (o teste só confere o cache)
            pass

    def test_status_edit_and_delete_clear_on_success(self) -> None:
        from doafacil.minhas_doacoes import change_status, delete_donation, update_donation

        for name, call, payload in (
            ("status", lambda c: change_status(c, "tok", 7, "reservada"), {"status": "reservada"}),
            ("edição", lambda c: update_donation(c, "tok", 7, {"title": "x"}), {"id": 7}),
            ("apagar", lambda c: delete_donation(c, "tok", 7), {"deleted": True}),
        ):
            with self.subTest(acao=name):
                self._seed()
                self._write(call, 200, payload)
                self.assertEqual(cache_publico._entries, {})

    def test_failed_write_keeps_cache(self) -> None:
        from doafacil.minhas_doacoes import delete_donation

        self._seed()
        self._write(lambda c: delete_donation(c, "tok", 7), 500, {})
        self.assertTrue(cache_publico._entries)

    def test_publish_clears_on_success(self) -> None:
        from doafacil.cadastro_doacao import _publish_donation

        self._seed()
        self._write(
            lambda c: _publish_donation(c, "https://xano.example/api:catalog/catalog/donations/publish", "tok", {"title": "x"}, []),
            200,
            {"donation": {"id": 9, "status": "disponível"}},
        )
        self.assertEqual(cache_publico._entries, {})


if __name__ == "__main__":
    unittest.main()
