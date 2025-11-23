"""HTTP output handler."""

from __future__ import annotations

from typing import Any, Mapping, Optional

import requests

from logforge.outputs.base import BaseOutput, Metadata, RetryPolicy


class HttpOutput(BaseOutput):
    """Sends events to an HTTP endpoint."""

    def __init__(
        self,
        name: str,
        *,
        url: str,
        method: str = "POST",
        headers: Optional[Mapping[str, str]] = None,
        retry_policy: RetryPolicy,
        buffer_size: int,
        session: Optional[requests.Session] = None,
    ) -> None:
        super().__init__(name, retry_policy=retry_policy, buffer_size=buffer_size)
        self.url = url
        self.method = method.upper()
        self.headers = dict(headers or {})
        self.session = session or requests.Session()

    def _send(self, event: str, metadata: Metadata = None) -> None:
        payload: dict[str, Any] = {"event": event}
        if metadata:
            payload["metadata"] = dict(metadata)
        resp = self.session.request(
            self.method,
            self.url,
            json=payload,
            headers=self.headers,
            timeout=10,
        )
        resp.raise_for_status()


__all__ = ["HttpOutput"]
