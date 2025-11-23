from __future__ import annotations

from typing import Optional

import requests
import typer

from .common import CLIConfig, ensure_api_ready, render_output, build_headers

app = typer.Typer(help="Manage LogForge generators via the management API.")


def _get_cli_config(ctx: typer.Context):
    config = ctx.find_object(CLIConfig)
    if config is None:
        raise typer.BadParameter("CLI configuration unavailable.")
    return config


def _api_request(ctx: typer.Context, method: str, path: str) -> dict:
    config = _get_cli_config(ctx)
    ensure_api_ready(config)
    headers = build_headers(config)
    url = f"{config.api_url}{path}"

    try:
        response = requests.request(method, url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.HTTPError as exc:
        typer.secho(f"API request failed ({exc.response.status_code}): {exc.response.text}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except requests.RequestException as exc:
        typer.secho(f"Failed to contact management API: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    return response.json()


@app.command("list")
def list_generators(ctx: typer.Context) -> None:
    """
    Display generator status from the management API.
    """

    data = _api_request(ctx, "GET", "/api/generators")
    config = _get_cli_config(ctx)
    render_output(config, data)


@app.command("start")
def start_generator(ctx: typer.Context, name: str) -> None:
    """
    Start a generator by name.
    """

    data = _api_request(ctx, "POST", f"/api/generators/{name}/start")
    config = _get_cli_config(ctx)
    render_output(config, data)


@app.command("stop")
def stop_generator(ctx: typer.Context, name: str) -> None:
    """
    Stop a generator by name.
    """

    data = _api_request(ctx, "POST", f"/api/generators/{name}/stop")
    config = _get_cli_config(ctx)
    render_output(config, data)

