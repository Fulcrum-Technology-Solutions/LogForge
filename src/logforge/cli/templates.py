"""Template CLI commands."""

from __future__ import annotations

import difflib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional, Sequence

import typer
import yaml

from logforge.cli.api_client import APIClient
from logforge.community.client import CommunityClient, CommunityClientConfig, CommunityClientError
from logforge.community.install import TemplateInstallError, install_template_archive
from logforge.core.home import resolve_logforge_home
from logforge.templates.loader import TemplateLoader
from logforge.templates.updater import (
    TemplateUpdateCandidate,
    TemplateUpdateChecker,
    TemplateUpdateError,
)
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


def _community_client(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> CommunityClient:
    url = base_url or os.getenv("LOGFORGE_COMMUNITY_URL", "https://api.logforge.io/v1")
    key = api_key or os.getenv("LOGFORGE_COMMUNITY_API_KEY")
    config = CommunityClientConfig(base_url=url, api_key=key)
    return CommunityClient(config)


def _normalize_diff_target(value: str) -> str:
    allowed = {"all", "metadata", "template"}
    normalized = value.lower()
    if normalized not in allowed:
        raise typer.BadParameter(f"--file must be one of: {', '.join(sorted(allowed))}")
    return normalized


def _normalize_merge_strategy(value: str) -> str:
    allowed = {"default", "custom"}
    normalized = value.lower()
    if normalized not in allowed:
        raise typer.BadParameter(f"--strategy must be one of: {', '.join(sorted(allowed))}")
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


DEFAULT_TEMPLATE_BODY = """{
  "timestamp": "{{ now() | timestamp_to_iso }}",
  "vendor": "{{ metadata.vendor }}",
  "product": "{{ metadata.product }}",
  "name": "{{ metadata.name }}",
  "message": "Replace this body with your own event structure."
}
"""


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    cleaned = cleaned.strip("-")
    return cleaned or "template"


def _sanitize_template_id(template_id: str) -> str:
    normalized = template_id.strip().strip("/")
    if not normalized:
        raise typer.BadParameter("Template ID cannot be empty.")
    parts = normalized.split("/")
    for part in parts:
        if part in {"", ".", ".."} or ".." in part:
            raise typer.BadParameter("Template ID segments must not use '.' or '..'.")
    return "/".join(parts)


def _ensure_tags(tags: List[str], prompt_if_missing: bool = True) -> List[str]:
    if tags:
        return [tag for tag in tags if tag]
    if not prompt_if_missing:
        return []
    raw = typer.prompt("Tags (comma separated)", default="")
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def _serialize_update(candidate: TemplateUpdateCandidate) -> dict[str, Any]:
    return {
        "template_id": candidate.template_id,
        "current_version": candidate.current_version,
        "latest_version": candidate.latest_version,
        "location": candidate.location,
    }


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


@app.command("create")
def create_template(
    template_id: Optional[str] = typer.Option(
        None,
        "--id",
        help="Explicit template ID (vendor/product/name). Generated when omitted.",
    ),
    destination: Optional[Path] = typer.Option(
        None,
        "--destination",
        dir_okay=True,
        file_okay=False,
        help="Custom templates directory (defaults to LOGFORGE_HOME/templates/custom).",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing template directory."),
    vendor: Optional[str] = typer.Option(None, "--vendor", help="Vendor name."),
    product: Optional[str] = typer.Option(None, "--product", help="Product name."),
    name: Optional[str] = typer.Option(None, "--name", help="Template display name."),
    data_source: Optional[str] = typer.Option(None, "--data-source", help="Data source identifier."),
    description: Optional[str] = typer.Option(None, "--description", help="Template description."),
    format: str = typer.Option("json", "--format", help="Output format (json, text, etc)."),
    version: str = typer.Option("1.0.0", "--version", help="Initial version string."),
    author: Optional[str] = typer.Option(None, "--author", help="Author/maintainer name."),
    tag: List[str] = typer.Option(
        [],
        "--tag",
        help="Tag to apply to metadata (can be provided multiple times).",
    ),
) -> None:
    """Interactive template creation wizard."""

    base_dir = destination or resolve_logforge_home() / "templates" / "custom"
    vendor = vendor or typer.prompt("Vendor name", default="Acme Corp")
    product = product or typer.prompt("Product name", default="Example Product")
    display_name = name or typer.prompt("Template display name", default=f"{product} Event")
    data_source = data_source or typer.prompt("Data source", default="system")
    if description is None:
        desc_input = typer.prompt("Description", default=f"{display_name} template", show_default=True)
        description = desc_input.strip() or None
    tags = _ensure_tags(tag, prompt_if_missing=True)
    template_id = template_id or "/".join(
        [_slugify(vendor), _slugify(product), _slugify(display_name)]
    )
    template_id = _sanitize_template_id(template_id)

    target_dir = base_dir.joinpath(*template_id.split("/"))
    if target_dir.exists():
        if not force:
            typer.secho(
                f"Template '{template_id}' already exists at {target_dir}. Use --force to overwrite.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = target_dir / "metadata.yaml"
    template_path = target_dir / "template.j2"
    timestamp = datetime.now(timezone.utc).isoformat()
    metadata: dict[str, Any] = {
        "id": template_id,
        "name": display_name,
        "description": description,
        "vendor": vendor,
        "product": product,
        "data_source": data_source,
        "format": format,
        "version": version,
        "author": author,
        "created": timestamp,
        "updated": timestamp,
    }
    if tags:
        metadata["tags"] = tags
    metadata = {key: value for key, value in metadata.items() if value not in (None, [])}
    _write_yaml(metadata_path, metadata)
    template_path.write_text(DEFAULT_TEMPLATE_BODY.strip() + "\n")

    loader = TemplateLoader()
    validator = TemplateValidator(loader)
    try:
        validator.validate_path(metadata_path)
    except TemplateValidationError as exc:
        typer.secho(f"Template validation failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho(
        f"Template '{template_id}' created at {target_dir}. Customize template.j2 to begin.",
        fg=typer.colors.GREEN,
    )


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


@app.command("merge")
def merge_template(
    template_id: str = typer.Argument(...),
    strategy: str = typer.Option(
        "default",
        "--strategy",
        "-s",
        help="Merge strategy: 'default' overwrites with default, 'custom' keeps current files.",
        show_default=True,
    ),
    backup: bool = typer.Option(
        True,
        "--backup/--no-backup",
        help="Create .bak files before overwriting.",
    ),
) -> None:
    """Sync default template changes into the custom copy."""
    loader = TemplateLoader()
    default_dir = loader.default_dir / template_id
    custom_dir = loader.custom_dir / template_id
    if not default_dir.exists():
        typer.secho(f"Default template '{template_id}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    custom_dir.mkdir(parents=True, exist_ok=True)
    normalized_strategy = _normalize_merge_strategy(strategy)
    files = [
        ("metadata.yaml", default_dir / "metadata.yaml", custom_dir / "metadata.yaml"),
        ("template.j2", default_dir / "template.j2", custom_dir / "template.j2"),
    ]
    changed = False
    for label, default_path, custom_path in files:
        if not default_path.exists():
            continue
        if normalized_strategy == "custom" and custom_path.exists():
            continue
        if custom_path.exists() and normalized_strategy == "default":
            if default_path.read_text() == custom_path.read_text():
                continue
            if backup:
                backup_path = custom_path.with_suffix(custom_path.suffix + ".bak")
                shutil.copy2(custom_path, backup_path)
            shutil.copy2(default_path, custom_path)
            changed = True
        elif not custom_path.exists():
            shutil.copy2(default_path, custom_path)
            changed = True
    if changed:
        typer.secho(
            f"Merged template '{template_id}' using strategy '{normalized_strategy}'.",
            fg=typer.colors.GREEN,
        )
    else:
        typer.secho("No changes applied during merge.", fg=typer.colors.YELLOW)


@app.command("search")
def search_templates_command(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query string"),
    limit: int = typer.Option(20, "--limit", help="Maximum number of results to return."),
    community_url: Optional[str] = typer.Option(
        None,
        "--community-url",
        help="Override community API URL.",
    ),
    community_api_key: Optional[str] = typer.Option(
        None,
        "--community-api-key",
        help="API key for community template catalog.",
    ),
) -> None:
    """Search community templates."""

    client = _community_client(community_url, community_api_key)
    try:
        results = client.search_templates(query, limit=limit)
    except CommunityClientError as exc:
        typer.secho(f"Community search failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    if _output_json(ctx):
        typer.echo(json.dumps(results, indent=2))
        return
    if not results:
        typer.secho("No templates found.", fg=typer.colors.YELLOW)
        return
    for template in results:
        typer.echo(f"{template.get('id', 'unknown'):40} {template.get('name', '')}")


@app.command("install")
def install_template_from_community(
    ctx: typer.Context,
    template_id: str = typer.Argument(..., help="Community template ID to install."),
    community_url: Optional[str] = typer.Option(
        None,
        "--community-url",
        help="Override community API URL.",
    ),
    community_api_key: Optional[str] = typer.Option(
        None,
        "--community-api-key",
        help="API key for community template catalog.",
    ),
    destination: Optional[Path] = typer.Option(
        None,
        "--destination",
        dir_okay=True,
        file_okay=False,
        help=(
            "Directory to place template contents "
            "(defaults to LOGFORGE_HOME/templates/custom/<id>)."
        ),
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing template directory."),
) -> None:
    """Download and install a template from the community catalog."""

    base_dir = destination or resolve_logforge_home() / "templates" / "custom"
    target_dir = base_dir / template_id
    if target_dir.exists() and not force:
        typer.secho(
            f"Template '{template_id}' already exists at {target_dir}. Use --force to overwrite.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)
    base_dir.mkdir(parents=True, exist_ok=True)
    client = _community_client(community_url, community_api_key)
    try:
        archive_bytes = client.download_template(template_id)
        installed_path = install_template_archive(
            template_id,
            archive_bytes,
            destination=base_dir,
            force=force,
        )
    except (CommunityClientError, TemplateInstallError) as exc:
        typer.secho(f"Failed to install template: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    typer.secho(f"Installed template '{template_id}' to {installed_path}", fg=typer.colors.GREEN)


@app.command("download")
def download_template_archive(
    template_id: str = typer.Argument(..., help="Community template ID to download."),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        file_okay=True,
        dir_okay=False,
        help="Destination .forge file (defaults to ./<template_id>.forge).",
    ),
    overwrite: bool = typer.Option(False, "--force", help="Overwrite output file if it exists."),
    community_url: Optional[str] = typer.Option(
        None,
        "--community-url",
        help="Override community API URL.",
    ),
    community_api_key: Optional[str] = typer.Option(
        None,
        "--community-api-key",
        help="API key for community template catalog.",
    ),
) -> None:
    """Download a template package for offline installation."""

    default_name = template_id.replace("/", "_")
    target_file = output or Path.cwd() / f"{default_name}.forge"
    if target_file.exists() and not overwrite:
        typer.secho(
            f"File {target_file} already exists. Use --force to overwrite.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)
    target_file.parent.mkdir(parents=True, exist_ok=True)
    client = _community_client(community_url, community_api_key)
    try:
        archive_bytes = client.download_template(template_id)
    except CommunityClientError as exc:
        typer.secho(f"Failed to download template: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    target_file.write_bytes(archive_bytes)
    typer.secho(f"Saved '{template_id}' package to {target_file}", fg=typer.colors.GREEN)


@app.command("update")
def update_templates(
    ctx: typer.Context,
    template_id: Optional[str] = typer.Option(
        None,
        "--id",
        help="Specific template ID to check/update (defaults to all default templates).",
    ),
    check_only: bool = typer.Option(
        False,
        "--check",
        help="Only report available updates without installing.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Install updates without confirmation.",
    ),
    community_url: Optional[str] = typer.Option(
        None,
        "--community-url",
        help="Override community API URL.",
    ),
    community_api_key: Optional[str] = typer.Option(
        None,
        "--community-api-key",
        help="API key for community template catalog.",
    ),
) -> None:
    """Check for and install template updates from the community catalog."""

    template_ids = [template_id] if template_id else None
    checker = TemplateUpdateChecker(
        loader=TemplateLoader(),
        client=_community_client(community_url, community_api_key),
    )
    try:
        updates = checker.check_updates(template_ids=template_ids)
    except TemplateUpdateError as exc:
        typer.secho(f"Update check failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    if not updates:
        payload = {"updates": []}
        if _output_json(ctx):
            typer.echo(json.dumps(payload, indent=2))
        else:
            typer.secho("All default templates are up to date.", fg=typer.colors.GREEN)
        return

    if check_only:
        payload = {"updates": [_serialize_update(candidate) for candidate in updates]}
        if _output_json(ctx):
            typer.echo(json.dumps(payload, indent=2))
        else:
            typer.secho("Updates available:", fg=typer.colors.YELLOW)
            for candidate in updates:
                current = candidate.current_version or "unknown"
                typer.echo(f"- {candidate.template_id}: {current} -> {candidate.latest_version}")
        return

    auto_confirm = yes or _output_json(ctx)
    results: List[dict[str, Any]] = []
    failures = 0
    for candidate in updates:
        if not auto_confirm:
            confirm = typer.confirm(
                f"Update {candidate.template_id} from "
                f"{candidate.current_version or 'unknown'} to {candidate.latest_version}?",
                default=True,
            )
            if not confirm:
                if _output_json(ctx):
                    results.append(
                        {
                            "template_id": candidate.template_id,
                            "status": "skipped",
                        }
                    )
                else:
                    typer.secho(f"Skipped {candidate.template_id}.", fg=typer.colors.YELLOW)
                continue
        try:
            installed_path = checker.apply_update(candidate)
        except TemplateUpdateError as exc:
            failures += 1
            if _output_json(ctx):
                results.append(
                    {
                        "template_id": candidate.template_id,
                        "status": "failed",
                        "error": str(exc),
                    }
                )
            else:
                typer.secho(f"Failed to update {candidate.template_id}: {exc}", fg=typer.colors.RED)
            continue
        if _output_json(ctx):
            results.append(
                {
                    "template_id": candidate.template_id,
                    "status": "updated",
                    "latest_version": candidate.latest_version,
                    "path": str(installed_path),
                }
            )
        else:
            typer.secho(
                f"Updated {candidate.template_id} to version {candidate.latest_version} ({installed_path}).",
                fg=typer.colors.GREEN,
            )
    if _output_json(ctx):
        typer.echo(json.dumps({"results": results}, indent=2))
    if failures:
        raise typer.Exit(code=1)
