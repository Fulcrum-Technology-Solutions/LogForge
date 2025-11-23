"""Template CLI commands."""

from __future__ import annotations

import difflib
import json
import shutil
from pathlib import Path
from typing import List, Optional, Sequence

import typer

from logforge.cli.api_client import APIClient
from logforge.templates.loader import TemplateLoader
from logforge.templates.validator import TemplateValidationError, TemplateValidator

app = typer.Typer(help="Discover, install, and manage templates.")


def _client(ctx: typer.Context) -> APIClient:
    if ctx.obj is None:
        raise typer.BadParameter("CLI context missing; run through `logforge` entrypoint.")
    return ctx.obj.client()


def _output_json(ctx: typer.Context) -> bool:
    return bool(getattr(ctx.obj, "output_format", "table") == "json")


def _emit(ctx: typer.Context, data: dict) -> None:
    if _output_json(ctx):
        typer.echo(json.dumps(data, indent=2))
    else:
        if "templates" in data:
            for tpl in data["templates"]:
                typer.echo(f"{tpl['id']} [{tpl['location']}] - {tpl['name']}")
        else:
            typer.echo(json.dumps(data, indent=2))


def _normalize_diff_target(value: str) -> str:
    allowed = {"all", "metadata", "template"}
    normalized = value.lower()
    if normalized not in allowed:
        raise typer.BadParameter(f"--file must be one of: {', '.join(sorted(allowed))}")
    return normalized


def _read_lines(path: Path) -> List[str]:
    return path.read_text().splitlines()


def _diff_files(default_path: Path, custom_path: Path) -> Sequence[str]:
    return list(
        difflib.unified_diff(
            _read_lines(default_path),
            _read_lines(custom_path),
            fromfile=f"default/{default_path.name}",
            tofile=f"custom/{custom_path.name}",
            lineterm="",
        )
    )


@app.command("list")
def list_templates(ctx: typer.Context) -> None:
    """List available templates via the API."""
    response = _client(ctx).get("/api/templates")
    _emit(ctx, response)


@app.command("info")
def template_info(ctx: typer.Context, template_id: str = typer.Argument(...)) -> None:
    """Show metadata for a single template."""
    data = _client(ctx).get(f"/api/templates/{template_id}")
    if _output_json(ctx):
        typer.echo(json.dumps(data, indent=2))
        return
    summary = data["summary"]
    typer.secho(f"{summary['id']} ({summary['location']})", bold=True)
    typer.echo(f"Name       : {summary['name']}")
    typer.echo(f"Vendor     : {summary['vendor']}")
    typer.echo(f"Product    : {summary['product']}")
    typer.echo(f"Data Source: {summary['data_source']}")
    if summary.get("version"):
        typer.echo(f"Version    : {summary['version']}")
    if description := data["metadata"].get("description"):
        typer.echo(f"Description: {description}")


@app.command("validate")
def validate_template(
    ctx: typer.Context,
    template_id: Optional[str] = typer.Option(
        None,
        "--id",
        help="Validate a template by ID (using the configured LOGFORGE_HOME).",
    ),
    metadata_path: Optional[Path] = typer.Option(
        None,
        "--path",
        exists=True,
        dir_okay=False,
        help="Validate a template from an arbitrary metadata.yaml path.",
    ),
) -> None:
    """Validate template metadata + Jinja syntax."""
    if not template_id and not metadata_path:
        raise typer.BadParameter("Provide either --id or --path.")
    loader = TemplateLoader()
    validator = TemplateValidator(loader)
    try:
        if metadata_path:
            result = validator.validate_path(metadata_path)
        else:
            result = validator.validate(template_id or "")
    except TemplateValidationError as exc:
        typer.secho(f"Validation failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    typer.secho(f"Template '{result.template_id}' is valid.", fg=typer.colors.GREEN)


@app.command("customize")
def customize_template(
    template_id: str = typer.Argument(...),
    force: bool = typer.Option(False, "--force", help="Overwrite existing customization."),
) -> None:
    """Copy a default template into the custom workspace for editing."""
    loader = TemplateLoader()
    source_dir = loader.default_dir / template_id
    target_dir = loader.custom_dir / template_id
    if not source_dir.exists():
        typer.secho(f"Default template '{template_id}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    if target_dir.exists():
        if not force:
            typer.secho(
                "Custom version already exists. Use --force to overwrite.",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=1)
        shutil.rmtree(target_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, target_dir)
    typer.secho(f"Customized template created at {target_dir}", fg=typer.colors.GREEN)


@app.command("revert")
def revert_template(template_id: str = typer.Argument(...)) -> None:
    """Remove a customized template copy."""
    loader = TemplateLoader()
    target_dir = loader.custom_dir / template_id
    if not target_dir.exists():
        typer.secho("No custom template found.", fg=typer.colors.YELLOW)
        return
    shutil.rmtree(target_dir)
    typer.secho(f"Reverted custom template '{template_id}'.", fg=typer.colors.GREEN)


@app.command("diff")
def diff_template(
    template_id: str = typer.Argument(...),
    file: str = typer.Option(
        "all",
        "--file",
        "-f",
        help="File(s) to diff (metadata, template, all).",
        show_default=True,
    ),
) -> None:
    """Show differences between default and custom template files."""
    loader = TemplateLoader()
    default_dir = loader.default_dir / template_id
    custom_dir = loader.custom_dir / template_id
    if not default_dir.exists():
        typer.secho(f"Default template '{template_id}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    if not custom_dir.exists():
        typer.secho("No custom template to diff.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    target = _normalize_diff_target(file)
    sections = []
    if target in {"all", "metadata"}:
        sections.append(
            ("metadata.yaml", default_dir / "metadata.yaml", custom_dir / "metadata.yaml")
        )
    if target in {"all", "template"}:
        sections.append(
            ("template.j2", default_dir / "template.j2", custom_dir / "template.j2")
        )

    has_diff = False
    for label, default_path, custom_path in sections:
        if not default_path.exists() or not custom_path.exists():
            typer.secho(f"Missing {label} for diff.", fg=typer.colors.RED)
            continue
        diff_lines = _diff_files(default_path, custom_path)
        if diff_lines:
            has_diff = True
            typer.secho(f"=== {label} ===", fg=typer.colors.CYAN)
            typer.echo("\n".join(diff_lines))
    if not has_diff:
        typer.secho("No differences detected.", fg=typer.colors.GREEN)
