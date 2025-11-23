"""Client for LogForge community template services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests


@dataclass
class CommunityClientConfig:
    base_url: str = "https://api.logforge.io/v1"
    api_key: Optional[str] = None
    timeout: float = 15.0


class CommunityClientError(Exception):
    """Raised when the community API returns an error."""


@dataclass
class CommunityClient:
    config: CommunityClientConfig
    _session: requests.Session = field(default_factory=requests.Session)

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        response = self._session.request(
            method,
            url,
            headers={**self._headers(), **kwargs.pop("headers", {})},
            timeout=self.config.timeout,
            **kwargs,
        )
        if response.status_code >= 400:
            raise CommunityClientError(
                f"Community API error {response.status_code}: {response.text}"
            )
        if response.status_code == 204:
            return None
        return response.json()

    def search_templates(self, query: str, *, limit: int = 20) -> List[Dict[str, Any]]:
        payload = {"query": query, "limit": limit}
        result = self._request("GET", "templates/search", params=payload)
        return result.get("results", [])

    def get_template_details(self, template_id: str) -> Dict[str, Any]:
        return self._request("GET", f"templates/{template_id}")

    def download_template(self, template_id: str) -> bytes:
        url = f"templates/{template_id}/download"
        response = self._session.get(
            f"{self.config.base_url.rstrip('/')}/{url}",
            headers=self._headers(),
            timeout=self.config.timeout,
        )
        if response.status_code >= 400:
            raise CommunityClientError(
                f"Failed to download template '{template_id}': {response.text}"
            )
        return response.content


__all__ = ["CommunityClient", "CommunityClientConfig", "CommunityClientError"]
