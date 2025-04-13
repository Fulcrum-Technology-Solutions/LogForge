# Example Templates

These templates are provided as examples for customization. They use simplified static values instead of template functions to avoid compatibility issues.

## Usage

1. Copy an example template to the `templates/` directory
2. Edit as needed, using proper Jinja2 template syntax
3. Test with the application

## Available Functions in Templates

The following functions are available in templates and can be used either as functions or as filters:

### Random Value Generation
- `random_int(min_value=0, max_value=1000)`: Generate a random integer between min and max
- `random_guid()`: Generate a random GUID/UUID
- `random_string(length=10, chars=None)`: Generate a random string of specified length

### Network-related Functions
- `random_ip()` or `random_public_ip()`: Generate a random public IP address
- `random_private_ip()`: Generate a random private IP from ranges 10.0.0.0/8, 172.16.0.0/12, or 192.168.0.0/16
- `random_port(min_port=1024, max_port=65535)`: Generate a random port number
- `random_mac()`: Generate a random MAC address

### Time-related Functions
- `current_timestamp()`: Get the current timestamp in seconds since epoch
- `format_timestamp(timestamp=None, format_str='%Y-%m-%d %H:%M:%S')`: Format a timestamp with given format string
- `to_datetime(timestamp)`: Convert a timestamp string to a datetime object
- `format_datetime(dt, format_str='%Y-%m-%dT%H:%M:%S.%fZ')`: Format a datetime object with given format string

### Entity Registry Functions
- `registry.get_random_user()`: Get a random user from the entity registry
- `registry.get_random_device()`: Get a random device from the entity registry
  - Access standard fields: `device.hostname`, `device.fqdn`, `device.ip_address`, etc.
  - Access custom fields: `device.custom_asset_tag`, `device.custom_location`, etc.
  - Check if a field exists: `{% if device.custom_field is defined %}`
- `registry.get_random_service()`: Get a random service from the entity registry
- `registry.get_device(hostname)`: Get a specific device by hostname
- `registry.get_user(username)`: Get a specific user by username
- `registry.get_service(name)`: Get a specific service by name
- `registry.get_organization()`: Get the organization object with all settings
- `registry.get_domain()`: Get the organization's domain name (e.g., "example.com")
- `registry.get_netbios_domain()`: Get the organization's NetBIOS domain name (e.g., "EXAMPLE")
- `registry.get_org_setting(setting_name, default=None)`: Get a specific organization setting

## Usage Example

These functions can be used directly in templates:

```xml
{%- set device = registry.get_random_device() -%}
{%- set user = registry.get_random_user() -%}
{%- set domain = registry.get_domain() -%}
{%- set netbios_domain = registry.get_netbios_domain() -%}
<Event>
  <TimeCreated SystemTime="{{ current_timestamp() | format_timestamp('%Y-%m-%dT%H:%M:%S.%fZ') }}" />
  <EventID>{{ random_int(1000, 9999) }}</EventID>
  <Computer>{{ device.hostname }}</Computer>
  <FQDN>{{ device.fqdn | default(device.hostname + '.' + domain) }}</FQDN>
  <Domain>{{ netbios_domain }}</Domain>
  <IpAddress>{{ device.ip_address }}</IpAddress>
  <SourcePort>{{ random_port() }}</SourcePort>
  <User>{{ user.username }}</User>
  <UserDomain>{{ netbios_domain }}</UserDomain>
  <UserEmail>{{ user.username }}@{{ domain }}</UserEmail>
  <Department>{{ user.department }}</Department>
  <PasswordExpiry>{{ registry.get_org_setting('password_expiry_days', 90) }}</PasswordExpiry>
  {% if device.custom_asset_tag is defined %}
  <AssetTag>{{ device.custom_asset_tag }}</AssetTag>
  {% endif %}
  {% if device.custom_location is defined %}
  <Location>{{ device.custom_location }}</Location>
  {% endif %}
</Event>
```

This example demonstrates:
- Using `set` to store entities in variables for consistent references
- Accessing the device's FQDN with a fallback value
- Using organization's domain and NetBIOS domain names
- Accessing specific organization settings with defaults
- Creating a user email by combining username with domain
- Conditionally including custom fields when they exist

## Template Metadata

Each template can have a corresponding `.meta.yaml` file that provides metadata about the template, including:
- Vendor and product information
- Description and format
- Generation frequency settings
- Default context values
- Parameter definitions

See the example in `windows/security/login_success.meta.yaml` for a complete metadata file that demonstrates:
- Basic template information (vendor, product, format)
- Generation frequency settings with time-based multipliers
- Documentation for registry entity access including FQDN and custom fields
- Parameter documentation and examples

