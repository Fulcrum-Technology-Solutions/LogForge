from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
import yaml
from pydantic import ValidationError

from logforge import __version__
from logforge.api.server import ApiServer
from logforge.core.config import (
    LogForgeConfig,
    default_config_path,
    default_entities_path,
    default_templates_dir,
    ensure_runtime_paths,
    load_config,
    write_default_config,
)
from logforge.utils.logging import configure_logging


def _write_entities_file(path: Path, *, force: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    default_payload = {
        "organization": {
            "name": "Example Corporation",
            "domain": "example.com",
            "contacts": {"admin": "admin@example.com", "security": "security@example.com"},
        },
        "users": [
            {
                "username": "jsmith",
                "email": "jsmith@example.com",
                "full_name": "John Smith",
                "department": "Engineering",
                "role": "Senior Developer",
            }
        ],
        "devices": [
            {
                "hostname": "ws-001",
                "ip_address": "192.168.1.10",
                "mac_address": "00:11:22:33:44:55",
                "os": "Windows 11",
                "owner": "jsmith",
            }
        ],
        "services": [
            {
                "name": "web_app",
                "description": "Primary web application",
                "url": "https://app.example.com",
                "protocol": "https",
                "port": 443,
            }
        ],
    }
    if path.exists() and not force:
        raise FileExistsError(f"Entities file already exists at {path}")
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(default_payload, handle, sort_keys=False)
    return path


@click.group()
@click.version_option(__version__)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Override configuration path.",
)
@click.pass_context
def cli(ctx: click.Context, config_path: Optional[Path]) -> None:
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path


@cli.command()
@click.option(
    "--path",
    "state_path",
    type=click.Path(path_type=Path, file_okay=False),
    default=None,
    help="Base directory for LogForge state (defaults to ~/.logforge).",
)
@click.option("--force", is_flag=True, help="Overwrite existing files.")
def init(state_path: Optional[Path], force: bool) -> None:
    base_config_path = state_path / "config.yaml" if state_path else default_config_path()
    entities_path = state_path / "entities.yaml" if state_path else default_entities_path()
    templates_dir = state_path / "templates" if state_path else default_templates_dir()

    ensure_runtime_paths()
    if state_path:
        state_path.mkdir(parents=True, exist_ok=True)
        (templates_dir / "default").mkdir(parents=True, exist_ok=True)
        (templates_dir / "custom").mkdir(parents=True, exist_ok=True)

    try:
        config_file = write_default_config(base_config_path, force=force)
    except FileExistsError as exc:
        if not force:
            raise click.ClickException(str(exc)) from exc
        config_file = write_default_config(base_config_path, force=True)

    try:
        entities_file = _write_entities_file(entities_path, force=force)
    except FileExistsError as exc:
        if not force:
            raise click.ClickException(str(exc)) from exc
        entities_file = _write_entities_file(entities_path, force=True)

    click.echo(f"Configuration written to {config_file}")
    click.echo(f"Entities file written to {entities_file}")
    click.echo(f"Template directories ensured at {templates_dir}")


def _resolve_config(ctx: click.Context) -> LogForgeConfig:
    path_override = ctx.obj.get("config_path") if ctx.obj else None
    return load_config(config_path=path_override)


def _resolve_config_with_overrides(ctx: click.Context, overrides: Optional[dict] = None) -> LogForgeConfig:
    path_override = ctx.obj.get("config_path") if ctx.obj else None
    return load_config(config_path=path_override, overrides=overrides or {})


@cli.group()
@click.pass_context
def config(ctx: click.Context) -> None:
    ctx.ensure_object(dict)
    if "config_path" not in ctx.obj:
        ctx.obj["config_path"] = None


@config.command("show")
@click.option(
    "--output",
    type=click.Choice(["yaml", "json"], case_sensitive=False),
    default="yaml",
)
@click.pass_context
def config_show(ctx: click.Context, output: str) -> None:
    config = _resolve_config(ctx)
    data = config.dict_with_expanded_paths()
    if output.lower() == "json":
        import json

        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(yaml.safe_dump(data, sort_keys=False))


@config.command("validate")
@click.pass_context
def config_validate(ctx: click.Context) -> None:
    try:
        _resolve_config(ctx)
    except (ValidationError, ValueError) as exc:
        raise click.ClickException(f"Invalid configuration: {exc}") from exc
    click.echo("Configuration is valid.")


@cli.group()
@click.pass_context
def api(ctx: click.Context) -> None:
    ctx.ensure_object(dict)


@api.command("serve")
@click.option("--host", type=str, default=None, help="Override bind host.")
@click.option("--port", type=int, default=None, help="Override bind port.")
@click.option("--no-console-log", is_flag=True, default=False, help="Disable console logging output.")
@click.pass_context
def api_serve(ctx: click.Context, host: Optional[str], port: Optional[int], no_console_log: bool) -> None:
    overrides = {}
    if host:
        overrides.setdefault("api", {})["host"] = host
    if port:
        overrides.setdefault("api", {})["port"] = port

    config = _resolve_config_with_overrides(ctx, overrides)
    ensure_runtime_paths()
    configure_logging(config.logging, enable_console=not no_console_log)

    server = ApiServer(config)
    click.echo(f"Starting LogForge API on http://{config.api.host}:{config.api.port}")
    try:
        server.start(background=False)
    except KeyboardInterrupt:
        click.echo("Shutting down...")
        server.stop()
