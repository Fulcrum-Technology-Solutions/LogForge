"""Output factory utilities."""

from __future__ import annotations

from pathlib import Path

from logforge.core.config_schema import OutputDefinition
from logforge.outputs.base import BaseOutput
from logforge.outputs.console import ConsoleOutput
from logforge.outputs.file import FileOutput


def build_output(definition: OutputDefinition, *, generator_name: str) -> BaseOutput:
    """Instantiate an output handler from a configuration definition."""

    output_type = definition.type
    if output_type == "file":
        if not definition.path:
            raise ValueError("File outputs require a 'path'.")
        resolved_path = Path(definition.path.format(generator=generator_name))
        return FileOutput(definition.name, resolved_path)
    if output_type == "console":
        return ConsoleOutput(definition.name, format=definition.format or "plain")
    raise ValueError(f"Unsupported output type '{output_type}'.")


__all__ = ["build_output", "BaseOutput", "ConsoleOutput", "FileOutput"]
