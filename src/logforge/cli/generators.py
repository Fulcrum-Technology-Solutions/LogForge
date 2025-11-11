from __future__ import annotations

from typing import Optional

import click

from logforge.cli.utils import APIClient, APIClientError, echo_api_error, render_output


@click.group(help="Inspect and control generators.")
@click.pass_context
def generators(ctx: click.Context) -> None:
    """Generator management commands."""
    ctx.ensure_object(dict)


@generators.command("list", help="List generators and their current status.")
@click.option("--output", type=click.Choice(["table", "json"], case_sensitive=False), default="table")
@click.pass_context
def list_generators(ctx: click.Context, output: str) -> None:
    """Display generator status in a table or JSON."""
    client: APIClient = ctx.obj["api_client"]
    try:
        payload = client.get("/api/generators")
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    columns = [
        ("name", "NAME"),
        ("state", "STATE"),
        ("template", "TEMPLATE"),
        ("events_generated", "EVENTS"),
        ("errors", "ERRORS"),
    ]
    click.echo(render_output(payload, output, columns=columns if output.lower() == "table" else None))


@generators.command("start", help="Start a generator by name.")
@click.argument("name", type=str)
@click.pass_context
def start_generator(ctx: click.Context, name: str) -> None:
    """Start a generator and print the resulting status."""
    client: APIClient = ctx.obj["api_client"]
    try:
        payload = client.post(f"/api/generators/{name}/start")
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    click.echo(f"Generator {name} started.")
    click.echo(render_output(payload, "json"))


@generators.command("stop", help="Stop a running generator.")
@click.argument("name", type=str)
@click.pass_context
def stop_generator(ctx: click.Context, name: str) -> None:
    """Stop a generator and print the resulting status."""
    client: APIClient = ctx.obj["api_client"]
    try:
        payload = client.post(f"/api/generators/{name}/stop")
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    click.echo(f"Generator {name} stopped.")
    click.echo(render_output(payload, "json"))


@generators.command("restart", help="Restart a generator (stop then start).")
@click.argument("name", type=str)
@click.pass_context
def restart_generator(ctx: click.Context, name: str) -> None:
    """Restart a generator and print the resulting status."""
    client: APIClient = ctx.obj["api_client"]
    try:
        payload = client.post(f"/api/generators/{name}/restart")
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    click.echo(f"Generator {name} restarted.")
    click.echo(render_output(payload, "json"))
