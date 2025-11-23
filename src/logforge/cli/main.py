"""LogForge CLI entry point."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer

from logforge import __version__
from logforge.cli import config, entities, generators, outputs, templates
from logforge.cli.api_client import APIClient
from logforge.core.default_config import DefaultConfigOptions, write_default_config


@dataclass
class CLIContext:
    """Shared options passed to subcommands."""

    api_url: str
    api_key: Optional[str]
    output_format: str
    _client: Optional[APIClient] = None

    def client(self) -> APIClient:
        if self._client is None:
            self._client = APIClient(self.api_url, self.api_key)
        return self._client


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


@app.command("start")
def start_service(
    ctx: typer.Context,
    foreground: bool = typer.Option(False, "--foreground", "-f", help="Run in foreground"),
) -> None:
    """Start the LogForge service."""
    from logforge.core.service import LogForgeService
    from logforge.api.server import APIServer, APISettings, build_dependencies_from_service, create_app

    try:
        service = LogForgeService.from_config_path()
        deps = build_dependencies_from_service(service)
        api_settings = APISettings(
            host=service.config.api.host,
            port=service.config.api.port,
            auth_enabled=service.config.api.auth.enabled,
            api_key=service.config.api.auth.key,
        )
        app = create_app(settings=api_settings, dependencies=deps)
        api_server = APIServer(app, settings=api_settings)

        if foreground:
            typer.echo("Starting LogForge service in foreground...")
            service.start()
            api_server.start()
            try:
                import signal
                import sys

                def signal_handler(sig, frame):
                    typer.echo("\nShutting down...")
                    service.stop()
                    api_server.stop()
                    sys.exit(0)

                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)
                # Keep running
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                signal_handler(None, None)
        else:
            typer.secho("Background service mode not yet implemented", fg=typer.colors.YELLOW)
            typer.echo("Use --foreground to run in foreground mode")
    except Exception as e:
        typer.secho(f"Error starting service: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command("stop")
def stop_service(ctx: typer.Context) -> None:
    """Stop the LogForge service (foreground mode only)."""
    typer.secho("Stop command works only for foreground processes", fg=typer.colors.YELLOW)
    typer.echo("Use Ctrl+C to stop a foreground service")


@app.command("status")
def service_status(ctx: typer.Context) -> None:
    """Show overall service status."""
    client = ctx.obj.client() if ctx.obj else None
    if not client:
        typer.secho("Error: Cannot connect to API", fg=typer.colors.RED)
        raise typer.Exit(1)

    try:
        status_data = client.get("/api/status")
        if ctx.obj and ctx.obj.output_format == "json":
            import json
            typer.echo(json.dumps(status_data, indent=2))
            return

        typer.secho("Service Status", bold=True)
        typer.echo(f"Version: {status_data.get('version', 'N/A')}")
        typer.echo(f"Uptime: {status_data.get('uptime', 0)}s")
        system = status_data.get("system", {})
        typer.echo(f"CPU: {system.get('cpu_percent', 0):.1f}%")
        typer.echo(f"Memory: {system.get('memory_mb', 0):.1f} MB")
        typer.echo(f"Threads: {system.get('threads', 0)}")
        typer.echo(f"\nGenerators:")
        generators = status_data.get("generators", [])
        for gen in generators:
            typer.echo(f"  {gen['name']:20} {gen['state']:>8}  {gen.get('statistics', {}).get('events_generated', 0)} events")
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command("health")
def health_check(ctx: typer.Context) -> None:
    """Comprehensive health check with suggestions."""
    client = ctx.obj.client() if ctx.obj else None
    if not client:
        typer.secho("Error: Cannot connect to API", fg=typer.colors.RED)
        raise typer.Exit(1)

    try:
        health_data = client.get("/api/health")
        if ctx.obj and ctx.obj.output_format == "json":
            import json
            typer.echo(json.dumps(health_data, indent=2))
            return

        status = health_data.get("status", "unknown")
        color = typer.colors.GREEN if status == "healthy" else typer.colors.YELLOW if status == "degraded" else typer.colors.RED
        typer.secho(f"Status: {status.upper()}", fg=color, bold=True)
        gens = health_data.get("generators", {})
        typer.echo(f"Generators: {gens.get('total', 0)} total, {gens.get('running', 0)} running, "
                   f"{gens.get('degraded', 0)} degraded, {gens.get('error', 0)} error")
        typer.echo(f"Entity Registry: {health_data.get('entity_registry', 'unknown')}")
        typer.echo(f"Template Cache: {health_data.get('template_cache', 'unknown')}")
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command("generate")
def generate_once(
    ctx: typer.Context,
    template: str = typer.Argument(..., help="Template ID to use"),
    count: int = typer.Option(1, "--count", "-n", help="Number of events to generate"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file (default: stdout)"),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json, plain)"),
) -> None:
    """Generate events without starting the service (one-shot mode)."""
    from logforge.core.service import LogForgeService
    from logforge.outputs.console import ConsoleOutput
    from logforge.outputs.base import RetryPolicy
    import sys

    try:
        service = LogForgeService.from_config_path()
        renderer = service.template_renderer

        # Create output
        if output:
            from logforge.outputs.file import FileOutput
            from pathlib import Path
            out_handler = FileOutput(
                "one_shot",
                path_template=output,
                generator_name="one_shot",
                retry_policy=RetryPolicy(max_attempts=1, retry_interval=1, backoff_multiplier=1.0, max_backoff=1),
                buffer_size=0,
            )
        else:
            stream = sys.stdout if format == "plain" else sys.stdout
            out_handler = ConsoleOutput(
                "one_shot",
                stream=stream,
                format=format,
                retry_policy=RetryPolicy(max_attempts=1, retry_interval=1, backoff_multiplier=1.0, max_backoff=1),
                buffer_size=0,
            )

        # Generate events
        for i in range(count):
            try:
                event = renderer.render(template, {"generator": "one_shot"})
                from datetime import datetime, timezone
                metadata = {
                    "generator": "one_shot",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                out_handler.emit(event, metadata)
            except Exception as e:
                typer.secho(f"Error generating event {i+1}: {e}", fg=typer.colors.RED)
                raise typer.Exit(1)

        if output:
            typer.echo(f"Generated {count} event(s) to {output}")
        else:
            typer.echo(f"Generated {count} event(s)", file=sys.stderr)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


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
