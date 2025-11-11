from __future__ import annotations

import json
import os
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple

import click
import httpx

DEFAULT_API_URL = "http://127.0.0.1:8080"


class APIClientError(RuntimeError):
    pass


def _normalize_base_url(url: Optional[str]) -> str:
    if not url:
        return DEFAULT_API_URL
    return url.rstrip("/")


class APIClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: float = 5.0) -> None:
        self.base_url = _normalize_base_url(base_url or os.environ.get("LOGFORGE_API_URL"))
        self.api_key = api_key or os.environ.get("LOGFORGE_API_KEY")
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def request(self, method: str, path: str, *, params: Optional[Mapping[str, Any]] = None, json_body: Any = None) -> Any:
        url = f"{self.base_url}{path}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            response = self._client.request(method, url, params=params, json=json_body, headers=headers)
        except httpx.RequestError as exc:
            raise APIClientError(f"Failed to reach API: {exc}") from exc

        if response.status_code >= 400:
            message = response.text
            try:
                payload = response.json()
                message = payload.get("detail") or payload.get("error") or message
            except ValueError:
                pass
            raise APIClientError(f"API error {response.status_code}: {message}")

        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def get(self, path: str, *, params: Optional[Mapping[str, Any]] = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, *, json_body: Any = None) -> Any:
        return self.request("POST", path, json_body=json_body)


def format_table(rows: Sequence[Mapping[str, Any]], columns: Sequence[Tuple[str, str]]) -> str:
    if not rows:
        return "No data."
    headers = [header for _, header in columns]
    matrix: List[List[str]] = []
    for row in rows:
        matrix.append([str(row.get(key, "")) for key, _ in columns])

    widths = [len(header) for header in headers]
    for row in matrix:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def render_line(values: Iterable[str]) -> str:
        parts = []
        for value, width in zip(values, widths):
            parts.append(value.ljust(width))
        return "  ".join(parts)

    lines = [render_line(headers), render_line(["-" * width for width in widths])]
    for row in matrix:
        lines.append(render_line(row))
    return "\n".join(lines)


def render_output(data: Any, output: str, *, columns: Optional[Sequence[Tuple[str, str]]] = None) -> str:
    output = output.lower()
    if output == "json":
        return json.dumps(data, indent=2)
    if columns and isinstance(data, Sequence):
        return format_table(data, columns)
    return str(data)


def echo_api_error(error: APIClientError) -> None:
    click.secho(str(error), fg="red")
