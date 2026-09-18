from __future__ import annotations

import os
from typing import Any

import httpx


class XanoApiError(Exception):
    """An error returned by the Xano API or raised while contacting it."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class XanoClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("XANO_API_BASE_URL", "")).rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        if not self.base_url:
            raise XanoApiError(
                "A API do Xano não está configurada. Defina XANO_API_BASE_URL."
            )

        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            response = httpx.request(
                method,
                f"{self.base_url}/{path.lstrip('/')}",
                json=payload,
                headers=headers,
                timeout=10,
            )
        except httpx.HTTPError as exc:
            raise XanoApiError("Não foi possível conectar à API.") from exc

        if response.is_error:
            try:
                error = response.json()
            except ValueError:
                error = {}
            message = (
                error.get("message")
                or error.get("error")
                or "A API rejeitou a operação."
            )
            raise XanoApiError(str(message), response.status_code)

        if not response.content:
            return None
        return response.json()

    def signup(
        self, *, name: str, email: str, password: str, city: str, state: str
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/signup",
            payload={
                "name": name,
                "email": email,
                "password": password,
                "city": city,
                "state": state,
            },
        )

    def login(self, *, email: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/login",
            payload={"email": email, "password": password},
        )

    def profile(self, token: str) -> dict[str, Any]:
        return self._request("GET", "/auth/profile", token=token)

    def update_profile(
        self, *, token: str, name: str, city: str, state: str
    ) -> dict[str, Any]:
        return self._request(
            "PATCH",
            "/auth/profile",
            token=token,
            payload={"name": name, "city": city, "state": state},
        )
