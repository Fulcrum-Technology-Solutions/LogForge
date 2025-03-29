# Logforge - Synthetic Event Log Generator

Logforge is a Python-based application for generating synthetic but realistic event logs from various products including Windows Event Log, Palo Alto Firewall, and Azure AD authentication. It's designed to help security professionals, developers, and testers create realistic log data for testing, development, and training purposes.

## Features

- Generates realistic logs with proper format and volume/frequency
- Defines assets and identities that can be inserted into logs for realism and correlation
- Uses Jinja templates for log definition
- Supports multiple log formats including JSON, syslog, XML, and others
- Supports multiple outputs (stdout, flat file, HTTP)
- Allows collaborators to easily add tech packages without modifying core code
- Supports multiple data sources per vendor
- Can run manually/headless, as a systemd service, or via a CLI menu
- Allows users to add or remove log generators at runtime
- Includes profiles to control frequency and verbosity based on time patterns
- Supports hourly log rotation with separate files per data source

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/logforge.git
cd logforge

# Install the package
pip install -e .
```

## Configuration

Logforge uses YAML configuration files to define outputs, time patterns, and active generators. See the `config.sample.yaml` file for an example.

```yaml
# Basic configuration
outputs:
  - type: stdout
    name: console
  - type: file
    name: file_output
    file_path: "logs/synth_logs.json"
    # Enable hourly rotation with timestamp in filename
    hourly_rotation: true
    # Field in log entry to identify the data source
    data_source_field: "generator"

# Active generators
active_generators:
  - windows_security
  - windows_system
```

## Usage

```bash
# Run with a configuration file
synth-logs run --config config.yaml

# List available generators
synth-logs list-generators --config config.yaml

# Create a systemd service
synth-logs create-service --config /absolute/path/to/config.yaml --user logforge
```

### Log File Output

By default, log files are organized with:
- Separate files per data source (based on the `data_source_field`)
- Hourly rotation with timestamps in filenames
- Format: `{data_source}_{YYYYMMDD_HH}_{filename}`

Example:
```
logs/
  ├── windows_security_20250329_14_synth_logs.json
  ├── windows_security_20250329_15_synth_logs.json
  ├── windows_system_20250329_14_synth_logs.json
  └── windows_system_20250329_15_synth_logs.json
```

### Systemd Service

To run Logforge as a systemd service:

1. Create the service file:
   ```bash
   sudo synth-logs create-service --config /absolute/path/to/config.yaml --user logforge
   ```

2. Control the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable logforge.service
   sudo systemctl start logforge.service
   sudo systemctl status logforge.service
   sudo systemctl stop logforge.service
   ```

## Extending

Logforge is designed to be easily extended with new log generators. See the `packages` directory for examples of how to implement new log generators.

## License

MIT