# Example Templates

These templates are provided as examples for customization. They use simplified static values instead of template functions to avoid compatibility issues.

## Usage

1. Copy an example template to the `templates/` directory
2. Edit as needed, using proper Jinja2 template syntax
3. Test with the application

## Available Functions in Templates

The following functions are available in templates:

- `random_int(min, max)`: Generate a random integer between min and max
- `random_guid()`: Generate a random GUID
- `random_ip()`: Generate a random public IP address
- `random_private_ip()`: Generate a random private IP address
- `random_port()`: Generate a random port number
- `random_mac()`: Generate a random MAC address
- `random_string(length)`: Generate a random string of the given length
- `current_timestamp()`: Get the current timestamp
- `format_timestamp(timestamp, format_str)`: Format a timestamp with the given format string

