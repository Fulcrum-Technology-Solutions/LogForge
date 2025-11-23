"""CLI helper utilities."""

from __future__ import annotations

import typer


def not_implemented(command_name: str) -> None:
    """Emit a friendly placeholder message until the command is implemented."""
    typer.secho(
        f"Command '{command_name}' is not implemented yet. "
        "Follow the roadmap in Tasks.md for progress.",
        fg=typer.colors.YELLOW,
    )
    raise typer.Exit(code=1)
