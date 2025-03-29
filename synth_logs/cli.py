"""Command-line interface for the synthetic log generator."""

import logging
import logging.handlers
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
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.getcwd(), 'app_logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up log level based on verbose flag
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create rotating file handler for detailed logs
    log_file = os.path.join(log_dir, 'logforge.log')
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Create console handler for important logs only (warning and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup information
    logging.info(f"Logging initialized. Log file: {log_file}")
    if verbose:
        logging.info("Verbose logging enabled (DEBUG level)")
    else:
        logging.info("Normal logging level (INFO level)")


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
    
    # If no outputs are configured, add a default file output
    if not outputs_config:
        click.echo("No outputs configured in config file. Adding default file output.")
        
        # Create a default output configuration
        default_output = {
            "type": "file",
            "name": "default_file_output",
            "file_path": "logs/synth_logs.json",
            "hourly_rotation": True,
            "data_source_field": "generator"
        }
        
        # Add it to the engine
        engine.add_output(FileAdapter(
            file_path=default_output["file_path"],
            name=default_output["name"],
            hourly_rotation=default_output["hourly_rotation"],
            data_source_field=default_output["data_source_field"]
        ))
        
        # Add it to the configuration so it will be saved
        config.setdefault('outputs', []).append(default_output)
        
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


@cli.command()
@click.option('--config', '-c', required=True, type=click.Path(exists=True), 
              help='Path to configuration file')
@click.pass_context
def configure(ctx, config):
    """Interactive configuration tool for the log generator."""
    from synth_logs.core.templates import TemplateManager
    
    # Load the current configuration
    config_data = load_config(config)
    
    # Create a template manager
    template_manager = TemplateManager()
    
    # Discover available templates
    templates = template_manager.discover_templates()
    
    # Get currently active generators
    active_generators = config_data.get('active_generators', [])
    
    # Create and set up the engine once
    engine = setup_engine(config_data)
    click.echo("Discovering generators...")
    engine.discover_packages()
    
    while True:
        click.clear()
        click.echo(click.style("🪵 Logforge Configuration Menu", fg='green', bold=True))
        click.echo(click.style("=" * 50, fg='green'))
        click.echo("")
        
        # Display active generators
        click.echo(click.style("Active Generators:", fg='blue', bold=True))
        if active_generators:
            for i, generator in enumerate(active_generators, 1):
                click.echo(f"{i}. {generator}")
        else:
            click.echo("  No active generators")
        
        click.echo("")
        # Get current outputs
        outputs = config_data.get('outputs', [])
        
        # Display active outputs
        click.echo(click.style("Active Outputs:", fg='blue', bold=True))
        if outputs:
            for i, output in enumerate(outputs, 1):
                click.echo(f"{i}. {output.get('name', 'unnamed')} ({output.get('type', 'unknown')})")
        else:
            click.echo("  No active outputs")
            
        click.echo("")
        click.echo(click.style("Options:", fg='yellow'))
        click.echo("1. Add generator")
        click.echo("2. Remove generator")
        click.echo("3. Configure outputs")
        click.echo("4. Start/stop generators")
        click.echo("5. Save configuration")
        click.echo("6. Exit")
        
        choice = click.prompt("Select an option", type=int, default=1)
        
        if choice == 1:
            # Add generator
            add_generator_menu(templates, active_generators)
        elif choice == 2:
            # Remove generator
            if active_generators:
                remove_generator_menu(active_generators)
            else:
                click.echo("No generators to remove.")
                click.pause()
        elif choice == 3:
            # Configure outputs
            outputs = configure_outputs_menu(outputs)
            config_data['outputs'] = outputs
            
            # Save the configuration
            try:
                with open(config, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
                click.echo(click.style("Configuration updated with new outputs!", fg='green'))
                click.pause()
            except Exception as e:
                click.echo(click.style(f"Error saving configuration: {e}", fg='red'))
                click.pause()
        elif choice == 4:
            # Start/stop generators
            if active_generators:
                start_stop_generators_menu(config, active_generators, engine)
            else:
                click.echo("No generators configured. Please add generators first.")
                click.pause()
        elif choice == 5:
            # Save configuration
            config_data['active_generators'] = active_generators
            
            try:
                with open(config, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
                click.echo(click.style("Configuration saved successfully!", fg='green'))
            except Exception as e:
                click.echo(click.style(f"Error saving configuration: {e}", fg='red'))
                
            click.pause()
        elif choice == 6:
            # Exit
            config_changed = (config_data.get('active_generators') != active_generators) or (config_data.get('outputs') != outputs)
            if config_changed:
                save = click.confirm("Configuration has changed. Save before exiting?", default=True)
                if save:
                    config_data['active_generators'] = active_generators
                    config_data['outputs'] = outputs
                    try:
                        with open(config, 'w') as f:
                            yaml.dump(config_data, f, default_flow_style=False)
                        click.echo(click.style("Configuration saved successfully!", fg='green'))
                    except Exception as e:
                        click.echo(click.style(f"Error saving configuration: {e}", fg='red'))
            break
        else:
            click.echo("Invalid option.")
            click.pause()


def add_generator_menu(templates, active_generators):
    """Display a menu for adding generators.
    
    Args:
        templates: Dictionary of available templates
        active_generators: List of active generators
    """
    config_modified = False
    
    while True:
        click.clear()
        click.echo(click.style("Add Generator", fg='green', bold=True))
        click.echo(click.style("=" * 50, fg='green'))
        click.echo("")
        
        # Display available vendors
        click.echo(click.style("Available Vendors:", fg='blue', bold=True))
        vendors = list(templates.keys())
        for i, vendor in enumerate(vendors, 1):
            click.echo(f"{i}. {vendor}")
            
        click.echo("")
        click.echo("0. Back")
        
        choice = click.prompt("Select a vendor", type=int, default=0)
        
        if choice == 0:
            # Auto-save the config if modified
            if config_modified:
                save_configuration()
            return
        elif 1 <= choice <= len(vendors):
            vendor = vendors[choice - 1]
            if select_product_menu(vendor, templates[vendor], active_generators):
                config_modified = True
        else:
            click.echo("Invalid option.")
            click.pause()


def select_product_menu(vendor, products, active_generators):
    """Display a menu for selecting a product.
    
    Args:
        vendor: Vendor name
        products: Dictionary of available products for the vendor
        active_generators: List of active generators
        
    Returns:
        True if generators were modified, False otherwise
    """
    modified = False
    
    while True:
        click.clear()
        click.echo(click.style(f"Select {vendor} Product", fg='green', bold=True))
        click.echo(click.style("=" * 50, fg='green'))
        click.echo("")
        
        # Display available products
        click.echo(click.style("Available Products:", fg='blue', bold=True))
        product_names = list(products.keys())
        for i, product_name in enumerate(product_names, 1):
            click.echo(f"{i}. {product_name}")
            
        click.echo("")
        click.echo("0. Back")
        
        choice = click.prompt("Select a product", type=int, default=0)
        
        if choice == 0:
            # Auto-save if modified
            if modified:
                save_configuration()
            return modified
        elif 1 <= choice <= len(product_names):
            product = product_names[choice - 1]
            if select_template_menu(vendor, product, products[product], active_generators):
                modified = True
        else:
            click.echo("Invalid option.")
            click.pause()
            
    return modified


def select_template_menu(vendor, product, templates, active_generators):
    """Display a menu for selecting a template.
    
    Args:
        vendor: Vendor name
        product: Product name
        templates: List of available templates for the product
        active_generators: List of active generators
        
    Returns:
        True if generators were modified, False otherwise
    """
    modified = False
    
    while True:
        click.clear()
        click.echo(click.style(f"Select {vendor} {product} Template", fg='green', bold=True))
        click.echo(click.style("=" * 50, fg='green'))
        click.echo("")
        
        # Map generator names from template metadata
        # Example: microsoft_windows_security_login_success
        template_to_generator = {}
        for template in templates:
            metadata = template.get('metadata', {})
            path_parts = template['path'].split('/')
            
            # Get components from metadata if available, fallback to path parts
            vendor = metadata.get('vendor', '').lower() or path_parts[0]
            product = metadata.get('product', '').lower() or (path_parts[1] if len(path_parts) > 1 else '')
            
            # Get data source from metadata or filename
            data_source = metadata.get('data_source', '').lower().replace(' ', '_')
            if not data_source:
                # Extract from filename
                filename = os.path.basename(template['path'])
                data_source = os.path.splitext(filename)[0]
            
            # Construct full generator name (vendor_product_data_source)
            full_generator = f"{vendor}_{product}_{data_source}"
            # Clean up name (remove special chars)
            generator_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in full_generator)
            
            template_to_generator[template['path']] = generator_name
        
        # Display available templates
        click.echo(click.style("Available Templates:", fg='blue', bold=True))
        for i, template in enumerate(templates, 1):
            generator_name = template_to_generator.get(template['path'], '')
            
            # Check if the generator is already active
            status = "[Active]" if generator_name in active_generators else ""
            
            click.echo(f"{i}. {template['data_source']} {status}")
            click.echo(f"   Description: {template['description']}")
            click.echo(f"   Generator: {generator_name}")
            click.echo("")
            
        click.echo("0. Back")
        
        choice = click.prompt("Select a template", type=int, default=0)
        
        if choice == 0:
            # Auto-save if modified
            if modified:
                save_configuration()
            return modified
        elif 1 <= choice <= len(templates):
            template = templates[choice - 1]
            generator_name = template_to_generator.get(template['path'], '')
            
            if not generator_name:
                click.echo("Could not determine generator name for this template.")
                click.pause()
                continue
                
            # Check if the generator is already active
            if generator_name in active_generators:
                click.echo(f"Generator '{generator_name}' is already active.")
                click.pause()
                continue
                
            # Add the generator
            active_generators.append(generator_name)
            click.echo(click.style(f"Added generator: {generator_name}", fg='green'))
            
            # Save configuration immediately
            save_configuration()
            
            click.pause()
            return True
        else:
            click.echo("Invalid option.")
            click.pause()
            
    return modified


def remove_generator_menu(active_generators):
    """Display a menu for removing generators.
    
    Args:
        active_generators: List of active generators
    """
    click.clear()
    click.echo(click.style("Remove Generator", fg='green', bold=True))
    click.echo(click.style("=" * 50, fg='green'))
    click.echo("")
    
    # Display active generators
    click.echo(click.style("Active Generators:", fg='blue', bold=True))
    for i, generator in enumerate(active_generators, 1):
        click.echo(f"{i}. {generator}")
        
    click.echo("")
    click.echo("0. Back")
    
    choice = click.prompt("Select a generator to remove", type=int, default=0)
    
    if choice == 0:
        return
    elif 1 <= choice <= len(active_generators):
        generator = active_generators[choice - 1]
        active_generators.remove(generator)
        click.echo(click.style(f"Removed generator: {generator}", fg='green'))
        
        # Save configuration immediately
        save_configuration()
        
        click.pause()
    else:
        click.echo("Invalid option.")
        click.pause()


def configure_outputs_menu(outputs):
    """Display a menu for configuring outputs.
    
    Args:
        outputs: List of current outputs
        
    Returns:
        Updated list of outputs
    """
    # Make a deep copy of outputs to avoid modifying the original unexpectedly
    import copy
    outputs = copy.deepcopy(outputs)
    while True:
        click.clear()
        click.echo(click.style("Configure Outputs", fg='green', bold=True))
        click.echo(click.style("=" * 50, fg='green'))
        click.echo("")
        
        # Display active outputs
        click.echo(click.style("Active Outputs:", fg='blue', bold=True))
        if outputs:
            for i, output in enumerate(outputs, 1):
                click.echo(f"{i}. {output.get('name', 'unnamed')} ({output.get('type', 'unknown')})")
        else:
            click.echo("  No active outputs")
            
        click.echo("")
        click.echo(click.style("Options:", fg='yellow'))
        click.echo("1. Add output")
        click.echo("2. Edit output")
        click.echo("3. Remove output") 
        click.echo("4. Save changes")
        click.echo("0. Back")
        
        choice = click.prompt("Select an option", type=int, default=0)
        
        if choice == 0:
            if click.confirm("Save changes before returning?", default=True):
                click.echo(click.style("Changes saved!", fg='green'))
                click.pause()
            return outputs
        elif choice == 1:
            # Add output
            new_output = add_output_menu()
            if new_output:
                outputs.append(new_output)
        elif choice == 2:
            # Edit output
            if outputs:
                edit_output_menu(outputs)
            else:
                click.echo("No outputs to edit.")
                click.pause()
        elif choice == 3:
            # Remove output
            if outputs:
                remove_output_menu(outputs)
            else:
                click.echo("No outputs to remove.")
                click.pause()
        elif choice == 4:
            # Just show a confirmation - actual save happens in the main menu
            click.echo(click.style("Changes will be saved when you return to the main menu.", fg='green'))
            click.pause()
        else:
            click.echo("Invalid option.")
            click.pause()


def add_output_menu():
    """Display a menu for adding an output.
    
    Returns:
        Dictionary representing the new output, or None if cancelled
    """
    click.clear()
    click.echo(click.style("Add Output", fg='green', bold=True))
    click.echo(click.style("=" * 50, fg='green'))
    click.echo("")
    
    # Choose output type
    click.echo(click.style("Output Types:", fg='blue', bold=True))
    click.echo("1. Console (stdout)")
    click.echo("2. File")
    click.echo("3. HTTP")
    click.echo("0. Cancel")
    
    choice = click.prompt("Select output type", type=int, default=0)
    
    if choice == 0:
        return None
    elif choice == 1:
        # Console output
        output = configure_stdout_output()
    elif choice == 2:
        # File output
        output = configure_file_output()
    elif choice == 3:
        # HTTP output
        output = configure_http_output()
    else:
        click.echo("Invalid option.")
        click.pause()
        return None
        
    return output


def configure_stdout_output():
    """Configure a stdout output.
    
    Returns:
        Dictionary representing the stdout output
    """
    click.clear()
    click.echo(click.style("Configure Console Output", fg='green', bold=True))
    click.echo(click.style("=" * 50, fg='green'))
    click.echo("")
    
    name = click.prompt("Output name", default="console")
    
    return {
        "type": "stdout",
        "name": name
    }


def configure_file_output():
    """Configure a file output.
    
    Returns:
        Dictionary representing the file output
    """
    click.clear()
    click.echo(click.style("Configure File Output", fg='green', bold=True))
    click.echo(click.style("=" * 50, fg='green'))
    click.echo("")
    
    name = click.prompt("Output name", default="file_output")
    file_path = click.prompt("File path", default="logs/synth_logs.json")
    max_size = click.prompt("Max file size in bytes (0 for no limit)", default=0, type=int)
    backup_count = click.prompt("Number of backup files to keep", default=5, type=int)
    hourly_rotation = click.confirm("Enable hourly rotation?", default=True)
    data_source_field = click.prompt("Data source field for file separation (empty for none)", default="generator")
    
    output = {
        "type": "file",
        "name": name,
        "file_path": file_path,
        "backup_count": backup_count,
        "hourly_rotation": hourly_rotation,
    }
    
    if max_size > 0:
        output["max_size"] = max_size
        
    if data_source_field:
        output["data_source_field"] = data_source_field
        
    return output


def configure_http_output():
    """Configure an HTTP output.
    
    Returns:
        Dictionary representing the HTTP output
    """
    click.clear()
    click.echo(click.style("Configure HTTP Output", fg='green', bold=True))
    click.echo(click.style("=" * 50, fg='green'))
    click.echo("")
    
    name = click.prompt("Output name", default="http_output")
    url = click.prompt("URL", default="http://localhost:8080/api/logs")
    method = click.prompt("HTTP method", default="POST")
    retry_count = click.prompt("Retry count", default=3, type=int)
    retry_delay = click.prompt("Retry delay (seconds)", default=1.0, type=float)
    
    # Headers
    headers = {}
    click.echo("\nConfigure Headers (leave name empty to finish):")
    while True:
        header_name = click.prompt("Header name", default="")
        if not header_name:
            break
            
        header_value = click.prompt("Header value")
        headers[header_name] = header_value
    
    output = {
        "type": "http",
        "name": name,
        "url": url,
        "method": method,
        "retry_count": retry_count,
        "retry_delay": retry_delay
    }
    
    if headers:
        output["headers"] = headers
        
    return output


def edit_output_menu(outputs):
    """Display a menu for editing an output.
    
    Args:
        outputs: List of outputs to edit
    """
    click.clear()
    click.echo(click.style("Edit Output", fg='green', bold=True))
    click.echo(click.style("=" * 50, fg='green'))
    click.echo("")
    
    # Display active outputs
    click.echo(click.style("Active Outputs:", fg='blue', bold=True))
    for i, output in enumerate(outputs, 1):
        click.echo(f"{i}. {output.get('name', 'unnamed')} ({output.get('type', 'unknown')})")
        
    click.echo("")
    click.echo("0. Back")
    
    choice = click.prompt("Select an output to edit", type=int, default=0)
    
    if choice == 0:
        return
    elif 1 <= choice <= len(outputs):
        output = outputs[choice - 1]
        output_type = output.get('type', 'unknown')
        
        if output_type == 'stdout':
            new_output = configure_stdout_output()
        elif output_type == 'file':
            new_output = configure_file_output()
        elif output_type == 'http':
            new_output = configure_http_output()
        else:
            click.echo(f"Unsupported output type: {output_type}")
            click.pause()
            return
            
        outputs[choice - 1] = new_output
        click.echo(click.style("Output updated successfully!", fg='green'))
        click.pause()
    else:
        click.echo("Invalid option.")
        click.pause()


def remove_output_menu(outputs):
    """Display a menu for removing an output.
    
    Args:
        outputs: List of outputs
    """
    click.clear()
    click.echo(click.style("Remove Output", fg='green', bold=True))
    click.echo(click.style("=" * 50, fg='green'))
    click.echo("")
    
    # Display active outputs
    click.echo(click.style("Active Outputs:", fg='blue', bold=True))
    for i, output in enumerate(outputs, 1):
        click.echo(f"{i}. {output.get('name', 'unnamed')} ({output.get('type', 'unknown')})")
        
    click.echo("")
    click.echo("0. Back")
    
    choice = click.prompt("Select an output to remove", type=int, default=0)
    
    if choice == 0:
        return
    elif 1 <= choice <= len(outputs):
        output = outputs.pop(choice - 1)
        click.echo(click.style(f"Removed output: {output.get('name', 'unnamed')}", fg='green'))
        click.pause()
    else:
        click.echo("Invalid option.")
        click.pause()


def save_configuration():
    """Save the current configuration to the config file."""
    try:
        # Need to get config_path and config_data from a higher scope
        # In an actual function this would be properly passed or accessed
        # For demonstration, this function is added but will be defined properly 
        # when integrated into the main code
        pass
    except Exception as e:
        click.echo(click.style(f"Error saving configuration: {e}", fg='red'))
        click.pause()


def start_stop_generators_menu(config_path, active_generators, engine):
    """Display a menu for starting and stopping generators.
    
    Args:
        config_path: Path to the configuration file
        active_generators: List of active generators
        engine: The engine instance to use
    """
    # Set up the engine with the configuration
    config_data = load_config(config_path)
    
    # Save the configuration function (defined within scope)
    def save_configuration():
        try:
            config_data['active_generators'] = active_generators
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            click.echo(click.style("Configuration saved successfully!", fg='green'))
            return True
        except Exception as e:
            click.echo(click.style(f"Error saving configuration: {e}", fg='red'))
            return False
    
    # Make save_configuration available in global scope for other menus
    globals()['save_configuration'] = save_configuration
    
    # Log the configuration for debugging
    click.echo("Using existing engine instance...")
    
    # Show outputs being loaded
    if 'outputs' in config_data:
        click.echo(f"Found {len(config_data['outputs'])} output(s) in configuration")
        for i, output in enumerate(config_data['outputs'], 1):
            click.echo(f"  {i}. {output.get('name', 'unnamed')} ({output.get('type', 'unknown')})")
    else:
        click.echo("No outputs found in configuration, will use default file output")
    
    # Small pause to let the user see the configuration
    click.pause()
    
    # Check if the engine is already running (in case we're returning to this menu)
    engine_running = engine.is_running()
    
    # Mark all generators in config file as active, but they're not running yet
    # When the engine starts, it will automatically start all active generators
    for name in active_generators:
        if name in engine.generators:
            # Set the generator to active in the engine
            engine.generators[name].active = True
    
    while True:
        click.clear()
        click.echo(click.style("Generator Control", fg='green', bold=True))
        click.echo(click.style("=" * 50, fg='green'))
        click.echo("")
        
        # Display engine status
        engine_status = click.style("[Running]", fg='green') if engine_running else click.style("[Stopped]", fg='yellow')
        click.echo(f"Engine Status: {engine_status}")
        click.echo("")
        
        # Display generators and their status
        click.echo(click.style("Generators:", fg='blue', bold=True))
        for i, generator_name in enumerate(active_generators, 1):
            # Check if this generator exists
            generator_exists = generator_name in engine.generators
            
            # Format status indicators
            if not generator_exists:
                status = click.style("[Not Found]", fg='red')
            elif engine_running and generator_name in engine.generators and engine.generators[generator_name].active:
                status = click.style("[Running]", fg='green')
            else:
                status = click.style("[Stopped]", fg='yellow')
                
            click.echo(f"{i}. {generator_name} {status}")
            
        click.echo("")
        click.echo(click.style("Options:", fg='yellow'))
        click.echo("1. Start/stop engine")
        click.echo("2. Start generator")
        click.echo("3. Stop generator")
        click.echo("4. Restart generator")
        click.echo("5. Start all generators")
        click.echo("6. Stop all generators")
        click.echo("0. Back")
        
        choice = click.prompt("Select an option", type=int, default=0)
        
        if choice == 0:
            # Before returning, stop the engine if it's running
            if engine_running:
                if click.confirm("Stop the engine before exiting?", default=True):
                    try:
                        engine.stop()
                        engine_running = False
                        click.echo("Engine stopped.")
                    except Exception as e:
                        click.echo(f"Error stopping engine: {e}")
            return
            
        elif choice == 1:
            # Start/stop the engine
            if engine_running:
                # Stop the engine
                try:
                    engine.stop()
                    engine_running = False
                    
                    # Save configuration to reflect engine status
                    save_configuration()
                    
                    click.echo("Engine stopped. All generators are now stopped.")
                    click.pause()
                except Exception as e:
                    click.echo(f"Error stopping engine: {e}")
                    click.pause()
            else:
                # Start the engine
                try:
                    # Start the engine - this will start all active generators
                    engine.start()
                    engine_running = True
                    
                    # Save configuration to reflect engine status
                    save_configuration()
                    
                    click.echo("Engine started. All active generators are now running.")
                    click.pause()
                except Exception as e:
                    click.echo(f"Error starting engine: {e}")
                    click.pause()
                
        elif choice == 2:
            # Start a generator
            generator_idx = select_generator_to_control(active_generators, "start")
            if generator_idx >= 0:
                generator_name = active_generators[generator_idx]
                if generator_name not in engine.generators:
                    click.echo(f"Generator '{generator_name}' not found in the system.")
                    click.pause()
                    continue
                    
                try:
                    # Set generator to active
                    engine.generators[generator_name].active = True
                    
                    # Save configuration to update active_generators status
                    save_configuration()
                    
                    # Start the generator if engine is running
                    if engine_running:
                        engine.start_generator(generator_name)
                        click.echo(f"Generator '{generator_name}' started and is now running.")
                    else:
                        click.echo(f"Generator '{generator_name}' is now active but the engine is stopped. " +
                                  "Start the engine to begin generating logs.")
                    
                    click.pause()
                except Exception as e:
                    click.echo(f"Error starting generator: {e}")
                    click.pause()
                    
        elif choice == 3:
            # Stop a generator
            generator_idx = select_generator_to_control(active_generators, "stop")
            if generator_idx >= 0:
                generator_name = active_generators[generator_idx]
                if generator_name not in engine.generators:
                    click.echo(f"Generator '{generator_name}' not found in the system.")
                    click.pause()
                    continue
                    
                try:
                    # Stop the generator
                    if engine_running:
                        engine.stop_generator(generator_name)
                    
                    engine.generators[generator_name].active = False
                    
                    # Save configuration to update active_generators status
                    save_configuration()
                    
                    click.echo(f"Generator '{generator_name}' stopped and is now inactive.")
                    click.pause()
                except Exception as e:
                    click.echo(f"Error stopping generator: {e}")
                    click.pause()
                    
        elif choice == 4:
            # Restart a generator
            generator_idx = select_generator_to_control(active_generators, "restart")
            if generator_idx >= 0:
                generator_name = active_generators[generator_idx]
                if generator_name not in engine.generators:
                    click.echo(f"Generator '{generator_name}' not found in the system.")
                    click.pause()
                    continue
                    
                try:
                    # Stop the generator if the engine is running
                    if engine_running:
                        # Stop first
                        engine.stop_generator(generator_name)
                        
                        # Set as active
                        engine.generators[generator_name].active = True
                        
                        # Start again
                        engine.start_generator(generator_name)
                        click.echo(f"Generator '{generator_name}' has been restarted and is now running.")
                    else:
                        # Just set as active, engine isn't running
                        engine.generators[generator_name].active = True
                        click.echo(f"Generator '{generator_name}' is now active but the engine is stopped. " +
                                  "Start the engine to begin generating logs.")
                    
                    # Save configuration to update active_generators status
                    save_configuration()
                    
                    click.pause()
                except Exception as e:
                    click.echo(f"Error restarting generator: {e}")
                    click.pause()
                    
        elif choice == 5:
            # Start all generators
            try:
                # Mark all generators as active
                for generator_name in active_generators:
                    if generator_name in engine.generators:
                        engine.generators[generator_name].active = True
                
                # Save configuration to update active_generators status
                save_configuration()
                
                # Start them if engine is running
                if engine_running:
                    for generator_name in active_generators:
                        if generator_name in engine.generators:
                            try:
                                engine.start_generator(generator_name)
                            except Exception as e:
                                click.echo(f"Error starting generator '{generator_name}': {e}")
                    
                    click.echo("All generators started and are now running.")
                else:
                    click.echo("All generators are now active. Start the engine to begin generating logs.")
                
                click.pause()
            except Exception as e:
                click.echo(f"Error starting generators: {e}")
                click.pause()
                
        elif choice == 6:
            # Stop all generators
            try:
                for generator_name in active_generators:
                    if generator_name in engine.generators:
                        if engine_running:
                            engine.stop_generator(generator_name)
                        engine.generators[generator_name].active = False
                
                # Save configuration to update active_generators status
                save_configuration()
                
                click.echo("All generators stopped and are now inactive.")
                click.pause()
            except Exception as e:
                click.echo(f"Error stopping generators: {e}")
                click.pause()
                
        else:
            click.echo("Invalid option.")
            click.pause()


def select_generator_to_control(generators, action):
    """Prompt the user to select a generator.
    
    Args:
        generators: List of generators
        action: Action to perform on the generator (for display purposes)
        
    Returns:
        Index of the selected generator, or -1 if cancelled
    """
    click.clear()
    click.echo(click.style(f"Select Generator to {action.title()}", fg='green', bold=True))
    click.echo(click.style("=" * 50, fg='green'))
    click.echo("")
    
    # Display generators
    for i, generator in enumerate(generators, 1):
        click.echo(f"{i}. {generator}")
        
    click.echo("")
    click.echo("0. Cancel")
    
    choice = click.prompt("Select a generator", type=int, default=0)
    
    if choice == 0:
        return -1
    elif 1 <= choice <= len(generators):
        return choice - 1
    else:
        click.echo("Invalid choice.")
        click.pause()
        return -1


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == '__main__':
    main()