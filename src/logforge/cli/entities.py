"""Entity CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import typer
import yaml

from logforge.cli.api_client import APIClient
from logforge.entities.storage import EntityStorage
from logforge.entities.validator import EntityValidationError, validate_entities

app = typer.Typer(help="Inspect and manage entity registry data.")


def _client(ctx: typer.Context) -> APIClient:
    if ctx.obj is None:
        raise typer.BadParameter("CLI context missing. Ensure you call from main CLI.")
    return cast(APIClient, ctx.obj.client())


@app.command("list")
def list_entities(
    ctx: typer.Context,
    entity_type: str = typer.Option(
        "summary",
        "--type",
        "-t",
        help="summary, users, devices, or services",
    ),
) -> None:
    """List entities or show summary via API."""

    client = _client(ctx)
    if entity_type == "summary":
        data = client.get("/api/entities")
        typer.echo(json.dumps(data, indent=2))
    else:
        data = client.get(f"/api/entities/{entity_type}")
        typer.echo(json.dumps(data, indent=2))


@app.command("add")
def add_entity(
    ctx: typer.Context,
    entity_type: str = typer.Argument(...),
    payload: str = typer.Option(
        ...,
        "--data",
        help="JSON string representing the entity payload.",
    ),
) -> None:
    """Add an entity via the API."""

    data = json.loads(payload)
    client = _client(ctx)
    created = client.post(f"/api/entities/{entity_type}", data)
    typer.echo(json.dumps(created, indent=2))


@app.command("import")
def import_entities(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, help="Path to entities.yaml"),
) -> None:
    """Import entities from a YAML file (local operation)."""

    data = yaml.safe_load(path.read_text())
    document = validate_entities(data)
    storage = EntityStorage(path=path)
    storage.save(document.model_dump())
    typer.secho(f"Imported entities from {path}", fg=typer.colors.GREEN)


@app.command("export")
def export_entities(
    destination: Path = typer.Argument(..., dir_okay=False),
) -> None:
    """Export current registry to a YAML file."""

    storage = EntityStorage()
    data = storage.load()
    destination.write_text(yaml.safe_dump(data, sort_keys=False))
    typer.secho(f"Exported entities to {destination}", fg=typer.colors.GREEN)


@app.command("validate")
def validate_entities_cmd(
    path: Path = typer.Option(None, "--path", help="Optional entities.yaml path"),
) -> None:
    """Validate entities.yaml locally."""

    storage = EntityStorage(path=path)
    data = storage.load()
    try:
        validate_entities(data)
    except EntityValidationError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    typer.secho("Entities validation successful.", fg=typer.colors.GREEN)
