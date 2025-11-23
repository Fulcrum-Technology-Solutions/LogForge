from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import typer

from logforge import __version__
from logforge.core import config as core_config
from . import entities as entities_commands
from . import generators as generators_commands
from . import templates as templates_commands
from .common import CLIConfig

app = typer.Typer(help="LogForge synthetic event generator CLI.")
app.add_typer(entities_commands.app, name="entities")
app.add_typer(generators_commands.app, name="generators")
app.add_typer(templates_commands.app, name="templates")




def version_callback(value: bool) -> bool:
    if value:
        typer.echo(f"LogForge {__version__}")
        raise typer.Exit()
    return value


def _collect_interactive_inputs() -> Dict[str, Any]:
    org_name = typer.prompt("Organization name", default="Example Organization").strip()
    if not org_name:
        org_name = "Example Organization"

    domain_default = "example.com"
    domain = typer.prompt("Organization domain", default=domain_default).strip().lower()
    if not domain:
        domain = domain_default

    log_dir_input = typer.prompt(
        "Log output directory",
        default="/var/log/logforge",
    ).strip()
    log_dir = Path(log_dir_input or "/var/log/logforge").expanduser()

    event_rate = typer.prompt(
        "Default event generation rate (events/sec)",
        default=10,
        type=int,
    )
    if event_rate <= 0:
        typer.secho("Event rate must be positive; using 10.", fg=typer.colors.YELLOW)
        event_rate = 10

    api_port = typer.prompt(
        "API server port",
        default=8080,
        type=int,
    )
    if api_port <= 0 or api_port > 65535:
        typer.secho("Invalid port; using 8080.", fg=typer.colors.YELLOW)
        api_port = 8080

    install_templates = typer.confirm(
        "Install starter template pack after init?",
        default=True,
    )

    return {
        "organization_name": org_name,
        "domain": domain,
        "log_output_dir": log_dir,
        "event_rate": event_rate,
        "api_port": api_port,
        "install_templates": install_templates,
    }


@app.callback()
def main(
    ctx: typer.Context,
    api_url: str = typer.Option(
        "http://127.0.0.1:8080",
        "--api-url",
        envvar="LOGFORGE_API_URL",
        help="Management API base URL.",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="LOGFORGE_API_KEY",
        help="API key for authenticated environments.",
    ),
    output: str = typer.Option(
        "table",
        "--output",
        "-o",
        help="Output format for command results.",
        show_default=True,
    ),
    skip_health_check: bool = typer.Option(
        False,
        "--skip-health-check",
        help="Skip the API health check before running commands.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        is_flag=True,
        help="Show the LogForge version and exit.",
    ),
) -> None:
    """
    CLI entrypoint that configures shared state for subcommands.
    """

    _ = version  # trigger callback side-effects, silence linters
    normalized_output = output.lower()
    if normalized_output not in {"table", "json"}:
        raise typer.BadParameter("Output format must be 'table' or 'json'.")
    ctx.obj = CLIConfig(
        api_url=api_url.rstrip("/"),
        api_key=api_key,
        output=normalized_output,
        skip_health_check=skip_health_check,
    )


@app.command()
def init(
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Run interactive configuration wizard.",
    ),
    config_path: Optional[str] = typer.Option(
        None,
        "--config",
        help="Override default config path within LOGFORGE_HOME.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration files.",
    ),
) -> None:
    """
    Initialize LogForge configuration and directory structure.
    """

    interactive_inputs = _collect_interactive_inputs() if interactive else None

    try:
        home = core_config.resolve_logforge_home()
    except core_config.ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    home.mkdir(parents=True, exist_ok=True)

    templates_root = home / "templates"
    (templates_root / "default").mkdir(parents=True, exist_ok=True)
    (templates_root / "custom").mkdir(parents=True, exist_ok=True)

    if config_path:
        candidate = Path(config_path)
        if not candidate.is_absolute():
            candidate = home / candidate
        resolved_candidate = candidate.resolve(strict=False)
        home_resolved = home.resolve(strict=False)
        if not str(resolved_candidate).startswith(str(home_resolved)):
            typer.secho(
                f"Config overrides must live inside LOGFORGE_HOME ({home_resolved}), "
                f"got {resolved_candidate}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)
    else:
        resolved_candidate = None

    created_artifacts = []

    config_kwargs: Dict[str, Any] = {}
    if interactive_inputs:
        config_kwargs = {
            "log_output_dir": interactive_inputs["log_output_dir"],
            "default_event_rate": interactive_inputs["event_rate"],
            "api_port": interactive_inputs["api_port"],
        }

    config_data = core_config.default_config_dict(**config_kwargs)

    try:
        config_file = core_config.write_default_config(
            target_path=resolved_candidate,
            overwrite=force,
            config_data=config_data,
        )
        created_artifacts.append(config_file)
    except core_config.ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    entity_kwargs: Dict[str, Any] = {}
    if interactive_inputs:
        entity_kwargs = {
            "organization_name": interactive_inputs["organization_name"],
            "domain": interactive_inputs["domain"],
        }

    try:
        entities_file = core_config.write_default_entities(
            overwrite=force,
            **entity_kwargs,
        )
        created_artifacts.append(entities_file)
    except core_config.ConfigError as exc:
        if force:
            typer.secho(str(exc), fg=typer.colors.RED)
            raise typer.Exit(code=1) from exc
        typer.secho(f"Skipped entities file: {exc}", fg=typer.colors.YELLOW)
        entities_file = None

    typer.secho("Initialization complete.", fg=typer.colors.GREEN)
    typer.echo(f"LOGFORGE_HOME: {home}")
    for artifact in created_artifacts:
        typer.echo(f" - {artifact}")
    if entities_file is None:
        typer.echo(" - entities.yaml already present; leaving untouched.")
    if interactive_inputs and interactive_inputs.get("install_templates"):
        typer.secho(
            "Starter template installation will be available in a future update. "
            "You can manually install packs via 'logforge templates install'.",
            fg=typer.colors.YELLOW,
        )


def main_entry() -> None:
    app()


def main() -> None:
    main_entry()


from .common import build_headers, ensure_api_ready, render_output

