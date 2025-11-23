"""File output handler."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from logforge.core.config_schema import LoggingRotationConfig
from logforge.outputs.base import BaseOutput, Metadata, RetryPolicy
from logforge.utils.logging import _build_handler as build_logging_handler


class FileOutput(BaseOutput):
    """Appends events to files with optional rotation and templating."""

    def __init__(
        self,
        name: str,
        *,
        path_template: str,
        generator_name: str,
        rotation: Optional[LoggingRotationConfig],
        retry_policy: RetryPolicy,
        buffer_size: int,
    ) -> None:
        super().__init__(name, retry_policy=retry_policy, buffer_size=buffer_size, output_type="file")
        self.path_template = path_template
        self.generator_name = generator_name
        self.rotation = rotation
        self._logger = logging.getLogger(f"logforge.output.file.{generator_name}.{name}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        self._handler: Optional[logging.Handler] = None
        self._current_path: Optional[Path] = None
        self._formatter = logging.Formatter("%(message)s")

    def _resolve_path(self) -> Path:
        now = datetime.now(timezone.utc)
        replacements = {
            "generator": self.generator_name,
            "date": now.strftime("%Y-%m-%d"),
            "timestamp": now.strftime("%Y%m%d%H%M%S"),
        }
        formatted = self.path_template.format(**replacements)
        path = Path(formatted).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _ensure_handler(self, path: Path) -> None:
        if self._handler and path == self._current_path:
            return
        if self._handler:
            self._logger.removeHandler(self._handler)
            self._handler.close()
        handler = build_logging_handler(path, self.rotation)
        handler.setFormatter(self._formatter)
        self._logger.handlers.clear()
        self._logger.addHandler(handler)
        self._handler = handler
        self._current_path = path

    def _send(self, event: str, metadata: Metadata = None) -> None:
        target_path = self._resolve_path()
        self._ensure_handler(target_path)
        self._logger.info(event)


__all__ = ["FileOutput"]
