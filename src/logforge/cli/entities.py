from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import requests
import typer
from .common import CLIConfig, build_headers, ensure_api_ready, render_output

app = typer.Typer(help="Manage LogForge entity registry via the management API.")


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
        response = requests.request(method, url, headers=headers, json=json_body, timeout=10)
        if method.upper() == "DELETE" and response.status_code == 204:
            return {}
        response.raise_for_status()
        if response.content:
            return response.json()
        return {}
    except requests.HTTPError as exc:
        typer.secho(f"API request failed ({exc.response.status_code}): {exc.response.text}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except requests.RequestException as exc:
        typer.secho(f"Failed to contact management API: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command("list")
def list_entities(
    ctx: typer.Context,
    entity_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Entity type to list (users, devices, services, organization).",
    ),
) -> None:
    """
    Display entity registry information from the management API.
    """

    entity_type_normalized = entity_type.lower() if entity_type else None
    if entity_type_normalized is None:
        data = _api_request(ctx, "GET", "/api/entities")
    else:
        data = _api_request(ctx, "GET", f"/api/entities/{entity_type_normalized}")

    config_obj = _get_cli_config(ctx)
    render_output(config_obj, data)


@app.command("show")
def show_entity(
    ctx: typer.Context,
    entity_type: str = typer.Argument(..., help="Entity type (users, devices, services, organization)."),
    identifier: str = typer.Argument(..., help="Identifier (username, hostname, service name, or organization name)."),
) -> None:
    entity_type = entity_type.lower()
    data = _api_request(ctx, "GET", f"/api/entities/{entity_type}/{identifier}")
    config = _get_cli_config(ctx)
    render_output(config, data)


@app.command("add")
def add_entity(
    ctx: typer.Context,
    entity_type: str = typer.Argument(..., help="Entity type to add (users, devices, services)."),
) -> None:
    entity_type = entity_type.lower()
    payload = _collect_entity_payload(entity_type)
    data = _api_request(ctx, "POST", f"/api/entities/{entity_type}", {"entity": payload})
    config = _get_cli_config(ctx)
    render_output(config, data)


@app.command("update")
def update_entity(
    ctx: typer.Context,
    entity_type: str = typer.Argument(..., help="Entity type to update (users, devices, services)."),
    identifier: str = typer.Argument(..., help="Identifier (username, hostname, or service name)."),
) -> None:
    entity_type = entity_type.lower()
    payload = _collect_entity_payload(entity_type, identifier=identifier)
    data = _api_request(ctx, "PUT", f"/api/entities/{entity_type}/{identifier}", {"entity": payload})
    config = _get_cli_config(ctx)
    render_output(config, data)


@app.command("delete")
def delete_entity(
    ctx: typer.Context,
    entity_type: str = typer.Argument(..., help="Entity type to delete (users, devices, services)."),
    identifier: str = typer.Argument(..., help="Identifier (username, hostname, or service name)."),
) -> None:
    entity_type = entity_type.lower()
    _api_request(ctx, "DELETE", f"/api/entities/{entity_type}/{identifier}")
    typer.secho(f"Deleted {entity_type[:-1]} '{identifier}'.", fg=typer.colors.GREEN)


@app.command("import")
def import_entities(
    ctx: typer.Context,
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True, help="YAML file to import."),
) -> None:
    content = path.read_text(encoding="utf-8")
    _api_request(ctx, "POST", "/api/entities/import", {"content": content})
    typer.secho("Entities imported successfully.", fg=typer.colors.GREEN)


@app.command("export")
def export_entities(
    ctx: typer.Context,
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional destination file. Writes to stdout if omitted.",
    ),
) -> None:
    data = _api_request(ctx, "GET", "/api/entities/export")
    content = data.get("content", "")
    if output:
        output.write_text(content, encoding="utf-8")
        typer.secho(f"Exported entities to {output}", fg=typer.colors.GREEN)
    else:
        typer.echo(content)


@app.command("validate")
def validate_entities(
    ctx: typer.Context,
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True, help="YAML file to validate."),
) -> None:
    content = path.read_text(encoding="utf-8")
    _api_request(ctx, "POST", "/api/entities/validate", {"content": content})
    typer.secho("Validation successful.", fg=typer.colors.GREEN)


def _collect_entity_payload(entity_type: str, identifier: Optional[str] = None) -> Dict[str, object]:
    if entity_type == "users":
        username = identifier or typer.prompt("Username")
        email = typer.prompt("Email")
        full_name = typer.prompt("Full name")
        department = typer.prompt("Department", default="")
        role = typer.prompt("Role", default="")
        return {
            "username": username,
            "email": email,
            "full_name": full_name,
            "department": department or None,
            "role": role or None,
            "attributes": _prompt_key_values("Attribute"),
        }
    if entity_type == "devices":
        hostname = identifier or typer.prompt("Hostname")
        ip_address = typer.prompt("IP address")
        mac_address = typer.prompt("MAC address (XX:XX:XX:XX:XX:XX)")
        os_value = typer.prompt("Operating system", default="")
        owner = typer.prompt("Owner username", default="")
        dev_type = typer.prompt("Device type", default="")
        return {
            "hostname": hostname,
            "ip_address": ip_address,
            "mac_address": mac_address,
            "os": os_value or None,
            "owner": owner or None,
            "type": dev_type or None,
            "attributes": _prompt_key_values("Attribute"),
        }
    if entity_type == "services":
        name = identifier or typer.prompt("Service name")
        description = typer.prompt("Description", default="")
        url = typer.prompt("URL", default="")
        port = typer.prompt("Port", type=int)
        protocol = typer.prompt("Protocol (e.g. http, https)")
        return {
            "name": name,
            "description": description or None,
            "url": url or None,
            "port": port,
            "protocol": protocol,
            "attributes": _prompt_key_values("Attribute"),
        }
    raise typer.BadParameter(f"Unsupported entity type: {entity_type}")


def _prompt_key_values(label: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    while typer.confirm(f"Add {label.lower()}?", default=False):
        key = typer.prompt(f"{label} key")
        value = typer.prompt(f"{label} value")
        values[key] = value
    return values

