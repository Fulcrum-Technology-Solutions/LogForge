"""Output handler CLI commands."""

from __future__ import annotations

import json
from typing import Any, Dict

import typer

from logforge.cli.api_client import APIClient

app = typer.Typer(help="Manage output handlers.")


def _client(ctx: typer.Context) -> APIClient:
    if ctx.obj is None:
        raise typer.BadParameter("CLI context missing; run through `logforge` entrypoint.")
    return ctx.obj.client()


def _output_json(ctx: typer.Context) -> bool:
    return bool(getattr(ctx.obj, "output_format", "table") == "json")


def _print_output(ctx: typer.Context, output: Dict[str, Any]) -> None:
    if _output_json(ctx):
        typer.echo(json.dumps(output, indent=2))
        return
    typer.secho(f"{output['name']} [{output['status']}]", bold=True)
    typer.echo(f"Type      : {output['type']}")
    config = output.get("configuration", {})
    if config:
        typer.echo(f"Config    : {json.dumps(config)}")
    stats = output.get("statistics", {})
    typer.echo(
        f"Events: {stats.get('events_sent',0)}  Errors: {stats.get('errors',0)}  "
        f"Buffered: {stats.get('buffered_events',0)}"
    )
    if stats.get("last_error"):
        typer.echo(f"Last Error: {stats['last_error']}")


@app.command("list")
def list_outputs(ctx: typer.Context) -> None:
    """List outputs with health and stats."""
    response = _client(ctx).get("/api/outputs")
    outputs = response.get("outputs", [])
    if _output_json(ctx):
        typer.echo(json.dumps(outputs, indent=2))
        return
    if not outputs:
        typer.echo("No outputs defined.")
        return
    for output in outputs:
        typer.echo(f"{output['name']:20} {output['type']:10} {output['status']:>8}")


@app.command("show")
def show_output(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Show output configuration and stats."""
    data = _client(ctx).get(f"/api/outputs/{name}")
    _print_output(ctx, data)
