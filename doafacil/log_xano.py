"""TEMPORÁRIO (diagnóstico da change navegacao-celular): log de toda chamada
HTTP que o servidor do Reflex faz ao Xano.

Liga com a variável de ambiente DOAFACIL_LOG_XANO=1 antes do `reflex run`:

    $env:DOAFACIL_LOG_XANO = "1"; reflex run          (PowerShell)

Cada linha sai no terminal do Reflex assim:

    [xano] 14:03:07.512 GET /api:XXXX/catalog/categories -> 200 em 143 ms (simultâneas: 3)
    [xano] 14:03:07.530 GET /api:XXXX/catalog/donations/count -> 429 LIMITE em 88 ms (simultâneas: 3)

O que o log NÃO mostra, de propósito: a query string (pode ter o texto da
busca), os cabeçalhos (o token vai no Authorization), os corpos e o host.
Mostra só o método, o caminho, o status, a categoria do erro (LIMITE para
429, ERRO_SERVIDOR para 5xx, ERRO_CLIENTE para os outros 4xx, TIMEOUT,
CONEXAO ou o nome da exceção), o tempo em ms e quantas chamadas estavam em
andamento quando esta começou.

Quem chama é o doafacil/xano_http.py (a nova tentativa no 429 e o
tratamento do cancelamento ficam lá). Remover este módulo quando o
diagnóstico terminar.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from urllib.parse import urlsplit

import httpx

ENV_FLAG = "DOAFACIL_LOG_XANO"


def enabled() -> bool:
    return os.getenv(ENV_FLAG, "").strip() == "1"


def classify_status(status: int) -> str:
    if status == 429:
        return "LIMITE"
    if status >= 500:
        return "ERRO_SERVIDOR"
    if status >= 400:
        return "ERRO_CLIENTE"
    return ""


def classify_error(error: BaseException) -> str:
    if isinstance(error, httpx.TimeoutException):
        return "TIMEOUT"
    if isinstance(error, (httpx.ConnectError, httpx.RemoteProtocolError, httpx.NetworkError)):
        return "CONEXAO"
    return type(error).__name__


def format_line(method: str, url: str, outcome: str, elapsed_ms: float, concurrent: int) -> str:
    """Uma linha do log, só com o caminho (sem host, query nem fragmento)."""
    path = urlsplit(url).path or "/"
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    return f"[xano] {now} {method} {path} -> {outcome} em {elapsed_ms:.0f} ms (simultâneas: {concurrent})"


def write(line: str) -> None:
    print(line, file=sys.stderr, flush=True)
