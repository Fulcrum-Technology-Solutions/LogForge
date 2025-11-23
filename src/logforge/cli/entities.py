"""Entity CLI commands."""

from __future__ import annotations

import typer

from logforge.cli.helpers import not_implemented

app = typer.Typer(help="Inspect and manage entity registry data.")


@app.command("list")
def list_entities(
    entity_type: str = typer.Option(
        "all",
        "--type",
        "-t",
        help="Filter by entity type (users/devices/services).",
    )
) -> None:
    """List entities (placeholder)."""
    not_implemented(f"entities list ({entity_type})")


@app.command("validate")
def validate_entities() -> None:
    """Validate entity registry (placeholder)."""
    not_implemented("entities validate")
