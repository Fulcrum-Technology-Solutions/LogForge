from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx


class CommunityAPIError(RuntimeError):
    pass


class CommunityAPIClient:
    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def list_templates(self, query: Optional[str] = None, vendor: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if query:
            params["q"] = query
        if vendor:
            params["vendor_id"] = vendor
        with self._client() as client:
            response = client.get("/api/v1/community-templates", params=params)
            self._raise_for_status(response)
            payload = response.json()
            return payload.get("templates", payload)

    def list_vendors(self) -> List[Dict[str, Any]]:
        with self._client() as client:
            response = client.get("/api/v1/vendors")
            self._raise_for_status(response)
            payload = response.json()
            return payload.get("vendors", payload)

    def get_vendor(self, vendor_id: str) -> Dict[str, Any]:
        with self._client() as client:
            response = client.get(f"/api/v1/vendors/{vendor_id}")
            self._raise_for_status(response)
            return response.json()

    def get_template(self, template_id: str) -> Dict[str, Any]:
        with self._client() as client:
            response = client.get(f"/api/v1/templates/{template_id}")
            self._raise_for_status(response)
            return response.json()

    def download_template(self, template_id: str) -> Dict[str, Any]:
        with self._client() as client:
            response = client.get(f"/api/v1/templates/{template_id}/download")
            self._raise_for_status(response)
            return response.json()

    def download_vendor_package(self, vendor_id: str) -> bytes:
        with self._client() as client:
            response = client.get(f"/api/v1/vendors/{vendor_id}/download")
            self._raise_for_status(response)
            return response.content

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code >= 400:
            detail = response.text
            try:
                payload = response.json()
                detail = payload.get("detail") or payload.get("error") or detail
            except ValueError:
                pass
            raise CommunityAPIError(f"Community API error {response.status_code}: {detail}")
