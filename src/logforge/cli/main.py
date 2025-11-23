"""CLI entry point placeholder."""

import typer

app = typer.Typer(help="LogForge CLI (stub)")


@app.command()
def version() -> None:
    """Temporary version command."""
    typer.echo("LogForge CLI is not yet implemented.")


def main() -> None:
    app()
