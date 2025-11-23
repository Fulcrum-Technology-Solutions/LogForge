"""Output handler CLI commands."""

from __future__ import annotations

import typer

from logforge.cli.helpers import not_implemented

app = typer.Typer(help="Manage output handlers.")


@app.command("list")
def list_outputs() -> None:
    """List outputs (placeholder)."""
    not_implemented("outputs list")


@app.command("test")
def test_output(name: str) -> None:
    """Test output connectivity (placeholder)."""
    not_implemented(f"outputs test {name}")
