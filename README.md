# Logforge - Synthetic Event Log Generator

Logforge is a Python-based application for generating synthetic but realistic event logs from various products including Windows Event Log, Palo Alto Firewall, and Azure AD authentication. It's designed to help security professionals, developers, and testers create realistic log data for testing, development, and training purposes.

Logforge uses a template-based approach that doesn't require any coding to add new log types. Simply create template files in the appropriate format (XML, JSON, etc.) and metadata files describing their attributes, and Logforge will automatically generate realistic event logs.

## Features

- **Pure Template-Based Approach**: No coding required to add new log types
- **Format Preservation**: XML templates output XML files, JSON templates output JSON files
- **Interactive CLI Menu**: Configure generators, outputs, and control engine in real-time
- **Realistic Generation**: Variable frequency based on time of day and day of week
- **Multiple Output Options**: Console, files (with rotation), or HTTP endpoints
- **Multiple Log Types**: Windows Event Logs, Palo Alto Firewall logs, and more
- **Dynamic Entity Population**: Insert realistic usernames, hostnames, and IPs in logs
- **Jinja2 Template Engine**: Powerful and flexible templating for log content
- **Runtime Control**: Start/stop individual generators on demand
- **Intelligent File Organization**: Separate files for each log type
- **Service Mode**: Run as a systemd service for continuous generation
- **Headless Operation**: Run without interaction for automated deployments

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
  - type: http
    name: api_output
    url: "https://api.example.com/logs"
    method: "POST"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer YOUR_API_TOKEN_HERE"
    retry_count: 3
    retry_delay: 1.0

# Active generators
active_generators:
  - microsoft_windows_security_login_success
  - microsoft_windows_system_service_start
  - paloalto_traffic_session
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
- File extension matching the source template (XML files output XML, JSON files output JSON)
- Format: `{data_source}_{YYYYMMDD_HH}_{filename}.{extension}`

Example:
```
logs/
  ├── windows_security_login_success_20250329_14_synth_logs.xml
  ├── windows_security_login_success_20250329_15_synth_logs.xml
  ├── windows_system_service_start_20250329_14_synth_logs.xml
  ├── windows_system_service_start_20250329_15_synth_logs.xml
  ├── paloalto_firewall_traffic_20250329_14_synth_logs.json
  └── paloalto_firewall_traffic_20250329_15_synth_logs.json
```

### HTTP Output with Authentication

Logforge supports several authentication methods for the HTTP output adapter:

1. **Bearer Token Authentication**:
   ```yaml
   outputs:
     - type: http
       name: api_output
       url: "https://api.example.com/logs"
       headers:
         Authorization: "Bearer YOUR_TOKEN_HERE"
   ```

2. **Basic Authentication**:
   ```yaml
   outputs:
     - type: http
       name: api_output
       url: "https://api.example.com/logs"
       headers:
         Authorization: "Basic BASE64_ENCODED_CREDENTIALS"
   ```

3. **API Key Authentication**:
   ```yaml
   outputs:
     - type: http
       name: api_output
       url: "https://api.example.com/logs"
       headers:
         X-API-Key: "YOUR_API_KEY_HERE"
   ```

The interactive CLI menu provides a guided setup for these authentication methods.

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

Logforge uses a template-only approach to create log generators. This simplifies the process of adding new log types without writing any code.

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
        ├── access.log
        ├── access.meta.yaml
        ├── error.log
        └── error.meta.yaml
```

The output logs will maintain the same file extension as the template files, so an `access.log` template will generate `.log` files, and an XML template will generate `.xml` files.

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

- `templates/microsoft/windows/security/login_success.xml` with `login_success.meta.yaml` creates a `microsoft_windows_security_login_success` generator
- `templates/microsoft/windows/security/login_failure.xml` with `login_failure.meta.yaml` creates a `microsoft_windows_security_login_failure` generator
- `templates/paloalto/traffic/session.json` with `session.meta.yaml` creates a `paloalto_traffic_session` generator

Each generator focuses on producing one specific type of log entry based on its template. The generator's name is constructed from the path components (vendor, product, data_source), and it will output logs with the same file extension as the template.

When using the interactive configuration menu, you'll see all available generators grouped by vendor and product, making it easy to select which log types to generate.

## License

MIT