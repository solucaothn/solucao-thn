"""Chamadas do servidor ao Xano (change navegacao-celular).

O plano grátis do Xano aceita 10 pedidos a cada 20 s para o site inteiro.
Este módulo envolve o `httpx.AsyncClient.send` do servidor do Reflex (todas
as chamadas HTTP do servidor são ao Xano) para:

- 429: esperar ~2 s e tentar uma vez de novo antes de devolver o erro a quem
  chamou (que mostra a mensagem de falha da página);
- cancelamento (a pessoa navegou e o Reflex cancelou o evento): não é falha;
  o `CancelledError` segue adiante sem virar mensagem de erro;
- log temporário: com DOAFACIL_LOG_XANO=1, cada tentativa sai numa linha
  `[xano]` no terminal (ver log_xano.py).

É instalado pelo lifespan do app (`app.register_lifespan_task(lifespan)` em
doafacil.py), ou seja, só quando o servidor sobe; os testes importam o app
sem ativar o wrapper.
"""

from __future__ import annotations

import asyncio
import contextlib
import time

import httpx

from doafacil import log_xano

RETRY_STATUS = 429
RETRY_DELAY_SECONDS = 2.0
_original_send = httpx.AsyncClient.send
_in_flight = 0


async def _send_once(client: httpx.AsyncClient, request: httpx.Request, attempt: int, **kwargs) -> httpx.Response:
    global _in_flight
    _in_flight += 1
    concurrent = _in_flight
    start = time.perf_counter()
    suffix = " (nova tentativa)" if attempt > 1 else ""
    try:
        response = await _original_send(client, request, **kwargs)
    except asyncio.CancelledError:
        # Navegação cancelou o pedido: não é falha.
        if log_xano.enabled():
            elapsed = (time.perf_counter() - start) * 1000
            log_xano.write(log_xano.format_line(request.method, str(request.url), "CANCELADA" + suffix, elapsed, concurrent))
        raise
    except Exception as error:
        if log_xano.enabled():
            elapsed = (time.perf_counter() - start) * 1000
            outcome = f"FALHOU {log_xano.classify_error(error)}{suffix}"
            log_xano.write(log_xano.format_line(request.method, str(request.url), outcome, elapsed, concurrent))
        raise
    finally:
        _in_flight -= 1
    if log_xano.enabled():
        elapsed = (time.perf_counter() - start) * 1000
        outcome = f"{response.status_code} {log_xano.classify_status(response.status_code)}".strip() + suffix
        log_xano.write(log_xano.format_line(request.method, str(request.url), outcome, elapsed, concurrent))
    return response


async def send_with_retry(client: httpx.AsyncClient, request: httpx.Request, **kwargs) -> httpx.Response:
    """Envia; num 429, espera RETRY_DELAY_SECONDS e tenta uma vez de novo."""
    response = await _send_once(client, request, 1, **kwargs)
    if response.status_code != RETRY_STATUS:
        return response
    await response.aclose()
    await asyncio.sleep(RETRY_DELAY_SECONDS)
    return await _send_once(client, request, 2, **kwargs)


def install() -> None:
    httpx.AsyncClient.send = send_with_retry  # type: ignore[method-assign]
    if log_xano.enabled():
        log_xano.write(f"[xano] log temporário de chamadas ao Xano ligado ({log_xano.ENV_FLAG}=1).")


def uninstall() -> None:
    httpx.AsyncClient.send = _original_send  # type: ignore[method-assign]


@contextlib.asynccontextmanager
async def lifespan():
    """Tarefa de lifespan do app: liga o wrapper enquanto o servidor roda."""
    install()
    try:
        yield
    finally:
        uninstall()
