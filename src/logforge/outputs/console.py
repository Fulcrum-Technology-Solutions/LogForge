"""Console output handler."""

from __future__ import annotations

import json
import sys
from typing import IO, Any

from logforge.outputs.base import BaseOutput, Metadata


class ConsoleOutput(BaseOutput):
    """Writes events to stdout/stderr, optionally as JSON."""

    def __init__(self, name: str, *, stream: IO[str] | None = None, format: str = "plain") -> None:
        super().__init__(name)
        self.stream = stream or sys.stdout
        self.format = format

    def emit(self, event: str, metadata: Metadata = None) -> None:
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
