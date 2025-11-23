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


@app.command("test")
def test_output(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Test output connectivity and configuration."""
    # TODO: Implement output test API endpoint
    typer.secho("Output test functionality requires API support", fg=typer.colors.YELLOW)
    typer.echo(f"Testing output '{name}' (not yet implemented)")


@app.command("add")
def add_output(ctx: typer.Context) -> None:
    """Interactively create a new output."""
    # TODO: Implement interactive output creation
    typer.secho("Interactive output creation not yet implemented", fg=typer.colors.YELLOW)
    typer.echo("Configure outputs in config.yaml and reload the service")


@app.command("enable")
def enable_output(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Enable an output."""
    # TODO: Implement enable/disable API endpoint
    typer.secho("Enable/disable functionality requires API support", fg=typer.colors.YELLOW)
    typer.echo(f"Output '{name}' enable requested (not yet implemented)")


@app.command("disable")
def disable_output(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Disable an output."""
    # TODO: Implement enable/disable API endpoint
    typer.secho("Enable/disable functionality requires API support", fg=typer.colors.YELLOW)
    typer.echo(f"Output '{name}' disable requested (not yet implemented)")


@app.command("metrics")
def output_metrics(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Show detailed metrics for an output."""
    output = _client(ctx).get(f"/api/outputs/{name}")
    if _output_json(ctx):
        typer.echo(json.dumps(output, indent=2))
        return

    stats = output.get("statistics", {})
    typer.secho(f"Metrics for {output['name']}", bold=True)
    typer.echo(f"\nEvents:")
    typer.echo(f"  Sent: {stats.get('events_sent', 0)}")
    typer.echo(f"  Errors: {stats.get('errors', 0)}")
    typer.echo(f"  Buffered: {stats.get('buffered_events', 0)}")
    if stats.get("last_error"):
        typer.echo(f"  Last Error: {stats['last_error']}")
    typer.echo(f"\nConfiguration:")
    config = output.get("configuration", {})
    for key, value in config.items():
        typer.echo(f"  {key}: {value}")
