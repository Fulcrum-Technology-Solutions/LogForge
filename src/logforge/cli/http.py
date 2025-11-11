"""Thin HTTP client wrapper for CLI commands."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class APIClient:
    """Simple wrapper around httpx for LogForge CLI."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers: Dict[str, str] = kwargs.pop("headers", {}) or {}
        if self.api_key:
            headers.setdefault("Authorization", f"Bearer {self.api_key}")
        return self._client.request(method, path, headers=headers, **kwargs)

    def json_request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        response = self.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
