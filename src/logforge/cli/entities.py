from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import click
import yaml

from logforge.cli.utils import APIClient, APIClientError, echo_api_error, render_output
from logforge.entities import validator

ENTITY_TYPES = click.Choice(["users", "devices", "services"], case_sensitive=False)


def _load_payload(path: Path) -> Dict:
    raw = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(raw) or {}
        return json.loads(raw)
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise click.ClickException(f"Failed to parse {path}: {exc}") from exc


@click.group(help="Manage the entity registry via the API.")
@click.pass_context
def entities(ctx: click.Context) -> None:
    """Entity registry commands."""
    ctx.ensure_object(dict)


@entities.command("list", help="List entities or provide summary counts.")
@click.option("--type", "entity_type", type=ENTITY_TYPES, default=None)
@click.option("--output", type=click.Choice(["table", "json"], case_sensitive=False), default="table")
@click.pass_context
def list_entities(ctx: click.Context, entity_type: Optional[str], output: str) -> None:
    """Display entities or summary counts in the requested format."""
    client: APIClient = ctx.obj["api_client"]
    try:
        if entity_type:
            payload = client.get(f"/api/entities/{entity_type.lower()}")
            data = payload
            columns = _columns_for(entity_type.lower())
        else:
            payload = client.get("/api/entities")
            data = [
                {"type": "users", "count": payload["users"]},
                {"type": "devices", "count": payload["devices"]},
                {"type": "services", "count": payload["services"]},
            ]
            columns = [("type", "TYPE"), ("count", "COUNT")]
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()

    click.echo(render_output(data, output, columns=columns if output.lower() == "table" else None))


@entities.command("show", help="Show a single entity by type and identifier.")
@click.argument("entity_type", type=ENTITY_TYPES)
@click.argument("identifier", type=str)
@click.option("--output", type=click.Choice(["yaml", "json"], case_sensitive=False), default="yaml")
@click.pass_context
def show_entity(ctx: click.Context, entity_type: str, identifier: str, output: str) -> None:
    """Show a specific entity in YAML or JSON format."""
    client: APIClient = ctx.obj["api_client"]
    try:
        payload = client.get(f"/api/entities/{entity_type.lower()}/{identifier}")
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    if output.lower() == "json":
        click.echo(json.dumps(payload, indent=2))
    else:
        click.echo(yaml.safe_dump(payload, sort_keys=False))


@entities.command("add", help="Add a new entity from a YAML or JSON file.")
@click.argument("entity_type", type=ENTITY_TYPES)
@click.option("--file", "file_path", type=click.Path(path_type=Path), required=True)
@click.pass_context
def add_entity(ctx: click.Context, entity_type: str, file_path: Path) -> None:
    """Create a new entity from the provided payload file."""
    payload = _load_payload(file_path)
    client: APIClient = ctx.obj["api_client"]
    try:
        created = client.post(f"/api/entities/{entity_type.lower()}", json_body=payload)
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    click.echo(yaml.safe_dump(created, sort_keys=False))


@entities.command("delete", help="Delete an entity by identifier.")
@click.argument("entity_type", type=ENTITY_TYPES)
@click.argument("identifier", type=str)
@click.pass_context
def delete_entity(ctx: click.Context, entity_type: str, identifier: str) -> None:
    """Delete an entity from the registry."""
    client: APIClient = ctx.obj["api_client"]
    try:
        client.request("DELETE", f"/api/entities/{entity_type.lower()}/{identifier}")
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    click.echo(f"Deleted {entity_type} entry '{identifier}'.")


@entities.command("import", help="Import entities from a bundle file.")
@click.option("--file", "file_path", type=click.Path(path_type=Path), required=True)
@click.option("--replace", is_flag=True, help="Replace existing registry instead of merging.")
@click.pass_context
def import_entities(ctx: click.Context, file_path: Path, replace: bool) -> None:
    """Import an entity bundle, optionally replacing existing data."""
    payload = _load_payload(file_path)
    client: APIClient = ctx.obj["api_client"]
    try:
        endpoint = "/api/entities/import"
        if replace:
            endpoint += "?replace=true"
        result = client.post(endpoint, json_body=payload)
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    click.echo("Import succeeded.")
    click.echo(yaml.safe_dump(result, sort_keys=False))


@entities.command("export", help="Export the entity registry to stdout or a file.")
@click.option("--file", "file_path", type=click.Path(path_type=Path), default=None)
@click.pass_context
def export_entities(ctx: click.Context, file_path: Optional[Path]) -> None:
    """Export the entity registry to stdout or a file."""
    client: APIClient = ctx.obj["api_client"]
    try:
        payload = client.get("/api/entities/export")
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    output = yaml.safe_dump(payload, sort_keys=False)
    if file_path:
        file_path.write_text(output, encoding="utf-8")
        click.echo(f"Wrote export to {file_path}")
    else:
        click.echo(output)


@entities.command("validate", help="Validate an entity bundle file.")
@click.option("--file", "file_path", type=click.Path(path_type=Path), required=True)
def validate_entities(file_path: Path) -> None:
    """Validate the entity bundle for schema and duplication issues."""
    payload = _load_payload(file_path)
    try:
        validator.validate_bundle(payload)
    except validator.EntityValidationError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo("Entities file is valid.")


def _columns_for(entity_type: str):
    if entity_type == "users":
        return [
            ("username", "USERNAME"),
            ("email", "EMAIL"),
            ("department", "DEPARTMENT"),
            ("role", "ROLE"),
        ]
    if entity_type == "devices":
        return [
            ("hostname", "HOSTNAME"),
            ("ip_address", "IP"),
            ("owner", "OWNER"),
            ("os", "OS"),
        ]
    return [
        ("name", "NAME"),
        ("url", "URL"),
        ("protocol", "PROTOCOL"),
        ("port", "PORT"),
    ]
