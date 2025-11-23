"""Output handler base classes."""
from __future__ import annotations

import abc
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Mapping, Optional, Tuple

Metadata = Mapping[str, Any] | None
BufferedEvent = Tuple[str, Metadata]


@dataclass
class RetryPolicy:
    max_attempts: int
    retry_interval: float
    backoff_multiplier: float
    max_backoff: float

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "RetryPolicy":
        return cls(
            max_attempts=config.get("max_attempts", -1),
            retry_interval=float(config.get("retry_interval", 1)),
            backoff_multiplier=float(config.get("backoff_multiplier", 2.0)),
            max_backoff=float(config.get("max_backoff", 60)),
        )


class OutputError(Exception):
    """Raised when an output cannot deliver an event."""


class BaseOutput(abc.ABC):
    """Abstract base class for all output handlers."""

    def __init__(
        self,
        name: str,
        *,
        retry_policy: RetryPolicy,
        buffer_size: int,
    ) -> None:
        self.name = name
        self.retry_policy = retry_policy
        self.buffer_size = max(0, buffer_size)
        self._buffer: Deque[BufferedEvent] = deque(maxlen=self.buffer_size or None)

    def emit(self, event: str, metadata: Metadata = None) -> None:
        """Buffer the event and attempt to deliver all pending events."""

        self._enqueue(event, metadata)
        self._flush()

    def _enqueue(self, event: str, metadata: Metadata) -> None:
        if self.buffer_size == 0:
            self._buffer.clear()
            self._buffer.append((event, metadata))
        else:
            self._buffer.append((event, metadata))

    def _flush(self) -> None:
        while self._buffer:
            next_event, next_meta = self._buffer[0]
            self._deliver_with_retry(next_event, next_meta)
            self._buffer.popleft()

    def _deliver_with_retry(self, event: str, metadata: Metadata) -> None:
        attempts = 0
        delay = self.retry_policy.retry_interval
        while True:
            try:
                self._send(event, metadata)
                return
            except Exception as exc:
                attempts += 1
                if (
                    self.retry_policy.max_attempts != -1
                    and attempts >= self.retry_policy.max_attempts
                ):
                    raise OutputError(
                        f"Output '{self.name}' failed after {attempts} attempts."
                    ) from exc
                time.sleep(delay)
                delay = min(
                    delay * self.retry_policy.backoff_multiplier,
                    self.retry_policy.max_backoff,
                )

    @abc.abstractmethod
    def _send(self, event: str, metadata: Metadata = None) -> None:
        """Send the rendered event to the destination."""


class CapturingOutput(BaseOutput):
    """Simple in-memory output used for testing."""

    def __init__(
        self,
        name: str = "capture",
        *,
        retry_policy: Optional[RetryPolicy] = None,
        buffer_size: int = 100,
    ) -> None:
        super().__init__(
            name,
            retry_policy=retry_policy or RetryPolicy(-1, 0, 1, 0),
            buffer_size=buffer_size,
        )
        self.events: list[str] = []

    def _send(self, event: str, metadata: Metadata = None) -> None:
        self.events.append(event)


__all__ = ["BaseOutput", "CapturingOutput", "Metadata", "RetryPolicy", "OutputError"]
