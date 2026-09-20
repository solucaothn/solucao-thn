from __future__ import annotations

import os
import logging
from typing import Any, Literal

import httpx
from dotenv import load_dotenv


load_dotenv(override=True)

logger = logging.getLogger(__name__)


class XanoApiError(Exception):
    """An error returned by the Xano API or raised while contacting it."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class XanoClient:
    def __init__(
        self,
        *,
        auth_base_url: str | None = None,
        catalog_base_url: str | None = None,
    ) -> None:
        self.auth_base_url = (
            auth_base_url or os.getenv("XANO_AUTH_BASE_URL", "")
        ).rstrip("/")
        self.catalog_base_url = (
            catalog_base_url or os.getenv("XANO_CATALOG_BASE_URL", "")
        ).rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        *,
        group: Literal["auth", "catalog"],
        token: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        base_url = (
            self.auth_base_url if group == "auth" else self.catalog_base_url
        )
        variable_name = (
            "XANO_AUTH_BASE_URL" if group == "auth" else "XANO_CATALOG_BASE_URL"
        )
        if not base_url:
            raise XanoApiError(
                f"A API do Xano não está configurada. Defina {variable_name}."
            )

        headers = {"Authorization": f"Bearer {token}"} if token else {}
        final_url = f"{base_url}/{path.lstrip('/')}"
        logged_headers = {
            key: ("<redacted>" if key.lower() == "authorization" else value)
            for key, value in headers.items()
        }
        logger.info(
            "Xano request: method=%s group=%s url=%s headers=%s",
            method,
            group,
            final_url,
            logged_headers,
        )
        try:
            response = httpx.request(
                method,
                final_url,
                json=payload,
                headers=headers,
                timeout=10,
            )
        except httpx.HTTPError as exc:
            logger.error(
                "Xano request transport failed: method=%s group=%s url=%s "
                "headers=%s error=%s",
                method,
                group,
                final_url,
                logged_headers,
                exc,
            )
            raise XanoApiError("Não foi possível conectar à API.") from exc

        if response.is_error:
            logger.error(
                "Xano request failed: method=%s group=%s url=%s headers=%s "
                "status=%s body=%s",
                method,
                group,
                final_url,
                logged_headers,
                response.status_code,
                response.text,
            )
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
            group="auth",
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
            group="auth",
            payload={"email": email, "password": password},
        )

    def profile(self, token: str) -> dict[str, Any]:
        return self._request("GET", "/auth/profile", group="auth", token=token)

    def update_profile(
        self, *, token: str, name: str, city: str, state: str
    ) -> dict[str, Any]:
        return self._request(
            "PATCH",
            "/auth/profile",
            group="auth",
            token=token,
            payload={"name": name, "city": city, "state": state},
        )

    def categories(self) -> list[dict[str, Any]]:
        result = self._request("GET", "/catalog/categories", group="catalog")
        return result if isinstance(result, list) else result.get("items", [])

    def donations(self) -> list[dict[str, Any]]:
        result = self._request("GET", "/catalog/donations", group="catalog")
        return result if isinstance(result, list) else result.get("items", [])

    def create_donation(
        self, *, token: str, category_id: int, title: str, description: str
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/catalog/donations",
            group="catalog",
            token=token,
            payload={
                "category_id": category_id,
                "title": title,
                "description": description,
            },
        )

    def update_donation(
        self,
        *,
        token: str,
        donation_id: int,
        category_id: int,
        title: str,
        description: str,
    ) -> dict[str, Any]:
        return self._request(
            "PATCH",
            "/catalog/donations",
            group="catalog",
            token=token,
            payload={
                "donation_id": donation_id,
                "category_id": category_id,
                "title": title,
                "description": description,
            },
        )

    def delete_donation(self, *, token: str, donation_id: int) -> dict[str, Any]:
        return self._request(
            "DELETE",
            "/catalog/donations",
            group="catalog",
            token=token,
            payload={"donation_id": donation_id},
        )

    def update_donation_status(
        self, *, token: str, donation_id: int, status: str
    ) -> dict[str, Any]:
        return self._request(
            "PATCH",
            "/catalog/donations/status",
            group="catalog",
            token=token,
            payload={"donation_id": donation_id, "status": status},
        )
