"""Template CLI commands."""

from __future__ import annotations

import typer

from logforge.cli.helpers import not_implemented

app = typer.Typer(help="Discover, install, and manage templates.")


@app.command("list")
def list_templates(
    local: bool = typer.Option(False, "--local", help="Show only local templates."),
    remote: bool = typer.Option(False, "--remote", help="Show only remote templates."),
    custom_only: bool = typer.Option(False, "--custom-only", help="Show only custom templates."),
) -> None:
    """List templates (placeholder)."""
    scope = "all"
    if local:
        scope = "local"
    if remote:
        scope = "remote"
    if custom_only:
        scope = "custom"
    not_implemented(f"templates list ({scope})")


@app.command("install")
def install_template(template_id: str) -> None:
    """Install template by ID (placeholder)."""
    not_implemented(f"templates install {template_id}")
