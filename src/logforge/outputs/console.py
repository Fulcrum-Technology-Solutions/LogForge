"""Console output handler."""

from __future__ import annotations

import json
import sys
from typing import IO, Any

from logforge.outputs.base import BaseOutput, Metadata, RetryPolicy


class ConsoleOutput(BaseOutput):
    """Writes events to stdout/stderr, optionally as JSON."""

    def __init__(
        self,
        name: str,
        *,
        stream: IO[str] | None = None,
        format: str = "plain",
        retry_policy: RetryPolicy,
        buffer_size: int,
    ) -> None:
        super().__init__(name, retry_policy=retry_policy, buffer_size=buffer_size, output_type="console")
        self.stream = stream or sys.stdout
        self.format = format

    def _send(self, event: str, metadata: Metadata = None) -> None:
        if self.format == "json":
            payload: dict[str, Any] = {"event": event}
            if metadata:
                payload["metadata"] = dict(metadata)
            line = json.dumps(payload, ensure_ascii=False)
        else:
            line = event
        self.stream.write(line.rstrip("\n") + "\n")
        self.stream.flush()


__all__ = ["ConsoleOutput"]
