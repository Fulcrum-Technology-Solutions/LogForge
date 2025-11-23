from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path
from typing import Optional

import requests
import typer

from .common import CLIConfig, build_headers, ensure_api_ready, render_output

app = typer.Typer(help="Manage LogForge templates via the management API.")


def _get_cli_config(ctx: typer.Context) -> CLIConfig:
    config = ctx.find_object(CLIConfig)
    if config is None:
        raise typer.BadParameter("CLI configuration unavailable.")
    return config


def _api_request(ctx: typer.Context, method: str, path: str, json_body: Optional[dict] = None) -> dict:
    config = _get_cli_config(ctx)
    ensure_api_ready(config)
    headers = build_headers(config)
    url = f"{config.api_url}{path}"
    try:
        response = requests.request(method, url, headers=headers, json=json_body, timeout=15)
        if response.status_code == 204 or not response.content:
            response.raise_for_status()
            return {}
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        typer.secho(f"API request failed ({exc.response.status_code}): {exc.response.text}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except requests.RequestException as exc:
        typer.secho(f"Failed to contact management API: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command("list")
def list_templates(
    ctx: typer.Context,
    query: Optional[str] = typer.Option(
        None,
        "--query",
        "-q",
        help="Filter templates by substring.",
    ),
) -> None:
    """
    List templates known to the management API.
    """

    path = "/api/templates"
    if query:
        path += f"?query={query}"
    data = _api_request(ctx, "GET", path)
    config = _get_cli_config(ctx)
    render_output(config, data)


@app.command("info")
def template_info(ctx: typer.Context, template_id: str) -> None:
    """
    Show metadata for a specific template.
    """

    data = _api_request(ctx, "GET", f"/api/templates/{template_id}")
    config = _get_cli_config(ctx)
    render_output(config, data)


@app.command("search")
def search_templates(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Query string to search community templates."),
) -> None:
    path = "/api/templates/search"
    if query:
        path += f"?query={query}"
    data = _api_request(ctx, "GET", path)
    config = _get_cli_config(ctx)
    render_output(config, data)


@app.command("install")
def install_template(
    ctx: typer.Context,
    template_id: Optional[str] = typer.Argument(None, help="Template ID to install from the community catalogue."),
    file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        exists=True,
        dir_okay=False,
        help="Local template package (zip). Overrides template_id download.",
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url",
        help="Override download URL for the template package.",
    ),
) -> None:
    payload: dict = {}
    if template_id:
        _warn_if_custom_override(ctx, template_id)
    if file:
        package_bytes = file.read_bytes()
        payload["package"] = base64.b64encode(package_bytes).decode("utf-8")
        if template_id:
            payload["template_id"] = template_id
    elif template_id:
        payload["template_id"] = template_id
        if url:
            payload["url"] = url
    else:
        raise typer.BadParameter("Provide either a template_id or --file.")

    _api_request(ctx, "POST", "/api/templates/install", payload)
    typer.secho("Template installation request submitted.", fg=typer.colors.GREEN)


@app.command("customize")
def customize_template(ctx: typer.Context, template_id: str) -> None:
    data = _api_request(ctx, "POST", f"/api/templates/{template_id}/customize")
    typer.secho(f"Custom template ready at {data.get('path')}", fg=typer.colors.GREEN)


@app.command("diff")
def diff_template(ctx: typer.Context, template_id: str) -> None:
    data = _api_request(ctx, "GET", f"/api/templates/{template_id}/diff")
    typer.echo(data.get("diff", ""))


@app.command("merge")
def merge_template(ctx: typer.Context, template_id: str) -> None:
    _api_request(ctx, "POST", f"/api/templates/{template_id}/merge")
    typer.secho("Custom template merged with default.", fg=typer.colors.GREEN)


@app.command("revert")
def revert_template(ctx: typer.Context, template_id: str) -> None:
    _api_request(ctx, "DELETE", f"/api/templates/{template_id}/custom")
    typer.secho("Custom template removed; default will be used.", fg=typer.colors.GREEN)


@app.command("validate")
def validate_template(
    ctx: typer.Context,
    path: Path = typer.Argument(..., exists=True, dir_okay=True, help="Template directory to validate."),
) -> None:
    archive = _zip_directory(path)
    payload = {"archive": base64.b64encode(archive).decode("utf-8")}
    data = _api_request(ctx, "POST", "/api/templates/validate", payload)
    config = _get_cli_config(ctx)
    render_output(config, data)


def _zip_directory(path: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        if path.is_file():
            archive.write(path, arcname=path.name)
        else:
            for item in path.rglob("*"):
                archive.write(item, arcname=item.relative_to(path.parent))
    return buffer.getvalue()


def _warn_if_custom_override(ctx: typer.Context, template_id: str) -> None:
    try:
        existing = _api_request(ctx, "GET", f"/api/templates/{template_id}")
    except typer.Exit:  # surface original error to user
        return
    locations = existing.get("locations", [])
    if "custom" in locations:
        proceed = typer.confirm(
            f"Custom version for '{template_id}' exists. Install community package anyway?",
            default=False,
        )
        if not proceed:
            typer.secho("Installation aborted.", fg=typer.colors.YELLOW)
            raise typer.Exit(code=1)

