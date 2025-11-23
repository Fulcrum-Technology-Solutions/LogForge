"""File output handler."""

from __future__ import annotations

from pathlib import Path

from logforge.outputs.base import BaseOutput, Metadata


class FileOutput(BaseOutput):
    """Appends events to a log file, creating directories as needed."""

    def __init__(self, name: str, path: Path) -> None:
        super().__init__(name)
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: str, metadata: Metadata = None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(event.rstrip("\n") + "\n")


__all__ = ["FileOutput"]
