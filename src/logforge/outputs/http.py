"""HTTP output handler."""

from __future__ import annotations

import os
import re
import threading
import time
from collections import deque
from typing import Any, Mapping, Optional

import requests

from logforge.outputs.base import BaseOutput, Metadata, RetryPolicy

ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


class HttpOutput(BaseOutput):
    """Sends events to an HTTP endpoint with optional batching."""

    def __init__(
        self,
        name: str,
        *,
        url: str,
        method: str = "POST",
        headers: Optional[Mapping[str, str]] = None,
        retry_policy: RetryPolicy,
        buffer_size: int,
        batch_size: Optional[int] = None,
        batch_interval: Optional[int] = None,
        timeout: int = 30,
        session: Optional[requests.Session] = None,
    ) -> None:
        super().__init__(name, retry_policy=retry_policy, buffer_size=buffer_size, output_type="http")
        self.url = url
        self.method = method.upper()
        self.headers = self._resolve_headers(headers or {})
        self.session = session or requests.Session()
        self.timeout = timeout
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self._batch: deque[tuple[str, Optional[Metadata]]] = deque()
        self._batch_lock = threading.Lock()
        self._last_batch_send = time.monotonic()
        self._batch_timer: Optional[threading.Timer] = None

    def _resolve_headers(self, headers: Mapping[str, str]) -> dict[str, str]:
        """Resolve environment variables in header values."""
        resolved = {}
        for key, value in headers.items():
            resolved[key] = self._substitute_env_vars(value)
        return resolved

    def _substitute_env_vars(self, template: str) -> str:
        """Substitute ${VAR_NAME} with environment variable values."""
        def _repl(match: re.Match[str]) -> str:
            key = match.group(1)
            return os.environ.get(key, match.group(0))  # Keep original if not found
        return ENV_VAR_PATTERN.sub(_repl, template)

    def emit(self, event: str, metadata: Optional[Metadata] = None) -> None:
        """Emit an event, batching if configured."""
        if self.batch_size is None and self.batch_interval is None:
            # No batching - send immediately
            super().emit(event, metadata)
            return

        with self._batch_lock:
            self._batch.append((event, metadata))
            should_send = False

            if self.batch_size and len(self._batch) >= self.batch_size:
                should_send = True
            elif self.batch_interval:
                elapsed = time.monotonic() - self._last_batch_send
                if elapsed >= self.batch_interval:
                    should_send = True
                elif self._batch_timer is None:
                    # Start timer for next batch
                    remaining = self.batch_interval - elapsed
                    self._batch_timer = threading.Timer(remaining, self._flush_batch)
                    self._batch_timer.start()

            if should_send:
                self._flush_batch()

    def _flush_batch(self) -> None:
        """Send all batched events."""
        with self._batch_lock:
            if not self._batch:
                return

            events_to_send = list(self._batch)
            self._batch.clear()
            self._last_batch_send = time.monotonic()

            if self._batch_timer:
                self._batch_timer.cancel()
                self._batch_timer = None

        # Send batch outside lock
        if len(events_to_send) == 1:
            # Single event - send as object
            event, metadata = events_to_send[0]
            payload: dict[str, Any] = {"event": event}
            if metadata:
                payload["metadata"] = dict(metadata)
        else:
            # Multiple events - send as array
            payload = []
            for event, metadata in events_to_send:
                item: dict[str, Any] = {"event": event}
                if metadata:
                    item["metadata"] = dict(metadata)
                payload.append(item)

        self._send_batch(payload)

    def _send_batch(self, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
        """Send a batch payload with retry logic."""
        attempt = 0
        while True:
            try:
                resp = self.session.request(
                    self.method,
                    self.url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                return
            except Exception as exc:
                attempt += 1
                if self.retry_policy.max_attempts > 0 and attempt >= self.retry_policy.max_attempts:
                    raise
                if attempt > 1:
                    backoff = min(
                        self.retry_policy.retry_interval * (self.retry_policy.backoff_multiplier ** (attempt - 2)),
                        self.retry_policy.max_backoff,
                    )
                    time.sleep(backoff)

    def _send(self, event: str, metadata: Metadata = None) -> None:
        """Send a single event (used when batching is disabled)."""
        payload: dict[str, Any] = {"event": event}
        if metadata:
            payload["metadata"] = dict(metadata)
        resp = self.session.request(
            self.method,
            self.url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()


__all__ = ["HttpOutput"]
