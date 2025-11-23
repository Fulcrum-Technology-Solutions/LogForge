from __future__ import annotations

import asyncio
import logging
import signal
from pathlib import Path
from typing import Optional

import typer

from logforge import __version__
from logforge.core.config import ConfigError, load_config
from logforge.utils.logging import setup_logging

LOGGER = logging.getLogger(__name__)

app = typer.Typer(help="Start the LogForge service.")


def _start_service(
    service_mode: bool = False,
    config_path: Optional[str] = None,
) -> None:
    """Start the LogForge service with embedded API server."""
    # Lazy import to avoid loading heavy dependencies until command is invoked
    from logforge.api.server import ManagementAPIServer
    
    try:
        from pathlib import Path

        config = load_config(Path(config_path) if config_path else None)
    except ConfigError as exc:
        typer.secho(f"ERROR: Configuration error: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    # Setup logging
    setup_logging(config.logging)

    typer.echo(f"Starting LogForge {__version__}...")
    LOGGER.info("LogForge %s starting...", __version__)

    # Initialize API server (which also initializes engine, registry, templates)
    try:
        api_server = ManagementAPIServer(config)
        typer.echo("✓ Loaded configuration")
        LOGGER.info("Configuration loaded successfully")
    except Exception as exc:
        typer.secho(f"ERROR: Failed to initialize service: {exc}", fg=typer.colors.RED)
        LOGGER.exception("Service initialization failed")
        raise typer.Exit(code=1) from exc

    # Start API server
    api_server.start()
    typer.echo(f"✓ Management API: http://{config.api.host}:{config.api.port}")
    LOGGER.info("Management API started on %s:%s", config.api.host, config.api.port)

    # Setup signal handlers for graceful shutdown
    shutdown_requested = False

    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        LOGGER.info("Received signal %s, initiating shutdown...", signum)
        shutdown_requested = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start enabled generators and run main loop
    async def run_service():
        engine = api_server.context.engine
        enabled_generators = [g for g in config.generators if g.enabled]
        if enabled_generators:
            typer.echo(f"✓ Starting {len(enabled_generators)} enabled generator(s)")
            for gen_config in enabled_generators:
                await engine.start_generator(gen_config.name)
                typer.echo(f"  └─ {gen_config.name}")
                LOGGER.info("Generator '%s' started", gen_config.name)
        else:
            typer.echo("✓ No generators enabled in configuration")

        typer.secho("\nLogForge is running", fg=typer.colors.GREEN)
        typer.echo(f"Management API: http://{config.api.host}:{config.api.port}/api/status")
        if not service_mode:
            typer.echo("Press Ctrl+C to stop\n")

        if service_mode:
            LOGGER.info("Service running in background mode")
        else:
            LOGGER.info("Service running in foreground mode")

        # Main loop - wait for shutdown signal
        while not shutdown_requested:
            await asyncio.sleep(1)

        # Graceful shutdown
        typer.echo("\nShutting down...")
        LOGGER.info("Initiating graceful shutdown")

        # Stop generators
        for gen_config in enabled_generators:
            try:
                await engine.stop_generator(gen_config.name)
                LOGGER.info("Generator '%s' stopped", gen_config.name)
            except Exception as exc:
                LOGGER.warning("Error stopping generator '%s': %s", gen_config.name, exc)

    # Run the service
    try:
        asyncio.run(run_service())
    except KeyboardInterrupt:
        LOGGER.info("Keyboard interrupt received")
        shutdown_requested = True
    finally:
        # Stop API server
        api_server.stop()
        LOGGER.info("Management API stopped")

        # Shutdown outputs
        for output_handler in api_server.context.engine._outputs.values():
            try:
                asyncio.run(output_handler.shutdown())
            except Exception as exc:
                LOGGER.warning("Error shutting down output handler: %s", exc)

        typer.echo("✓ Shutdown complete")
        LOGGER.info("LogForge shutdown complete")


@app.command()
def start(
    service: bool = typer.Option(
        False,
        "--service",
        help="Run in service/daemon mode (for systemd).",
    ),
    config: Optional[str] = typer.Option(
        None,
        "--config",
        help="Override config file path.",
    ),
) -> None:
    """Start the LogForge service with embedded API server."""
    _start_service(service_mode=service, config_path=config)

