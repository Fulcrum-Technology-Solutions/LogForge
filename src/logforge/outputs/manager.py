from __future__ import annotations

from typing import Dict, Iterable, List

from logforge.core.config import LogForgeConfig
from logforge.outputs.base import OutputHandler
from logforge.outputs.console import ConsoleOutputHandler
from logforge.outputs.file import FileOutputHandler
from logforge.outputs.http import HTTPOutputHandler


class OutputManager:
    def __init__(self, config: LogForgeConfig) -> None:
        self.config = config
        self._definitions = {definition["name"]: definition for definition in config.outputs.definitions}

    def create_handlers(self, generator_name: str, outputs: Iterable[str]) -> List[OutputHandler]:
        handlers: List[OutputHandler] = []
        for output_name in outputs:
            definition = self._definitions.get(output_name)
            if not definition:
                continue
            handler = self._create_handler_from_definition(generator_name, definition)
            if handler:
                handlers.append(handler)
        return handlers

    def _create_handler_from_definition(self, generator_name: str, definition: Dict) -> OutputHandler | None:
        output_type = definition.get("type")
        if output_type == "console":
            return ConsoleOutputHandler(format=definition.get("format", "text"))
        if output_type == "file":
            path = definition.get("path")
            if not path:
                return None
            max_bytes = definition.get("rotation", {}).get("max_bytes")
            return FileOutputHandler(path_template=path, generator_name=generator_name, max_bytes=max_bytes)
        if output_type == "http":
            url = definition.get("url")
            if not url:
                return None
            return HTTPOutputHandler(
                url=url,
                method=definition.get("method", "POST"),
                headers=definition.get("headers"),
                timeout=definition.get("timeout", 5.0),
                batch=definition.get("batch", False),
            )
        return None
