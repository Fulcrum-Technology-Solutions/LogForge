"""Configuration CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import typer
import yaml

from logforge.core.config import ConfigError, load_config, load_validated_config
from logforge.core.home import resolve_logforge_home

app = typer.Typer(help="Manage LogForge configuration settings.")


@app.command("show")
def show_config(
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        help="Path to config.yaml (defaults to LOGFORGE_HOME/config.yaml).",
    ),
    output: str = typer.Option(
        "json",
        "--output",
        "-o",
        help="Output format (json or yaml).",
    ),
) -> None:
    """Display the current configuration file."""

    config = load_config(config_path=path)
    fmt = output.lower()
    if fmt not in {"json", "yaml"}:
        raise typer.BadParameter("Output must be 'json' or 'yaml'.")

    if fmt == "json":
        typer.echo(json.dumps(config, indent=2))
    else:
        typer.echo(yaml.safe_dump(config, sort_keys=False))


@app.command("validate")
def validate_config(
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        help="Path to config.yaml (defaults to LOGFORGE_HOME/config.yaml).",
    ),
) -> None:
    """Validate configuration file using the schema."""

    try:
        model = load_validated_config(config_path=path)
    except ConfigError as exc:  # pragma: no cover - exercised via tests
        typer.secho(f"Validation failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho("Configuration is valid.", fg=typer.colors.GREEN)
    typer.echo(f"Generators defined: {len(model.generators)}")


@app.command("set")
def set_config_value(
    key: str = typer.Argument(..., help="Dot-delimited key (e.g. api.port)"),
    value: str = typer.Argument(..., help="Value to set"),
    path: Optional[Path] = typer.Option(None, "--path", help="Path to config.yaml."),
) -> None:
    """Set a configuration option and write the file back."""

    config_path = path or resolve_logforge_home() / "config.yaml"
    config = load_config(config_path=config_path)
    root = config
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in root or not isinstance(root[part], dict):
            root[part] = {}
        root = root[part]
    root[parts[-1]] = _parse_value(value)

    try:
        target_path = config_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(config, handle, sort_keys=False)
    except Exception as exc:  # pragma: no cover - out-of-scope for CI
        typer.secho(f"Failed to write configuration: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho(f"Updated {key} in {target_path}", fg=typer.colors.GREEN)


def _parse_value(raw: str) -> Any:
    for caster in (int, float):
        try:
            return caster(raw)
        except ValueError:
            continue
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    return raw
