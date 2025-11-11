from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import click
import yaml

from logforge.cli.utils import APIClient, APIClientError, echo_api_error, render_output


@click.group()
@click.pass_context
def templates(ctx: click.Context) -> None:
    """Template management commands."""
    ctx.ensure_object(dict)


@templates.command("list")
@click.option("--output", type=click.Choice(["table", "json"], case_sensitive=False), default="table")
@click.pass_context
def list_templates(ctx: click.Context, output: str) -> None:
    client: APIClient = ctx.obj["api_client"]
    try:
        payload = client.get("/api/templates")
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    columns = [
        ("id", "ID"),
        ("name", "NAME"),
        ("location", "LOCATION"),
        ("version", "VERSION"),
        ("overrides", "OVERRIDES"),
    ]
    click.echo(render_output(payload, output, columns=columns if output.lower() == "table" else None))


@templates.command("search")
@click.argument("query", required=False)
@click.option("--vendor", type=str, default=None)
@click.option("--output", type=click.Choice(["table", "json"], case_sensitive=False), default="table")
@click.pass_context
def search_templates(ctx: click.Context, query: Optional[str], vendor: Optional[str], output: str) -> None:
    client: APIClient = ctx.obj["api_client"]
    params = {}
    if query:
        params["q"] = query
    if vendor:
        params["vendor"] = vendor
    try:
        payload = client.get("/api/templates/search", params=params)
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    columns = [
        ("id", "ID"),
        ("name", "NAME"),
        ("vendor", "VENDOR"),
        ("version", "VERSION"),
    ]
    click.echo(render_output(payload, output, columns=columns if output.lower() == "table" else None))


@templates.command("info")
@click.argument("template_id", type=str)
@click.pass_context
def template_info(ctx: click.Context, template_id: str) -> None:
    client: APIClient = ctx.obj["api_client"]
    try:
        payload = client.get(f"/api/templates/{template_id}")
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    click.echo(yaml.safe_dump(payload, sort_keys=False))


@templates.command("install")
@click.argument("template_id", type=str)
@click.pass_context
def install_template(ctx: click.Context, template_id: str) -> None:
    client: APIClient = ctx.obj["api_client"]
    try:
        payload = client.post("/api/templates/install", json_body={"template_id": template_id})
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    click.echo(f"Installed template {template_id}")
    click.echo(yaml.safe_dump(payload, sort_keys=False))


@templates.command("validate")
@click.option("--template-id", type=str, default=None)
@click.option("--file", "file_path", type=click.Path(path_type=Path), default=None)
@click.pass_context
def validate_template(ctx: click.Context, template_id: Optional[str], file_path: Optional[Path]) -> None:
    client: APIClient = ctx.obj["api_client"]
    if template_id:
        endpoint = f"/api/templates/{template_id}/validate"
        try:
            payload = client.post(endpoint, json_body={})
        except APIClientError as exc:
            echo_api_error(exc)
            raise click.Abort()
        click.echo(yaml.safe_dump(payload, sort_keys=False))
        return
    if file_path:
        try:
            payload = client.post("/api/templates/validate", json_body={"path": str(file_path)})
        except APIClientError as exc:
            echo_api_error(exc)
            raise click.Abort()
        click.echo(yaml.safe_dump(payload, sort_keys=False))
        return
    raise click.ClickException("Provide either --template-id or --file")


@templates.command("customize")
@click.argument("template_id", type=str)
@click.pass_context
def customize_template(ctx: click.Context, template_id: str) -> None:
    client: APIClient = ctx.obj["api_client"]
    try:
        payload = client.post(f"/api/templates/{template_id}/customize", json_body={})
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    click.echo(f"Customized template {template_id}")
    click.echo(yaml.safe_dump(payload, sort_keys=False))


@templates.command("diff")
@click.argument("template_id", type=str)
@click.pass_context
def diff_template(ctx: click.Context, template_id: str) -> None:
    client: APIClient = ctx.obj["api_client"]
    try:
        payload = client.get(f"/api/templates/{template_id}/diff")
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    click.echo(payload.get("diff", ""))


@templates.command("revert")
@click.argument("template_id", type=str)
@click.pass_context
def revert_template(ctx: click.Context, template_id: str) -> None:
    client: APIClient = ctx.obj["api_client"]
    try:
        client.request("DELETE", f"/api/templates/{template_id}/custom")
    except APIClientError as exc:
        echo_api_error(exc)
        raise click.Abort()
    click.echo(f"Reverted custom template {template_id}")
