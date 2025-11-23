"""Output handler base classes."""
from __future__ import annotations

import abc
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Mapping, Optional, Tuple

from logforge.utils.metrics import (
    output_buffered_events,
    output_errors_total,
    output_events_sent_total,
    output_latency_seconds,
)

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
        output_type: str = "unknown",
    ) -> None:
        self.name = name
        self.retry_policy = retry_policy
        self.buffer_size = max(0, buffer_size)
        self.output_type = output_type
        self._buffer: Deque[BufferedEvent] = deque(maxlen=self.buffer_size or None)

    def emit(self, event: str, metadata: Metadata = None) -> None:
        """Buffer the event and attempt to deliver all pending events."""
        self._enqueue(event, metadata)
        self._update_buffer_metrics()
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
                with output_latency_seconds.labels(
                    output=self.name, output_type=self.output_type
                ).time():
                    self._send(event, metadata)
                output_events_sent_total.labels(output=self.name, output_type=self.output_type).inc()
                self._update_buffer_metrics()
                return
            except Exception as exc:
                attempts += 1
                error_type = type(exc).__name__
                output_errors_total.labels(
                    output=self.name, output_type=self.output_type, error_type=error_type
                ).inc()
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

    def _update_buffer_metrics(self) -> None:
        """Update buffered events gauge."""
        output_buffered_events.labels(output=self.name).set(len(self._buffer))

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
            output_type="capture",
        )
        self.events: list[str] = []

    def _send(self, event: str, metadata: Metadata = None) -> None:
        self.events.append(event)


__all__ = ["BaseOutput", "CapturingOutput", "Metadata", "RetryPolicy", "OutputError"]
