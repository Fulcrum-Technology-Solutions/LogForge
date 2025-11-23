"""Generator CLI commands."""

from __future__ import annotations

import typer

from logforge.cli.helpers import not_implemented

app = typer.Typer(help="Control event generators.")


@app.command("list")
def list_generators() -> None:
    """List generators (placeholder)."""
    not_implemented("generators list")


@app.command("start")
def start_generator(name: str) -> None:
    """Start generator (placeholder)."""
    not_implemented(f"generators start {name}")


@app.command("stop")
def stop_generator(name: str) -> None:
    """Stop generator (placeholder)."""
    not_implemented(f"generators stop {name}")
