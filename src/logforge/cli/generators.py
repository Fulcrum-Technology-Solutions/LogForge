"""Generator CLI commands."""

from __future__ import annotations

import json
from typing import Any, Dict

import typer

from logforge.cli.api_client import APIClient

app = typer.Typer(help="Control event generators.")


def _client(ctx: typer.Context) -> APIClient:
    if ctx.obj is None:
        raise typer.BadParameter("CLI context missing; run through `logforge` entrypoint.")
    return ctx.obj.client()


def _output_json(ctx: typer.Context) -> bool:
    return bool(getattr(ctx.obj, "output_format", "table") == "json")


def _print_status(ctx: typer.Context, status: Dict[str, Any]) -> None:
    if _output_json(ctx):
        typer.echo(json.dumps(status, indent=2))
        return
    typer.secho(f"{status['name']} [{status['state']}]", bold=True)
    typer.echo(f"Template : {status['template']}")
    typer.echo(f"Outputs  : {', '.join(status['outputs'])}")
    stats = status.get("statistics", {})
    typer.echo(
        f"Events: {stats.get('events_generated', 0)}  Errors: {stats.get('errors', 0)}  "
        f"Uptime: {round(stats.get('uptime', 0.0), 2)}s"
    )


@app.command("list")
def list_generators(ctx: typer.Context) -> None:
    """List all generators and their states."""
    response = _client(ctx).get("/api/generators")
    if _output_json(ctx):
        typer.echo(json.dumps(response, indent=2))
        return
    if not response:
        typer.echo("No generators found.")
        return
    for generator in response:
        typer.echo(f"{generator['name']:20} {generator['state']:>8}  {generator['template']}")


@app.command("status")
def generator_status(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Show detailed status for a generator."""
    status = _client(ctx).get(f"/api/generators/{name}")
    _print_status(ctx, status)


@app.command("start")
def start_generator(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Start a generator."""
    status = _client(ctx).post(f"/api/generators/{name}/start", {})
    _print_status(ctx, status)


@app.command("stop")
def stop_generator(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Stop a running generator."""
    status = _client(ctx).post(f"/api/generators/{name}/stop", {})
    _print_status(ctx, status)


@app.command("restart")
def restart_generator(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Restart a generator."""
    status = _client(ctx).post(f"/api/generators/{name}/restart", {})
    _print_status(ctx, status)
