# Logforge - Synthetic Event Log Generator

Logforge is a Python-based application for generating synthetic but realistic event logs from various products including Windows Event Log, Palo Alto Firewall, and Azure AD authentication. It's designed to help security professionals, developers, and testers create realistic log data for testing, development, and training purposes.

## Features

- Generates realistic logs with proper format and volume/frequency
- Defines assets and identities that can be inserted into logs for realism and correlation
- Uses Jinja templates for log definition
- Supports multiple log formats including JSON, syslog, XML, and others
- Supports multiple outputs (stdout, flat file, HTTP)
- Allows collaborators to easily add new log types using only template files
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

# Interactive configuration menu
synth-logs configure --config config.yaml
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

Logforge is designed to be easily extended with new log generators using a template-based approach that requires no coding.

### Adding Custom Data Sources

Logforge now uses a template-only approach to create log generators. This simplifies the process of adding new log types without writing any code.

#### Creating Templates and Metadata

To add a new log type:

1. Create a template file in the `templates` directory following the vendor/product/data_source structure
2. Add a corresponding `.meta.yaml` file with the same name
3. Logforge automatically discovers and creates generators from these templates

Example directory structure:
```
templates/
└── apache/
    └── webserver/
        ├── access.json
        ├── access.meta.yaml
        ├── error.json
        └── error.meta.yaml
```

Example metadata file (`access.meta.yaml`):
```yaml
vendor: Apache
product: Webserver
data_source: Access Logs
description: Common Apache access logs in JSON format
format: JSON

# Generator settings
is_generator: true
base_frequency: 0.5
time_patterns:
  - business_hours
  - night_hours
business_hours_multiplier: 2.0
night_hours_multiplier: 0.3

# Context values for template variables
context:
  server_name: www.example.com
  protocol: HTTP/1.1
```

#### Custom Plugins (For Special Cases)

For log generation that requires custom logic beyond what templates can provide, you can create an external plugin:

1. Create a Python package for your custom generator
2. Implement a generator class that inherits from `LogGenerator`
3. Register your generator using entry points

Example `setup.py` for an external plugin:
```python
setup(
    name="my_custom_plugin",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "synth_logs.generators": [
            "custom_generator=my_plugin.generators:CustomGenerator",
        ],
    },
)
```

The template-only approach is recommended for most use cases and requires no coding, just template files.

### Template Metadata

Each template can have a metadata file (`.meta.yaml`) that provides additional information about the template:

```yaml
vendor: Microsoft
product: Windows
data_source: Security Login Success
description: Windows Security successful login events (EventID 4624)
format: XML
frequency: high

# Generator settings for template-based generators
is_generator: true
base_frequency: 0.2
time_patterns:
  - business_hours
  - night_hours
  - weekend
business_hours_multiplier: 2.0
night_hours_multiplier: 0.3
weekend_multiplier: 0.5

# Context values for rendering
context:
  event_id: 4624
  logon_type: 2
  session_id: 1

# Parameter definitions
parameters:
  - name: username
    description: The username of the user logging in
    required: true
  - name: domain
    description: The domain of the user
    required: true
```

This metadata serves multiple purposes:
1. Powers the interactive configuration menu
2. Creates template-based generators automatically
3. Controls generation frequency and patterns
4. Provides default context values for templates

Metadata files are automatically discovered alongside templates with the same name but with `.meta.yaml` extension.

### Generators vs Templates

In Logforge, each template file with its metadata creates a generator. For example:

- `templates/windows/security/login_success.xml` with `login_success.meta.yaml` creates a `windows_security_login_success` generator
- `templates/windows/security/login_failure.xml` with `login_failure.meta.yaml` creates a `windows_security_login_failure` generator

Each generator focuses on producing one specific type of log entry based on its template. When using the interactive configuration menu, you'll see all available generators grouped by vendor and product.

## License

MIT