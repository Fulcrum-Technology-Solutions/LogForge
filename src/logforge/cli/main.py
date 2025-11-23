"""LogForge CLI entry point."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import typer

from logforge import __version__
from logforge.cli import config, entities, generators, outputs, templates


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


if __name__ == "__main__":
    app()
