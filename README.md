# LogForge - Synthetic Event Log Generator

LogForge is a Python-based application for generating synthetic but realistic event logs from various products including Windows Event Log, Palo Alto Firewall, and Azure AD authentication. It's designed to help security professionals, developers, and testers create realistic log data for testing, development, and training purposes.

## Recent Changes

**Version 1.1.0 (April 2025)**
- **File Output Module Fix**: Improved generator name extraction from metadata
- **Format Accuracy**: Fixed file extensions to correctly represent log format
- **Data Source Handling**: Better identification of data sources from generator metadata
- **File Naming**: More consistent handling of file naming and sanitization

LogForge uses a template-based approach that doesn't require any coding to add new log types. Simply create template files in the appropriate format (XML, JSON, etc.) and metadata files describing their attributes, and LogForge will automatically generate realistic event logs.

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
git clone https://github.com/yourusername/LogForge.git
cd LogForge

# Install the package
pip install -e .
```

## Configuration

LogForge uses YAML configuration files to define outputs, time patterns, and active generators. It also uses a separate entities YAML file to define users, devices, and services for use in log generation.

### Main Configuration File

The main configuration (`config.yaml`) contains the log generation settings:

```yaml
# Path to entity registry file
entity_registry: "entities.yaml"

# The initial config has no outputs configured
# LogForge will prompt you to choose between file or HTTP output when first run
outputs: []

# Time patterns control frequency of logs throughout the day/week
time_patterns:
  - name: business_hours
    base_frequency: 1.0
    start_time: "09:00"
    end_time: "17:00"
    days_of_week: ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    multiplier: 2.0
  - name: night_hours
    base_frequency: 0.3
    start_time: "17:00"
    end_time: "09:00"
    days_of_week: ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    multiplier: 0.3
  - name: weekend
    base_frequency: 0.2
    start_time: "00:00"
    end_time: "23:59"
    days_of_week: ["SATURDAY", "SUNDAY"]
    multiplier: 0.5

# No generators activated by default
# Use the CLI menu to add generators
active_generators: []
```

### Log Generation Frequency Control

LogForge provides a sophisticated system for controlling the frequency of log generation to create realistic patterns that mirror actual production environments:

#### Base Frequency

The `base_frequency` parameter is defined in each generator's metadata file and represents:

- **Events per second**: A value of 1.0 means approximately one log entry per second
- **Time between events**: A value of 0.5 means approximately one entry every 2 seconds
- **Starting point**: The actual generation rate is calculated by applying time pattern multipliers to this base value

For example, a common Windows login event might have a higher base frequency (0.5) than a rare system error (0.05).

#### Time Patterns

Time patterns allow you to model how event frequency changes throughout the day and week:

```yaml
time_patterns:
  - name: business_hours          # Descriptive name for the pattern
    base_frequency: 1.0           # Not used (use generator's base_frequency)
    start_time: "09:00"           # Pattern active start time (24-hour format)
    end_time: "17:00"             # Pattern active end time
    days_of_week: ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]  # Days when pattern is active
    multiplier: 2.0               # Multiply generator's base_frequency by this value when pattern is active
```

When a time pattern is active (current time is within its time range and on a matching day), it applies its multiplier to the generator's base frequency.

#### Multipliers

Multipliers directly scale the event frequency up or down:

- **Multiplier > 1.0**: Increases event frequency (2.0 = double the events)
- **Multiplier < 1.0**: Decreases event frequency (0.5 = half the events)
- **Default = 1.0**: When no patterns are active or specified

#### How Frequency is Calculated

1. Start with the generator's `base_frequency` (e.g., 0.2 events/second)
2. Check which time patterns are currently active
3. Multiply the base frequency by the multiplier of each active pattern
4. Add some randomness (±20%) to create natural variation

For example:
- Base frequency = 0.2 (1 event every 5 seconds)
- Active patterns: business_hours (2.0) and monday_boost (1.5)
- Effective frequency = 0.2 × 2.0 × 1.5 = 0.6 (3x faster, or about 1 event every 1.7 seconds)

This system lets you create realistic log patterns that reflect business hours, after-hours maintenance, weekend quiet periods, and other real-world scenarios.

Each log generator can reference different time patterns in its metadata, allowing Windows login events to follow one pattern while firewall logs follow another.

### Entity Registry

The entity registry (`entities.yaml`) defines the users, devices, and services that can be referenced in log templates:

```yaml
users:
  - username: "jsmith"
    full_name: "John Smith"
    email: "jsmith@example.com"
    user_id: "U1001"
    department: "IT"
    title: "System Administrator"
    is_admin: true
    employee_type: "employee"
    organization: "Technology Services"

devices:
  - hostname: "WS001"
    ip_address: "192.168.1.100"
    mac_address: "00:1A:2B:3C:4D:5E"
    device_id: "D1001"
    os_type: "Windows 10"
    os_version: "10.0.19044"
    owner: "jsmith"

services:
  - name: "Web Server"
    port: 80
    protocol: "HTTP"
    service_id: "S1001"
    description: "Internal company website"
    owner: "jsmith"
```

You can create multiple entity files for different environments or scenarios.
```

### Available Output Types

You can configure the following output types:

#### File Output
```yaml
outputs:
  - type: file
    name: file_output
    file_path: "logs/logforge.json"
    hourly_rotation: true
    data_source_field: "generator"
```

#### HTTP Output
```yaml
outputs:
  - type: http
    name: api_output
    url: "https://api.example.com/logs"
    method: "POST"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer YOUR_API_TOKEN_HERE"
    retry_count: 3
    retry_delay: 1.0
```

