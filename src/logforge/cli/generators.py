"""Generator CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import typer

from logforge.cli.api_client import APIClient

app = typer.Typer(help="Control event generators.")


def _client(ctx: typer.Context) -> APIClient:
    if ctx.obj is None:
        raise typer.BadParameter("CLI context missing; run through `logforge` entrypoint.")
    return ctx.obj.client()


def _output_json(ctx: typer.Context) -> bool:
    return bool(getattr(ctx.obj, "output_format", "table") == "json")


def _print_status(ctx: typer.Context, status: Dict[str, Any]) -> None:
    if _output_json(ctx):
        typer.echo(json.dumps(status, indent=2))
        return
    typer.secho(f"{status['name']} [{status['state']}]", bold=True)
    typer.echo(f"Template : {status['template']}")
    typer.echo(f"Outputs  : {', '.join(status['outputs'])}")
    stats = status.get("statistics", {})
    typer.echo(
        f"Events: {stats.get('events_generated', 0)}  Errors: {stats.get('errors', 0)}  "
        f"Uptime: {round(stats.get('uptime', 0.0), 2)}s"
    )


@app.command("list")
def list_generators(ctx: typer.Context) -> None:
    """List all generators and their states."""
    response = _client(ctx).get("/api/generators")
    if _output_json(ctx):
        typer.echo(json.dumps(response, indent=2))
        return
    if not response:
        typer.echo("No generators found.")
        return
    for generator in response:
        typer.echo(f"{generator['name']:20} {generator['state']:>8}  {generator['template']}")


@app.command("status")
def generator_status(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Show detailed status for a generator."""
    status = _client(ctx).get(f"/api/generators/{name}")
    _print_status(ctx, status)


@app.command("start")
def start_generator(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Start a generator."""
    status = _client(ctx).post(f"/api/generators/{name}/start", {})
    _print_status(ctx, status)


@app.command("stop")
def stop_generator(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Stop a running generator."""
    status = _client(ctx).post(f"/api/generators/{name}/stop", {})
    _print_status(ctx, status)


@app.command("restart")
def restart_generator(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Restart a generator."""
    status = _client(ctx).post(f"/api/generators/{name}/restart", {})
    _print_status(ctx, status)


@app.command("metrics")
def generator_metrics(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Show detailed metrics for a generator."""
    status = _client(ctx).get(f"/api/generators/{name}")
    if _output_json(ctx):
        typer.echo(json.dumps(status, indent=2))
        return

    stats = status.get("statistics", {})
    freq = status.get("frequency", {})
    typer.secho(f"Metrics for {status['name']}", bold=True)
    typer.echo(f"\nGeneration:")
    typer.echo(f"  Events Generated: {stats.get('events_generated', 0)}")
    typer.echo(f"  Errors: {stats.get('errors', 0)}")
    typer.echo(f"  Uptime: {round(stats.get('uptime', 0.0), 2)}s")
    typer.echo(f"  Last Event: {stats.get('last_event', 'Never')}")
    typer.echo(f"\nFrequency:")
    typer.echo(f"  Base Rate: {freq.get('base_rate', 0)} events/sec")
    typer.echo(f"  Current Rate: {freq.get('current_rate', 0)} events/sec")
    typer.echo(f"\nConfiguration:")
    typer.echo(f"  Template: {status.get('template', 'N/A')}")
    typer.echo(f"  Outputs: {', '.join(status.get('outputs', []))}")
    typer.echo(f"  Enabled: {status.get('enabled', False)}")


@app.command("enable")
def enable_generator(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Enable a generator (does not start it)."""
    # TODO: Implement enable/disable API endpoint
    typer.secho("Enable/disable functionality requires API support", fg=typer.colors.YELLOW)
    typer.echo(f"Generator '{name}' enable requested (not yet implemented)")


@app.command("disable")
def disable_generator(ctx: typer.Context, name: str = typer.Argument(...)) -> None:
    """Disable a generator (stops it if running)."""
    # TODO: Implement enable/disable API endpoint
    typer.secho("Enable/disable functionality requires API support", fg=typer.colors.YELLOW)
    typer.echo(f"Generator '{name}' disable requested (not yet implemented)")


@app.command("validate")
def validate_generator_config(
    ctx: typer.Context,
    config_file: Path = typer.Argument(..., help="Path to generator YAML config file"),
) -> None:
    """Validate a generator configuration file."""
    import yaml
    from logforge.core.config_schema import GeneratorConfig

    try:
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            for idx, gen_config in enumerate(data):
                try:
                    GeneratorConfig.model_validate(gen_config)
                    typer.echo(f"Generator {idx + 1}: ✓ Valid")
                except Exception as e:
                    typer.secho(f"Generator {idx + 1}: ✗ Invalid - {e}", fg=typer.colors.RED)
        else:
            GeneratorConfig.model_validate(data)
            typer.echo("✓ Configuration is valid")
    except FileNotFoundError:
        typer.secho(f"Error: File not found: {config_file}", fg=typer.colors.RED)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command("add")
def add_generator(ctx: typer.Context) -> None:
    """Interactively create a new generator."""
    # TODO: Implement interactive generator creation
    typer.secho("Interactive generator creation not yet implemented", fg=typer.colors.YELLOW)
    typer.echo("Use 'logforge generators apply <config.yaml>' to add generators from a file")


@app.command("apply")
def apply_generators(
    ctx: typer.Context,
    config_file: Path = typer.Argument(..., help="Path to generator YAML config file"),
) -> None:
    """Create or update generators from a YAML configuration file."""
    import yaml
    from logforge.core.config_schema import GeneratorConfig

    try:
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)

        generators = data if isinstance(data, list) else [data]
        client = _client(ctx)

        for gen_data in generators:
            try:
                gen_config = GeneratorConfig.model_validate(gen_data)
                # TODO: Implement POST /api/generators endpoint for creating generators
                typer.secho(
                    f"Generator '{gen_config.name}' apply requested (API endpoint not yet implemented)",
                    fg=typer.colors.YELLOW,
                )
            except Exception as e:
                typer.secho(f"Error validating generator: {e}", fg=typer.colors.RED)
                raise typer.Exit(1)
    except FileNotFoundError:
        typer.secho(f"Error: File not found: {config_file}", fg=typer.colors.RED)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command("reload")
def reload_generators(ctx: typer.Context) -> None:
    """Reload generator configuration from config.yaml."""
    # TODO: Implement reload API endpoint
    typer.secho("Reload functionality requires API support", fg=typer.colors.YELLOW)
    typer.echo("Reload requested (not yet implemented)")
