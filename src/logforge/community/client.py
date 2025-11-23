from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

LOGGER = logging.getLogger(__name__)


class CommunityClient:
    def __init__(self, base_url: str, session: Optional[requests.Session] = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = session or requests.Session()

    def search_templates(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"q": query} if query else {}
        try:
            response = self._session.get(f"{self._base_url}/community-templates", params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            return payload.get("templates", [])
        except requests.RequestException as exc:  # pragma: no cover - network failure path
            LOGGER.warning("Community template search failed: %s", exc)
            return []

    def get_template_info(self, template_id: str) -> Dict[str, Any]:
        try:
            response = self._session.get(f"{self._base_url}/templates/{template_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:  # pragma: no cover
            LOGGER.warning("Community template info lookup failed for %s: %s", template_id, exc)
            raise

    def download_template(self, template_id: str, url: Optional[str] = None) -> bytes:
        download_url = url or f"{self._base_url}/templates/{template_id}/download"
        response = self._session.get(download_url, timeout=30)
        response.raise_for_status()
        return response.content

