from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
import typer


@dataclass
class CLIConfig:
    api_url: str
    api_key: Optional[str]
    output: str
    skip_health_check: bool = False
    _health_checked: bool = False


def build_headers(config: CLIConfig) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    return headers


def ensure_api_ready(config: CLIConfig) -> None:
    if config.skip_health_check or config._health_checked:
        return

    health_url = f"{config.api_url}/api/health"
    try:
        response = requests.get(health_url, headers=build_headers(config), timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        typer.secho(f"Management API unavailable: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    payload = response.json()
    healthy = bool(payload.get("healthy", False))
    if not healthy:
        typer.secho("Management API reports unhealthy status; aborting.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config._health_checked = True


def render_output(config: CLIConfig, payload: Any) -> None:
    if config.output == "json":
        typer.echo(json.dumps(payload, indent=2))
        return

    rendered = (
        _render_generators_table(payload)
        or _render_entities_summary(payload)
        or _render_templates_table(payload)
    )
    if rendered:
        typer.echo(rendered)
        return

    typer.echo(json.dumps(payload, indent=2))


def _render_generators_table(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    generators = payload.get("generators")
    if not isinstance(generators, list):
        return None
    if not generators:
        return "No generators found."

    rows: List[List[str]] = []
    headers = ["Name", "State", "Rate (eps)", "Events", "Errors", "Outputs"]
    for generator in generators:
        if not isinstance(generator, dict):
            continue
        stats = generator.get("statistics", {})
        frequency = generator.get("frequency", {})
        row = [
            str(generator.get("name", "")),
            str(generator.get("state", "")),
            str(frequency.get("current_rate", "")),
            str(stats.get("events_generated", "")),
            str(stats.get("errors", "")),
            ", ".join(generator.get("outputs", [])),
        ]
        rows.append(row)
    return _format_table(headers, rows)


def _render_entities_summary(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    required = {"users", "devices", "services"}
    if not required.issubset(payload.keys()):
        return None
    headers = ["Metric", "Value"]
    rows = [
        ["Users", str(payload.get("users", 0))],
        ["Devices", str(payload.get("devices", 0))],
        ["Services", str(payload.get("services", 0))],
    ]
    return _format_table(headers, rows)


def _format_table(headers: List[str], rows: List[List[str]]) -> str:
    if not rows:
        return "No data."
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def _render_row(row: List[str]) -> str:
        return "  ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row))

    lines = [_render_row(headers), "  ".join("-" * width for width in widths)]
    lines.extend(_render_row(row) for row in rows)
    return "\n".join(lines)


def _render_templates_table(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    templates = payload.get("templates")
    if templates is None:
        return None
    if not templates:
        return "No templates found."

    headers = ["ID", "Locations", "Version", "Format"]
    rows: List[List[str]] = []
    for template in templates:
        if not isinstance(template, dict):
            continue
        rows.append(
            [
                str(template.get("id", "")),
                ", ".join(template.get("locations", []) or []),
                str(template.get("version", "") or ""),
                str(template.get("format", "") or ""),
            ]
        )
    return _format_table(headers, rows)

