"""CLI output helpers."""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

import click
import yaml


def echo_output(data: Any, output: str = "yaml") -> None:
    """Print data according to requested output format."""
    if output == "json":
        click.echo(json.dumps(data, indent=2))
    elif output == "yaml":
        click.echo(yaml.safe_dump(data, sort_keys=False))
    elif output == "table":
        render_table(data)
    else:  # pragma: no cover - defensive
        click.echo(str(data))


def render_table(data: Any) -> None:
    """Render simple table output for dicts or list of dicts."""
    if isinstance(data, Mapping):
        width = max((len(str(key)) for key in data.keys()), default=0)
        for key, value in data.items():
            click.echo(f"{str(key).ljust(width)}  {value}")
        return

    if isinstance(data, Sequence) and data and isinstance(data[0], Mapping):
        headers = list(data[0].keys())
        widths = {header: max(len(str(header)), *(len(str(row.get(header, ""))) for row in data)) for header in headers}
        header_line = "  ".join(str(header).ljust(widths[header]) for header in headers)
        click.echo(header_line)
        click.echo("-" * len(header_line))
        for row in data:
            click.echo("  ".join(str(row.get(header, "")).ljust(widths[header]) for header in headers))
        return

    click.echo(str(data))
