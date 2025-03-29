"""Command-line interface for the synthetic log generator."""

import logging
import os
import sys
import time
from typing import List, Optional

import click
import yaml

from synth_logs.core.engine import Engine
from synth_logs.outputs.stdout import StdoutAdapter
from synth_logs.outputs.file import FileAdapter
from synth_logs.outputs.http import HttpAdapter


def configure_logging(verbose: bool):
    """Configure logging for the application.
    
    Args:
        verbose: Whether to enable verbose logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def load_config(config_path: str) -> dict:
    """Load configuration from a file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        The configuration as a dictionary
    """
    if not os.path.exists(config_path):
        click.echo(f"Configuration file not found: {config_path}", err=True)
        sys.exit(1)
        
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        return config or {}
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


def setup_engine(config: dict) -> Engine:
    """Set up the engine based on configuration.
    
    Args:
        config: The configuration dictionary
        
    Returns:
        The configured engine
    """
    engine = Engine()
    
    # Load entity registry if specified
    if 'entity_registry' in config:
        registry_file = config['entity_registry']
        if os.path.exists(registry_file):
            engine.registry.load_from_file(registry_file)
        else:
            click.echo(f"Entity registry file not found: {registry_file}", err=True)
            
    # Configure outputs
    outputs_config = config.get('outputs', [])
    for output_config in outputs_config:
        output_type = output_config.get('type')
        name = output_config.get('name', output_type)
        
        if output_type == 'stdout':
            engine.add_output(StdoutAdapter(name=name))
        elif output_type == 'file':
            file_path = output_config.get('file_path')
            if not file_path:
                click.echo(f"Missing file_path for file output: {name}", err=True)
                continue
                
            max_size = output_config.get('max_size')
            backup_count = output_config.get('backup_count', 5)
            hourly_rotation = output_config.get('hourly_rotation', True)
            data_source_field = output_config.get('data_source_field')
            
            engine.add_output(FileAdapter(
                file_path=file_path,
                name=name,
                max_size=max_size,
                backup_count=backup_count,
                hourly_rotation=hourly_rotation,
                data_source_field=data_source_field
            ))
        elif output_type == 'http':
            url = output_config.get('url')
            if not url:
                click.echo(f"Missing URL for HTTP output: {name}", err=True)
                continue
                
            method = output_config.get('method', 'POST')
            headers = output_config.get('headers', {})
            retry_count = output_config.get('retry_count', 3)
            retry_delay = output_config.get('retry_delay', 1.0)
            timeout = output_config.get('timeout', 10.0)
            verify_ssl = output_config.get('verify_ssl', True)
            
            engine.add_output(HttpAdapter(
                url=url,
                name=name,
                method=method,
                headers=headers,
                retry_count=retry_count,
                retry_delay=retry_delay,
                timeout=timeout,
                verify_ssl=verify_ssl
            ))
        else:
            click.echo(f"Unknown output type: {output_type}", err=True)
            
    # Configure time patterns
    patterns_config = config.get('time_patterns', [])
    for pattern_config in patterns_config:
        name = pattern_config.get('name')
        if not name:
            click.echo(f"Missing name for time pattern", err=True)
            continue
            
        from synth_logs.core.scheduler import TimePattern, DayOfWeek
        
        # Convert day names to DayOfWeek enum values
        days_of_week = None
        if 'days_of_week' in pattern_config:
            days_of_week = []
            for day in pattern_config['days_of_week']:
                try:
                    days_of_week.append(DayOfWeek[day.upper()])
                except KeyError:
                    click.echo(f"Invalid day of week: {day}", err=True)
                    
        # Create the time pattern
        engine.scheduler.add_pattern(TimePattern(
            name=name,
            base_frequency=pattern_config.get('base_frequency', 1.0),
            start_time=pattern_config.get('start_time', '00:00'),
            end_time=pattern_config.get('end_time', '23:59'),
            days_of_week=days_of_week,
            multiplier=pattern_config.get('multiplier', 1.0)
        ))
        
    return engine


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """Synthetic log generator."""
    configure_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--config', '-c', required=True, type=click.Path(exists=True), 
              help='Path to configuration file')
@click.pass_context
def run(ctx, config):
    """Run the log generator."""
    click.echo("Starting synthetic log generator...")
    
    # Load configuration
    config_data = load_config(config)
    
    # Set up the engine
    engine = setup_engine(config_data)
    
    # Discover packages
    engine.discover_packages()
    
    # Start all generators that are configured to be active
    active_generators = config_data.get('active_generators', [])
    for generator_name in active_generators:
        if generator_name in engine.generators:
            engine.generators[generator_name].active = True
        else:
            click.echo(f"Generator not found: {generator_name}", err=True)
            
    # Start the engine
    engine.start()
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\nStopping...")
    finally:
        # Stop the engine
        engine.stop()
        
        # Close all outputs
        for output in engine.outputs:
            output.close()
            
    click.echo("Stopped.")


@cli.command()
@click.option('--config', '-c', required=True, type=click.Path(exists=True), 
              help='Path to configuration file')
@click.pass_context
def list_generators(ctx, config):
    """List available log generators."""
    # Load configuration
    config_data = load_config(config)
    
    # Set up the engine
    engine = setup_engine(config_data)
    
    # Discover packages
    engine.discover_packages()
    
    # List generators
    click.echo("Available log generators:")
    for name in sorted(engine.generators.keys()):
        click.echo(f"  - {name}")


@cli.command()
@click.option('--user', '-u', default=None, help='User to run the service as')
@click.option('--output', '-o', default='/etc/systemd/system/logforge.service',
              help='Path to output the service file')
@click.option('--config', '-c', required=True, type=click.Path(), 
              help='Path to configuration file (absolute path)')
@click.option('--description', '-d', default='Synthetic Log Generator Service',
              help='Description for the service')
@click.pass_context
def create_service(ctx, user, output, config, description):
    """Create a systemd service file for the log generator."""
    # Validate config path
    if not os.path.isabs(config):
        click.echo("Config path must be absolute for systemd service", err=True)
        sys.exit(1)
    
    # Get the executable path
    executable = sys.executable
    
    # Get the script path
    script_path = os.path.abspath(sys.argv[0])
    
    # Create the service file content
    service_content = f"""[Unit]
Description={description}
After=network.target

[Service]
Type=simple
ExecStart={executable} {script_path} run --config {config}
Restart=on-failure
"""

    # Add user if specified
    if user:
        service_content += f"User={user}\n"
    
    service_content += """
[Install]
WantedBy=multi-user.target
"""

    # Write the service file
    try:
        with open(output, 'w') as f:
            f.write(service_content)
        
        click.echo(f"Service file created at {output}")
        click.echo("\nTo control the service:")
        click.echo("  sudo systemctl daemon-reload")
        click.echo("  sudo systemctl enable logforge.service")
        click.echo("  sudo systemctl start logforge.service")
        click.echo("  sudo systemctl status logforge.service")
        click.echo("  sudo systemctl stop logforge.service")
    except Exception as e:
        click.echo(f"Error creating service file: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == '__main__':
    main()