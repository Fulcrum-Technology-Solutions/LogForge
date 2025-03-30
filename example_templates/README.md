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
- `registry.get_random_service()`: Get a random service from the entity registry

## Usage Example

These functions can be used directly in templates:

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

## Template Metadata

Each template can have a corresponding `.meta.yaml` file that provides metadata about the template, including:
- Vendor and product information
- Description and format
- Generation frequency settings
- Default context values
- Parameter definitions

