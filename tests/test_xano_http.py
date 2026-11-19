"""Chamadas do servidor ao Xano (change navegacao-celular): nova tentativa no
429, cancelamento sem erro e o log temporário."""

import asyncio
import contextlib
import io
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from doafacil import log_xano, xano_http


class XanoHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        xano_http.install()
        self.calls = 0

    def tearDown(self) -> None:
        xano_http.uninstall()

    def _run(self, respond, url="https://xano.example/api:a/catalog/donations/count", log=False, **headers):
        def counted(request):
            self.calls += 1
            return respond(request)

        async def run():
            async with httpx.AsyncClient(transport=httpx.MockTransport(counted)) as client:
                try:
                    return await client.get(url, headers=headers)
                except BaseException as error:  # noqa: BLE001 (o teste confere o tipo)
                    return error

        stderr = io.StringIO()
        with (
            patch.dict("os.environ", {log_xano.ENV_FLAG: "1" if log else ""}),
            patch("doafacil.xano_http.asyncio.sleep", new_callable=AsyncMock) as sleep,
            contextlib.redirect_stderr(stderr),
        ):
            result = asyncio.run(run())
        return result, stderr.getvalue(), sleep

    def test_429_waits_and_retries_once(self) -> None:
        statuses = iter([429, 200])
        response, _, sleep = self._run(lambda r: httpx.Response(next(statuses)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.calls, 2)
        sleep.assert_awaited_once_with(xano_http.RETRY_DELAY_SECONDS)
        self.assertAlmostEqual(xano_http.RETRY_DELAY_SECONDS, 2.0)

    def test_second_429_is_returned(self) -> None:
        response, _, _ = self._run(lambda r: httpx.Response(429))
        self.assertEqual(response.status_code, 429)
        self.assertEqual(self.calls, 2)

    def test_other_statuses_are_not_retried(self) -> None:
        for status in (200, 404, 500):
            with self.subTest(status=status):
                self.calls = 0
                response, _, sleep = self._run(lambda r, s=status: httpx.Response(s))
                self.assertEqual((response.status_code, self.calls), (status, 1))
                sleep.assert_not_awaited()

    def test_cancelled_is_not_a_failure(self) -> None:
        def cancel(request):
            raise asyncio.CancelledError()

        error, output, _ = self._run(cancel, log=True)
        self.assertIsInstance(error, asyncio.CancelledError)
        self.assertIn("-> CANCELADA em", output)
        self.assertNotIn("FALHOU", output)

    def test_log_lines_without_private_data(self) -> None:
        statuses = iter([429, 200])
        _, output, _ = self._run(
            lambda r: httpx.Response(next(statuses)),
            url="https://xano.example/api:a/catalog/donations/search?q=cadeira&email=ana@x.com",
            log=True,
            Authorization="Bearer segredo-123",
        )
        self.assertIn("GET /api:a/catalog/donations/search -> 429 LIMITE em ", output)
        self.assertIn("GET /api:a/catalog/donations/search -> 200 (nova tentativa) em ", output)
        self.assertIn("(simultâneas: 1)", output)
        for private in ("segredo", "Bearer", "cadeira", "ana@x.com", "xano.example", "?"):
            self.assertNotIn(private, output)

    def test_log_off_without_flag(self) -> None:
        _, output, _ = self._run(lambda r: httpx.Response(200))
        self.assertEqual(output, "")

    def test_timeout_is_logged_and_raised(self) -> None:
        def timeout(request):
            raise httpx.ReadTimeout("lento", request=request)

        error, output, _ = self._run(timeout, url="https://x.example/api:a/auth/me", log=True)
        self.assertIsInstance(error, httpx.ReadTimeout)
        self.assertIn("GET /api:a/auth/me -> FALHOU TIMEOUT", output)


class InstallTests(unittest.TestCase):
    def test_lifespan_installs_and_restores(self) -> None:
        original = httpx.AsyncClient.send

        async def run():
            async with xano_http.lifespan():
                self.assertIs(httpx.AsyncClient.send, xano_http.send_with_retry)

        with contextlib.redirect_stderr(io.StringIO()):
            asyncio.run(run())
        self.assertIs(httpx.AsyncClient.send, original)

    def test_app_registers_lifespan_and_tests_run_without_it(self) -> None:
        from doafacil.doafacil import app

        self.assertIn(xano_http.lifespan, app._lifespan_tasks)
        self.assertIsNot(httpx.AsyncClient.send, xano_http.send_with_retry)

    def test_classification(self) -> None:
        self.assertEqual(log_xano.classify_status(429), "LIMITE")
        self.assertEqual(log_xano.classify_status(503), "ERRO_SERVIDOR")
        self.assertEqual(log_xano.classify_status(404), "ERRO_CLIENTE")
        request = httpx.Request("GET", "https://x.example")
        self.assertEqual(log_xano.classify_error(httpx.ConnectError("x", request=request)), "CONEXAO")


if __name__ == "__main__":
    unittest.main()
