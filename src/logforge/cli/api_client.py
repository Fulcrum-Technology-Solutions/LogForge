"""Simple HTTP client for interacting with the LogForge API."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class APIClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.api_key = api_key

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get(self, path: str) -> Any:
        resp = self.session.get(f"{self.base_url}{path}", headers=self._headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, payload: dict) -> Any:
        resp = self.session.post(
            f"{self.base_url}{path}",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


__all__ = ["APIClient"]
