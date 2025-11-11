from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from logforge.outputs.base import OutputHandler


class FileOutputHandler(OutputHandler):
    def __init__(self, *, path_template: str, generator_name: str, max_bytes: Optional[int] = None) -> None:
        self.path_template = path_template
        self.generator_name = generator_name
        self.max_bytes = max_bytes
        self._path = self._resolve_path()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self) -> Path:
        formatted = self.path_template.format(generator=self.generator_name)
        return Path(formatted).expanduser()

    def write(self, event: str) -> None:
        data = event + "\n"
        file_path = self._resolve_path()
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(data)
        if self.max_bytes is not None and file_path.stat().st_size > self.max_bytes:
            self._rotate(file_path)

    def _rotate(self, file_path: Path) -> None:
        rotated = file_path.with_suffix(file_path.suffix + ".1")
        if rotated.exists():
            rotated.unlink()
        os.replace(file_path, rotated)
