# LogForge OSS

Synthetic event log generator with API-first architecture, configurable templates, and CLI tooling.

## Features

- FastAPI management API with health and status endpoints
- Click-based CLI (`logforge`) with initialization and status commands
- YAML configuration validated via Pydantic models
- Logging setup with rotating file handler and console output
- Embedded API server runnable in foreground or background thread

## Quick Start

```bash
pip install -e .

# Initialize user configuration (~/.logforge by default)
logforge init

# Show effective configuration
logforge config show

# Start API server
logforge api start

# Query status
logforge status
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

Licensed under the Apache License 2.0. See `LICENSE` for details.
