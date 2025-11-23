"""Configuration CLI commands."""

from __future__ import annotations

import typer

from logforge.cli.helpers import not_implemented

app = typer.Typer(help="Manage LogForge configuration settings.")


@app.command("show")
def show_config() -> None:
    """Display current configuration (placeholder)."""
    not_implemented("config show")


@app.command("validate")
def validate_config() -> None:
    """Validate configuration file (placeholder)."""
    not_implemented("config validate")
