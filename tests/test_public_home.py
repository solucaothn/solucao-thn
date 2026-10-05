import asyncio
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import httpx

from doafacil.doafacil import (
    _fetch_donation_count,
    _fetch_recent_donations,
    _is_new_donation,
    _load_count_result,
    _load_donations_result,
    _parse_donations,
    _xano_endpoints,
)


class PublicHomeTests(unittest.TestCase):
    def test_endpoint_urls_use_xano_api_url_environment_variable(self) -> None:
        with patch.dict(
            os.environ,
            {"XANO_API_URL": "https://xano.example/api:catalog/"},
        ):
            self.assertEqual(
                _xano_endpoints(),
                (
                    "https://xano.example/api:catalog/catalog/donations/recent",
                    "https://xano.example/api:catalog/catalog/donations/count",
                ),
            )

    def test_new_badge_includes_exact_seven_day_boundary(self) -> None:
        now = datetime(2026, 1, 8, tzinfo=timezone.utc)
        exactly_seven_days_ago = (now - timedelta(days=7)).isoformat()
        older_than_seven_days = (now - timedelta(days=7, seconds=1)).isoformat()
        future_date = (now + timedelta(seconds=1)).isoformat()

        self.assertTrue(_is_new_donation(exactly_seven_days_ago, now))
        self.assertFalse(_is_new_donation(older_than_seven_days, now))
        self.assertFalse(_is_new_donation(future_date, now))

    def test_optional_card_data_uses_required_fallbacks(self) -> None:
        now = datetime(2026, 1, 8, tzinfo=timezone.utc)
        donations = _parse_donations(
            [
                {
                    "id": 1,
                    "created_at": now.isoformat(),
                    "title": "Cadeira",
                    "photo": None,
                    "condition": None,
                }
            ],
            now,
        )

        self.assertEqual(donations[0]["photo"], "/doacao-generica.svg")
        self.assertEqual(
            donations[0]["condition_label"], "Condição não informada"
        )
        self.assertTrue(donations[0]["is_new"])

    def test_empty_recent_response_stays_empty(self) -> None:
        self.assertEqual(_parse_donations([]), [])

    def test_recent_endpoint_payload_maps_card_fields(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("/catalog/donations/recent"))
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 2,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "title": "Mesa",
                        "photo": "https://images.example/mesa.jpg",
                        "condition": "Bom",
                    }
                ],
            )

        async def fetch() -> list[dict[str, str | int | bool]]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_recent_donations(
                    client,
                    "https://xano.example/api:catalog/catalog/donations/recent",
                )

        donations = asyncio.run(fetch())
        self.assertEqual(donations[0]["title"], "Mesa")
        self.assertEqual(donations[0]["photo"], "https://images.example/mesa.jpg")
        self.assertEqual(donations[0]["condition_label"], "Condição: Bom")

    def test_recent_endpoint_accepts_xano_epoch_milliseconds(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("/catalog/donations/recent"))
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 4,
                        "created_at": 1790134916685,
                        "title": "aaaaa",
                        "photo": None,
                        "condition": None,
                    },
                    {
                        "id": 3,
                        "created_at": 1790040131218,
                        "title": "iphone 6",
                        "photo": None,
                        "condition": None,
                    },
                ],
            )

        async def fetch() -> list[dict[str, str | int | bool]]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_recent_donations(
                    client,
                    "https://xano.example/api:catalog/catalog/donations/recent",
                )

        donations = asyncio.run(fetch())

        self.assertEqual([donation["id"] for donation in donations], [4, 3])
        self.assertEqual([donation["title"] for donation in donations], ["aaaaa", "iphone 6"])
        self.assertTrue(
            all(
                donation["photo"] == "/doacao-generica.svg"
                and donation["condition_label"] == "Condição não informada"
                for donation in donations
            )
        )

    def test_count_endpoint_returns_count(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("/catalog/donations/count"))
            return httpx.Response(200, json={"count": 3})

        async def fetch() -> int:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_donation_count(
                    client,
                    "https://xano.example/api:catalog/catalog/donations/count",
                )

        self.assertEqual(asyncio.run(fetch()), 3)

    def test_invalid_count_is_reported(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("/count"))
            return httpx.Response(200, json={"count": "3"})

        async def fetch() -> int:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await _fetch_donation_count(client, "https://xano.example/count")

        with self.assertRaises(ValueError):
            asyncio.run(fetch())

    def test_endpoint_failures_are_independent(self) -> None:
        async def respond(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/count"):
                return httpx.Response(503)
            return httpx.Response(200, json=[])

        async def fetch() -> tuple[int | Exception, object]:
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(respond)
            ) as client:
                return await asyncio.gather(
                    _load_count_result(client, "https://xano.example/count"),
                    _load_donations_result(
                        client, "https://xano.example/recent"
                    ),
                )

        count_result, donations_result = asyncio.run(fetch())

        self.assertIsInstance(count_result, httpx.HTTPStatusError)
        self.assertEqual(donations_result, [])


if __name__ == "__main__":
    unittest.main()
