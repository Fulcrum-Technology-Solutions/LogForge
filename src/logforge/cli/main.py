"""LogForge CLI entry point."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Optional

import click
import httpx

from logforge.api.server import APIServer
from logforge.core.config import ConfigError, ConfigManager, LogForgeConfig
from logforge.utils.logging import configure_logging

from .http import APIClient
from .output import echo_output, render_table

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


class CLIContext:
    """Store shared CLI state."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path).expanduser() if config_path else None
        self.manager = ConfigManager(config_path=self.config_path)
        self._config: Optional[LogForgeConfig] = None

    def ensure_config(self) -> LogForgeConfig:
        if self._config is None:
            self._config = self.manager.load()
        return self._config

    def set_config_path(self, path: Path) -> None:
        self.config_path = path.expanduser()
        self.manager = ConfigManager(config_path=self.config_path)
        self._config = None


def handle_errors(func):
    """Convert internal exceptions to Click exceptions."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigError as exc:
            raise click.ClickException(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise click.ClickException(f"API request failed: {exc}") from exc
        except Exception as exc:  # pragma: no cover - safety net
            raise click.ClickException(str(exc)) from exc

    return wrapper


pass_context = click.make_pass_decorator(CLIContext, ensure=True)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to configuration file.",
)
@pass_context
def cli(ctx: CLIContext, config_path: Optional[Path]) -> None:
    """LogForge command line interface."""
    if config_path:
        ctx.set_config_path(config_path)


@cli.command()
@click.option(
    "--path",
    "base_path",
    type=click.Path(file_okay=False, path_type=Path),
    help="Initialize configuration under this directory.",
)
@click.option("--force", is_flag=True, help="Overwrite existing configuration files.")
@pass_context
@handle_errors
def init(ctx: CLIContext, base_path: Optional[Path], force: bool) -> None:
    """Initialize configuration and directories."""
    base = base_path.expanduser() if base_path else ctx.manager.config_path.parent
    base.mkdir(parents=True, exist_ok=True)
    config_path = base / "config.yaml"

    overrides = {
        "entity_registry": {"path": str(base / "entities.yaml")},
        "templates": {
            "local_path": str(base / "templates"),
            "default_path": str(base / "templates" / "default"),
            "custom_path": str(base / "templates" / "custom"),
        },
        "logging": {"file": str(base / "logforge.log")},
        "outputs": {
            "definitions": [
                {
                    "name": "default_file",
                    "type": "file",
                    "path": str(base / "logs" / "{generator}.log"),
                    "rotation": {
                        "type": "size",
                        "max_size": "100MB",
                        "max_age": "7d",
                        "compress": True,
                    },
                },
                {"name": "console_json", "type": "console", "format": "json"},
            ]
        },
    }

    manager = ConfigManager(config_path=config_path)
    manager.save_default(overwrite=force, overrides=overrides)
    manager.ensure_supporting_files(base_dir=base)
    ctx.set_config_path(config_path)

    click.secho(f"Initialized LogForge configuration at {config_path}", fg="green")


@cli.group()
def config() -> None:
    """Configuration commands."""


@config.command("show")
@click.option(
    "--output",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    show_default=True,
)
@pass_context
@handle_errors
def config_show(ctx: CLIContext, output: str) -> None:
    """Display current configuration."""
    cfg = ctx.ensure_config()
    echo_output(cfg.model_dump(mode="json"), output)


@config.command("validate")
@pass_context
@handle_errors
def config_validate(ctx: CLIContext) -> None:
    """Validate configuration file."""
    ctx.ensure_config()
    click.secho("Configuration valid.", fg="green")


@cli.group()
def api() -> None:
    """API server commands."""


@api.command("start")
@click.option("--host", type=str, help="Override API host.")
@click.option("--port", type=int, help="Override API port.")
@pass_context
@handle_errors
def api_start(ctx: CLIContext, host: Optional[str], port: Optional[int]) -> None:
    """Start the embedded FastAPI server."""
    cfg = ctx.ensure_config()
    if host:
        cfg.api.host = host
    if port:
        cfg.api.port = port

    configure_logging(cfg.logging)
    server = APIServer(cfg)
    click.secho(f"Starting API server on {cfg.api.host}:{cfg.api.port} (press Ctrl+C to stop)", fg="green")

    try:
        server.start(background=False)
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
        server.stop()


@cli.command()
@click.option(
    "--api-url",
    default=None,
    envvar="LOGFORGE_API_URL",
    help="Override API URL (default derived from config).",
)
@click.option(
    "--api-key",
    default=None,
    envvar="LOGFORGE_API_KEY",
    help="API key for authenticated requests.",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    show_default=True,
)
@pass_context
@handle_errors
def status(ctx: CLIContext, api_url: Optional[str], api_key: Optional[str], output: str) -> None:
    """Fetch system status from the API."""
    cfg = ctx.ensure_config()
    base_url = api_url or f"http://{cfg.api.host}:{cfg.api.port}"
    key = api_key or (cfg.api.auth.key if cfg.api.auth.enabled else None)

    with APIClient(base_url=base_url, api_key=key) as client:
        data = client.json_request("GET", "/api/status")

    if output == "table":
        click.echo(f"Uptime: {data.get('uptime')}s | Version: {data.get('version')}")
        generators = data.get("generators") or []
        if generators:
            click.echo("\nGenerators:")
            render_table(generators)
        else:
            click.echo("\nGenerators: none")
        system = data.get("system") or {}
        if system:
            click.echo("\nSystem:")
            render_table(system)
    else:
        echo_output(data, output)
