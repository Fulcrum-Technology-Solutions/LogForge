from __future__ import annotations

import json
import sys
from typing import IO, Optional

from logforge.outputs.base import OutputHandler


class ConsoleOutputHandler(OutputHandler):
    def __init__(self, *, stream: Optional[IO[str]] = None, format: str = "text") -> None:
        self.stream = stream or sys.stdout
        self.format = format

    def write(self, event: str) -> None:
        if self.format == "json":
            try:
                parsed = json.loads(event)
                output = json.dumps(parsed)
            except json.JSONDecodeError:
                output = event
        else:
            output = event
        self.stream.write(output + "\n")
        self.stream.flush()
