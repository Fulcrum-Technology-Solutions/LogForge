# LogForge OSS

Synthetic log generator with an API-first architecture, template-driven generators, and a batteries-included CLI.

## Features

- FastAPI management API with health, status, entity, generator, and template endpoints
- Click-based CLI (`logforge`) for config bootstrap, validation, entities, templates, and generator control
- YAML configuration backed by Pydantic models with `LOGFORGE__SECTION__KEY` environment overrides
- Entity registry and template loader with validation and pluggable outputs
- Console and file outputs with retry/backoff, plus metrics-ready instrumentation

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

The editable install provides the CLI (`logforge`) and all development tooling
(`ruff`, `pytest`, etc.).

## Quick Start (CLI)

```bash
# bootstrap local state under ~/.logforge
logforge init

# inspect effective configuration
logforge config show

# validate configuration & ensure filesystem layout
logforge config validate

# start the embedded API server (runs in foreground)
logforge api serve --host 0.0.0.0

# interact with the API via CLI
logforge status --output table
logforge entities list --type users
logforge generators list
logforge templates list
```

## Configuration Layout

- Config file: `~/.logforge/config.yaml`
- Entity registry: `~/.logforge/entities.yaml`
- Templates: `~/.logforge/templates/{default,custom}`
- Override via env: `LOGFORGE__API__HOST=0.0.0.0`, `LOGFORGE__TEMPLATES__CACHE_TTL=120`

Example configuration bundles live under `examples/configs/` and include:

- `simple-config.yaml`: single generator emitting to the console
- `multi-generator.yaml`: multiple generators with rotation-enabled file output
- `http-output.yaml`: ships events to an external HTTP collector (e.g., Splunk HEC)
- `entities-example.yaml`: sample entity registry for quick bootstrapping

## Templates

Sample templates are available in `examples/templates/` and are mounted into the
container image (see below). Review the [Template Guide](docs/template-guide.md)
for structure, helpers, and best practices when building new templates.

Included examples:

- `examples/windows_eventlog/security` – JSON Windows security events
- `examples/json/app_event` – Application telemetry in JSON format
- `examples/syslog/firewall` – RFC3164-style firewall syslog message

## Running with Docker

A production-ready container image ships with a non-root user, health check, and
volume mounts for configuration and templates.

```bash
# build the image locally
docker build -t logforge:latest .

# run with docker-compose (exposes port 8080)
docker compose up --build
```

The compose file mounts the example configuration, entity registry, and sample
templates into `/data/logforge`. Modify `docker-compose.yml` to point at your
own config bundle or secret store.

## API & Health

```bash
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8080/api/status

# authenticated CLI calls when API key auth is enabled
logforge --api-key "$LOGFORGE_TOKEN" entities list
logforge --api-key "$LOGFORGE_TOKEN" generators start demo
```

Enable API key auth by setting `api.auth.enabled` in the config or exporting
`LOGFORGE__API__AUTH__ENABLED=true`. When enabled, the API generates a key for
you if one is not already present.

## Development & Testing

```bash
ruff check src tests
PYTHONPATH=src pytest
```

All tests must pass before merging. The integration suite exercises the API
surface, entity registry, templates, and generator engine.

## Smoke Test Checklist

1. `pip install -e ".[dev]"` (or Docker build)
2. `logforge init`
3. Populate entities (`examples/configs/entities-example.yaml`)
4. Start the API server (`logforge api serve`)
5. Verify CLI commands (status, entities, templates, generators)
6. Hit `GET /api/health` and `GET /api/status`
7. Start and stop generators
8. Review console/file outputs
9. Build and run the Docker image

## License

Licensed under the Apache License 2.0. See `LICENSE` for details.