#### Console Output
```yaml
outputs:
  - type: stdout
    name: console
```

## Usage

```bash
# Run with a configuration file
logforge run --config config.yaml

# Run with a custom entities file (overrides the one in config.yaml)
logforge run --config config.yaml --entities local/entities.yaml

# List available generators
logforge list-generators --config config.yaml

# List generators with a custom entities file
logforge list-generators --config config.yaml --entities local/entities.yaml

# Interactive configuration menu (recommended for first-time setup)
logforge configure --config config.yaml

# Configure with a custom entities file
logforge configure --config config.yaml --entities local/entities.yaml

# Create a systemd service (after configuring)
logforge create-service --config /absolute/path/to/config.yaml --user LogForge

# Create a service with a custom entities file
logforge create-service --config /absolute/path/to/config.yaml --entities /absolute/path/to/entities.yaml --user LogForge

# Run with verbose output (shows errors on console)
logforge -v run --config config.yaml
```

### Log File Output

By default, log files are organized with:
- Separate files per data source (based on the `data_source_field`)
- Hourly rotation with timestamps in filenames
- File extension matching the actual log format (not the template extension)
- Format: `{data_source}_{YYYYMMDD_HH}_{filename}.{extension}`

Example:
```
logs/
  ├── windows_security_login_success_20250329_14_logforge.xml
  ├── windows_security_login_success_20250329_15_logforge.xml
  ├── windows_system_service_start_20250329_14_logforge.xml
  ├── windows_system_service_start_20250329_15_logforge.xml
  ├── paloalto_firewall_traffic_20250329_14_logforge.json
  └── paloalto_firewall_traffic_20250329_15_logforge.json
```

> **Note**: In version 1.1.0, the file output module was significantly improved to correctly use metadata from the generator for file naming and data source identification. Previous versions may have used incorrect extensions or failed to properly separate logs by data source.

### HTTP Output with Authentication

The HTTP output adapter wraps all log events in a JSON object with the raw content in an `event` field, and when available, the format is included as well:

```json
{
  "event": "<actual log content as text>",
  "format": "xml"
}
```

This ensures that regardless of the original log format (XML, JSON, etc.), the HTTP endpoint receives a well-formed JSON object with the raw event content preserved.

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

To run LogForge as a systemd service:

1. Create the service file:
   ```bash
   sudo logforge create-service --config /absolute/path/to/config.yaml --user LogForge
   ```

2. Control the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable LogForge.service
   sudo systemctl start LogForge.service
   sudo systemctl status LogForge.service
   sudo systemctl stop LogForge.service
   ```

## Extending

LogForge is designed to be easily extended with new log generators using a template-based approach that requires no coding.

### Adding Custom Data Sources

LogForge uses a template-only approach to create log generators. This simplifies the process of adding new log types without writing any code.

#### Creating Templates and Metadata

To add a new log type:

1. Create a template file in the `templates` directory following the vendor/product/data_source structure
2. Add a corresponding `.meta.yaml` file with the same name
3. LogForge automatically discovers and creates generators from these templates

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
        "logforge.generators": [
            "custom_generator=my_plugin.generators:CustomGenerator",
        ],
    },
)
```

The template-only approach is recommended for most use cases and requires no coding, just template files.

### Template Functions

Logforge provides a rich set of template functions to generate random synthetic data in your templates. These can be used as either functions or filters in Jinja2 templates:

#### Random Value Generation
- `random_int(min_value=0, max_value=1000)`: Generate a random integer
- `random_guid()`: Generate a random GUID/UUID
- `random_string(length=10, chars=None)`: Generate a random string

#### Network-related Functions
- `random_ip()` or `random_public_ip()`: Generate a random public IP address
- `random_private_ip()`: Generate a random private IP from common private ranges
- `random_port(min_port=1024, max_port=65535)`: Generate a random port number
- `random_mac()`: Generate a random MAC address

#### Time-related Functions
- `current_timestamp()`: Current timestamp in seconds since epoch
- `format_timestamp(timestamp=None, format_str='%Y-%m-%d %H:%M:%S')`: Format a timestamp
- `to_datetime(timestamp)`: Convert a timestamp string to a datetime object
- `format_datetime(dt, format_str='%Y-%m-%dT%H:%M:%S.%fZ')`: Format a datetime object

#### Entity Registry Functions
- `registry.get_random_user()`: Get a random user from the entity registry
- `registry.get_random_device()`: Get a random device from the entity registry
- `registry.get_random_service()`: Get a random service from the entity registry

Example usage in an XML template:
```xml
<Event>
  <TimeCreated SystemTime="{{ current_timestamp() | format_timestamp('%Y-%m-%dT%H:%M:%S.%fZ') }}" />
  <EventID>{{ random_int(1000, 9999) }}</EventID>
  <Computer>{{ registry.get_random_device().hostname }}</Computer>
  <IpAddress>{{ random_ip() }}</IpAddress>
  <SourcePort>{{ random_port() }}</SourcePort>
  <User>{{ registry.get_random_user().username }}</User>
</Event>
```

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
base_frequency: 0.2          # Base rate: 1 event every 5 seconds
time_patterns:               # List of time patterns that affect this generator
  - business_hours           # References patterns defined in config.yaml
  - night_hours
  - weekend
business_hours_multiplier: 2.0    # Override the default multiplier for this generator
night_hours_multiplier: 0.3       # Lower frequency after business hours
weekend_multiplier: 0.5           # Medium frequency on weekends

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