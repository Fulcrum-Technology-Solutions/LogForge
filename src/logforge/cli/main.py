"""LogForge CLI entry point."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer

from logforge import __version__
from logforge.cli import config, entities, generators, outputs, templates
from logforge.core.default_config import DefaultConfigOptions, write_default_config


@dataclass
class CLIContext:
    """Shared options passed to subcommands."""

    api_url: str
    api_key: Optional[str]
    output_format: str


def _create_app() -> typer.Typer:
    return typer.Typer(
        help="LogForge management CLI (API-first).",
        add_completion=False,
        no_args_is_help=True,
        context_settings={"help_option_names": ["-h", "--help"]},
    )


app = _create_app()
app.add_typer(config.app, name="config")
app.add_typer(templates.app, name="templates")
app.add_typer(entities.app, name="entities")
app.add_typer(generators.app, name="generators")
app.add_typer(outputs.app, name="outputs")


def _validate_output_format(value: str) -> str:
    normalized = value.lower()
    allowed = {"table", "json"}
    if normalized not in allowed:
        raise typer.BadParameter(f"Output must be one of: {', '.join(sorted(allowed))}")
    return normalized


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    api_url: str = typer.Option(
        "http://127.0.0.1:8080",
        "--api-url",
        envvar="LOGFORGE_API_URL",
        show_default=True,
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
        show_default=True,
        callback=_validate_output_format,
        help="Default output format for commands (table or json).",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        is_eager=True,
        help="Show LogForge version and exit.",
    ),
) -> None:
    """Initialize CLI context and optionally print version info."""
    if version:
        typer.echo(f"LogForge CLI {__version__}")
        raise typer.Exit()

    ctx.obj = CLIContext(api_url=api_url, api_key=api_key, output_format=output)


@app.command("init")
def init_command(
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Launch the interactive setup wizard.",
    ),
    home: Optional[Path] = typer.Option(
        None,
        "--home",
        help="Override LOGFORGE_HOME for initialization.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing config.yaml if present.",
    ),
) -> None:
    """Initialize LogForge home with default configuration."""

    options = DefaultConfigOptions()
    if interactive:
        options = _run_init_wizard(options)

    config_path = write_default_config(
        logforge_home=home,
        overwrite=overwrite,
        options=options,
    )

    typer.secho(f"LogForge initialized. Config written to {config_path}", fg=typer.colors.GREEN)
    if options.install_templates:
        typer.secho(
            "Template installation automation is not implemented yet. "
            "Use `logforge templates install ...` once available.",
            fg=typer.colors.YELLOW,
        )


def _run_init_wizard(options: DefaultConfigOptions) -> DefaultConfigOptions:
    typer.secho("Interactive LogForge setup", bold=True)
    org_name = typer.prompt(
        "Organization name",
        default=options.organization_name,
        show_default=True,
    )
    org_domain = typer.prompt(
        "Organization domain",
        default=options.organization_domain,
        show_default=True,
    )
    log_dir = typer.prompt(
        "Log output directory",
        default=str(options.log_output_dir),
        show_default=True,
    )
    api_port = typer.prompt(
        "API server port",
        default=options.api_port,
        show_default=True,
    )
    base_rate = typer.prompt(
        "Default event generation rate (events/sec)",
        default=options.base_rate,
        show_default=True,
    )
    install_templates = typer.confirm(
        "Install starter templates now?",
        default=options.install_templates,
    )

    return DefaultConfigOptions(
        organization_name=org_name,
        organization_domain=org_domain,
        log_output_dir=Path(log_dir).expanduser(),
        api_port=int(api_port),
        base_rate=int(base_rate),
        install_templates=install_templates,
    )


if __name__ == "__main__":
    app()
