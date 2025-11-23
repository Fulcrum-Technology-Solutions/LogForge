from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

import typer

from logforge.core import config as core_config

LOGGER = logging.getLogger(__name__)

app = typer.Typer(help="Manage LogForge systemd service integration.")


@app.command()
def install(
    user: str = typer.Option("logforge", help="System user for the service."),
    group: str = typer.Option("logforge", help="System group for the service."),
    home: Optional[str] = typer.Option(None, help="LOGFORGE_HOME path (defaults to /opt/logforge)."),
    log_dir: Optional[str] = typer.Option(None, help="Log directory (defaults to /var/log/logforge)."),
) -> None:
    """Install LogForge as a systemd service."""
    try:
        import pwd
        import grp
    except ImportError:
        typer.secho("ERROR: systemd integration requires Unix-like system.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if hasattr(os, "geteuid") and os.geteuid() != 0:
        typer.secho("ERROR: This command must be run as root (use sudo).", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    home_path = Path(home) if home else core_config.DEFAULT_LOGFORGE_HOME
    log_path = Path(log_dir) if log_dir else Path("/var/log/logforge")

    typer.echo("Installing LogForge systemd service...")

    # Create user/group if they don't exist
    try:
        pwd.getpwnam(user)
        typer.echo(f"✓ User '{user}' already exists")
    except KeyError:
        typer.echo(f"Creating user '{user}'...")
        subprocess.run(["useradd", "-r", "-s", "/bin/false", "-d", str(home_path), user], check=True)
        typer.echo(f"✓ Created user '{user}'")

    try:
        grp.getgrnam(group)
        typer.echo(f"✓ Group '{group}' already exists")
    except KeyError:
        typer.echo(f"Creating group '{group}'...")
        subprocess.run(["groupadd", "-r", group], check=True)
        typer.echo(f"✓ Created group '{group}'")

    # Create directories
    for directory in [home_path, log_path]:
        directory.mkdir(parents=True, exist_ok=True)
        subprocess.run(["chown", "-R", f"{user}:{group}", str(directory)], check=True)
        typer.echo(f"✓ Created/verified directory: {directory}")

    # Write systemd service file
    service_content = f"""[Unit]
Description=LogForge Synthetic Event Generator
After=network.target

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={home_path}
ExecStart=/usr/local/bin/logforge start --service
Restart=on-failure
RestartSec=10s

# Environment
Environment="LOGFORGE_HOME={home_path}"

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=logforge

[Install]
WantedBy=multi-user.target
"""

    service_path = Path("/etc/systemd/system/logforge.service")
    service_path.write_text(service_content, encoding="utf-8")
    typer.echo(f"✓ Created service file: {service_path}")

    # Reload systemd
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    typer.echo("✓ Reloaded systemd daemon")

    typer.secho("\nService installed successfully!", fg=typer.colors.GREEN)
    typer.echo("\nManage with systemd:")
    typer.echo("  sudo systemctl start logforge")
    typer.echo("  sudo systemctl stop logforge")
    typer.echo("  sudo systemctl status logforge")
    typer.echo("  sudo systemctl enable logforge  # start on boot")
    typer.echo("\nOr use LogForge commands:")
    typer.echo("  sudo logforge service start")
    typer.echo("  sudo logforge service stop")
    typer.echo("  sudo logforge service restart")
    typer.echo("  sudo logforge service status")


@app.command()
def start() -> None:
    """Start the LogForge systemd service."""
    _run_systemctl("start")


@app.command()
def stop() -> None:
    """Stop the LogForge systemd service."""
    _run_systemctl("stop")


@app.command()
def restart() -> None:
    """Restart the LogForge systemd service."""
    _run_systemctl("restart")


@app.command()
def status() -> None:
    """Show status of the LogForge systemd service."""
    _run_systemctl("status", check=False)


def _run_systemctl(action: str, check: bool = True) -> None:
    """Run systemctl command for logforge service."""
    try:
        result = subprocess.run(["systemctl", action, "logforge"], check=check, capture_output=True)
        if result.stdout:
            typer.echo(result.stdout.decode())
        if result.stderr:
            typer.echo(result.stderr.decode(), err=True)
        if check and result.returncode != 0:
            raise typer.Exit(code=result.returncode)
    except FileNotFoundError:
        typer.secho("ERROR: systemctl not found. This command requires systemd.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except subprocess.CalledProcessError as exc:
        raise typer.Exit(code=exc.returncode) from exc

