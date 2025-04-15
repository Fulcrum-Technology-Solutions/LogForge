# LogForge - Synthetic Event Log Generator

LogForge is a Python-based application for generating synthetic but realistic event logs from various products including Windows Event Log, Palo Alto Firewall, and Azure AD authentication. It's designed to help security professionals, developers, and testers create realistic log data for testing, development, and training purposes.

## Recent Changes

**Version 1.2.0 (April 2025)**
- **Enhanced Device Entities**: Added FQDN field to devices and extended device attributes
- **Custom Device Fields**: Support for custom fields with `custom_` prefix
- **Template Access**: Improved Jinja2 access to device fields including custom fields
- **Registry Functions**: Better device field access in templates with conditional support

**Version 1.1.0 (April 2025)**
- **File Output Module Fix**: Improved generator name extraction from metadata
- **Format Accuracy**: Fixed file extensions to correctly represent log format
- **Data Source Handling**: Better identification of data sources from generator metadata
- **File Naming**: More consistent handling of file naming and sanitization
- **Folder-Based Naming**: File names now use template folder structure for organization
- **Clearer Configuration**: Simplified file output configuration with separate directory and filename parameters

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
- **Template Verification**: Tools to verify template quality and fix common issues

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/LogForge.git
cd LogForge

# Install the package
pip install -e .
```

If the `logforge` command isn't available after installation, you can run it using:

```bash
# Run using the Python module syntax
python -m logforge.cli [COMMAND] [OPTIONS]

# Or use the executable scripts provided in the bin directory
./bin/logforge [COMMAND] [OPTIONS]
./bin/logforge-cli [COMMAND] [OPTIONS]
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
  - hostname: "WS001"                      # Required: Hostname
    fqdn: "WS001.example.com"              # Optional: Fully Qualified Domain Name
    ip_address: "192.168.1.100"            # Required: IP address
    mac_address: "00:1A:2B:3C:4D:5E"       # Required: MAC address
    device_id: "D1001"                     # Required: Unique device ID
    os_type: "Windows 10"                  # Optional: OS type
    os_version: "10.0.19044"               # Optional: OS version
    owner: "jsmith"                        # Required: Owner username
    device_type: "workstation"             # Optional: Type of device (workstation, laptop, server)
    model: "Dell OptiPlex 7090"            # Optional: Hardware model
    department: "IT"                       # Optional: Department
    status: "active"                       # Optional: Status (active, maintenance, etc.)
    last_updated: "2025-03-01"             # Optional: Date of last update
    custom_asset_tag: "IT-PC-7090-001"     # Optional: Any field with custom_ prefix
    custom_purchase_date: "2024-12-15"     # Optional: Custom fields can store any information

services:
  - name: "Web Server"
    port: 80
    protocol: "HTTP"
    service_id: "S1001"
    description: "Internal company website"
    owner: "jsmith"
```

#### Custom Device Fields

Any field prefixed with `custom_` can be added to device definitions to store organization-specific data. These fields are accessible in templates just like standard fields. For example:

```yaml
# In entities.yaml
devices:
  - hostname: "SRV001"
    # ... standard fields ...
    custom_location: "Rack 3, Data Center 1"
    custom_warranty_expiry: "2027-01-15"
