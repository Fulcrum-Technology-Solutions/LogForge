from __future__ import annotations

import os
import re
from typing import Dict, Iterable, Optional

import httpx

from logforge.outputs.base import OutputHandler


class HTTPOutputHandler(OutputHandler):
    """Send events to a remote HTTP endpoint."""

    def __init__(
        self,
        *,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 5.0,
        batch: bool = False,
    ) -> None:
        self.url = url
        self.method = method.upper()
        self.headers = self._resolve_headers(headers or {})
        self.timeout = timeout
        self.batch = batch
        self._client = httpx.Client(timeout=self.timeout)

    def write(self, event: str) -> None:
        response = self._client.request(
            self.method,
            self.url,
            headers=self.headers,
            content=event.encode("utf-8"),
        )
        response.raise_for_status()

    def write_batch(self, events: Iterable[str]) -> None:
        if not self.batch:
            super().write_batch(events)
            return
        payload = "[{}]".format(",".join(events))
        response = self._client.request(
            self.method,
            self.url,
            headers=self.headers,
            content=payload.encode("utf-8"),
        )
        response.raise_for_status()

    def close(self) -> None:
        self._client.close()

    def _resolve_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        resolved: Dict[str, str] = {}
        for key, value in headers.items():
            if not isinstance(value, str):
                resolved[key] = value
                continue
            def _replace(match: re.Match[str]) -> str:
                env_key = match.group(1)
                return os.environ.get(env_key, "")

            resolved[key] = re.sub(r"\$\{([A-Za-z0-9_]+)\}", _replace, value)
        return resolved