```

```jinja
{# In a template #}
{% set device = registry.get_random_device() %}
{% if device.custom_location is defined %}
Location: {{ device.custom_location }}
{% endif %}
```

You can create multiple entity files for different environments or scenarios.
```

### Available Output Types

You can configure the following output types:

#### File Output

```yaml
# Recommended new format (version 1.1.0 and later):
outputs:
  - type: file
    name: file_output
    output_dir: "logs"              # Directory where log files will be stored
    base_filename: "logforge"       # Base name used in all log files (without extension)
    default_extension: ".log"       # Default extension when format can't be determined
    hourly_rotation: true           # Creates timestamped files (YYYYMMDD_HH)
    max_size: 10485760              # Optional: 10MB maximum file size before rotation
    backup_count: 5                 # Optional: Keep 5 backup files when rotating by size
    data_source_field: "generator"  # Optional: Field to use as fallback if folder structure can't be determined
```

```yaml
# Legacy format (still supported):
outputs:
  - type: file
    name: file_output
    file_path: "logs/logforge.log"  # Full path with filename
    hourly_rotation: true
    max_size: 10485760              # Optional: 10MB
    backup_count: 5                 # Optional
    data_source_field: "generator"  # Optional
```

The new format improves clarity by separating the directory from the base filename and explicitly defining the default extension, making it easier to understand the file naming process.

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
- Separate files per template folder structure (automatically extracted from template paths)
- Hourly rotation with timestamps in filenames
- File extension matching the actual log format (not the template extension)
- Format: `{folder1_folder2_folder3}_{YYYYMMDD_HH}_{filename}.{extension}`

Example:
```
logs/
  ├── microsoft_windows_security_20250329_14_logforge.xml
  ├── microsoft_windows_security_20250329_15_logforge.xml
  ├── microsoft_windows_system_20250329_14_logforge.xml
  ├── microsoft_windows_system_20250329_15_logforge.xml
  ├── paloalto_traffic_20250329_14_logforge.json
  └── paloalto_traffic_20250329_15_logforge.json
```

The naming is derived from the template folder structure:
- `templates/microsoft/windows/security/login_success.j2` → `microsoft_windows_security_TIMESTAMP_filename.ext`
- `templates/paloalto/traffic/traffic.j2` → `paloalto_traffic_TIMESTAMP_filename.ext`

> **Note**: In version 1.1.0, the file output module was significantly improved to use the folder structure of templates for file naming to ensure consistent organization. The file extension is determined by:
> 1. Explicitly provided extension in config
> 2. Original template file extension
> 3. Format specified in template metadata
> 4. Default (.log)

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
- `random_private_ip([subnet])`: Generate a random private IP address
  - Optionally specify a subnet name or CIDR notation (e.g., `random_private_ip('office')` or `random_private_ip('10.0.0.0/24')`)
  - Subnets can be configured in config.yaml (see "Configuring Internal Networks" below)

### Configuring Internal Networks

You can define custom internal network ranges in your configuration file to use for IP address generation. This is useful for creating realistic internal IP addresses that match your organization's network structure.

```yaml
# Network ranges configuration for internal IP address generation
network_ranges:
  # Using CIDR notation (recommended)
  - cidr: "10.1.0.0/16"
    name: "office"
  - cidr: "172.16.0.0/24"
    name: "servers"
  - cidr: "192.168.0.0/16"
    name: "corporate"
  
  # Using start/end IP addresses
  - start_ip: "10.2.0.0"
    end_ip: "10.2.255.255"
    name: "datacenter"
```

You can then reference these named ranges in your templates:

```
IP Address: {{ random_private_ip('office') }}
```

If no subnet is specified, LogForge will randomly choose one of your configured networks. If no custom networks are configured, it will use standard private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16).
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
  - Access standard fields like `device.hostname`, `device.fqdn`, `device.ip_address`, etc.
  - Access custom fields with the same dot notation: `device.custom_asset_tag`, `device.custom_location`
  - Check if a field exists with `{% if device.custom_field is defined %}`
- `registry.get_random_service()`: Get a random service from the entity registry
- `registry.get_device(hostname)`: Get a specific device by hostname
- `registry.get_user(username)`: Get a specific user by username
- `registry.get_service(name)`: Get a specific service by name

### Template Variable Reuse

You can create reusable variables in your templates using Jinja2's `set` statement. This is particularly useful for:

1. Creating coherent events with consistent entities
2. Improving template readability
3. Optimizing performance by avoiding repeated calls to registry functions

Example using variable reuse in a JSON template:

```jinja
{%- set user = registry.get_random_user() -%}
{%- set device = registry.get_random_device() -%}
{%- set timestamp = current_timestamp() -%}
{%- set event_type = ['info', 'warning', 'error'] | random -%}

{
  "timestamp": "{{ timestamp | format_timestamp('%Y-%m-%dT%H:%M:%S.%fZ') }}",
  "eventType": "{{ event_type }}",
  "severity": "{{ event_type | capitalize }}",
  "user": {
    "username": "{{ user.username }}",
    "email": "{{ user.email }}",
    "department": "{{ user.department }}"
  },
  "device": {
    "hostname": "{{ device.hostname }}",
    "ipAddress": "{{ device.ip_address }}",
    "osVersion": "{{ device.os_version }}"
  },
  "message": "User {{ user.username }} logged in from {{ device.hostname }}"
}
```

This ensures that the same user, device, timestamp, and event type are used consistently throughout the template, making the generated log more realistic and coherent.

Example usage in an XML template:
```xml
{%- set user = registry.get_random_user() -%}
{%- set device = registry.get_random_device() -%}
{%- set event_time = current_timestamp() | format_timestamp('%Y-%m-%dT%H:%M:%S.%fZ') -%}

<Event>
  <TimeCreated SystemTime="{{ event_time }}" />
  <EventID>{{ random_int(1000, 9999) }}</EventID>
  <Computer>{{ device.hostname }}</Computer>
  <IpAddress>{{ device.ip_address }}</IpAddress>
  <SourcePort>{{ random_port() }}</SourcePort>
  <User>{{ user.username }}</User>
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