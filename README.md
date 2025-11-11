# LogForge OSS

Synthetic log generator with an API-first architecture, template-driven generators, and a batteries-included CLI.

## Features

- FastAPI management API with health, status, entity, generator, and template endpoints
- Click-based CLI (`logforge`) for config bootstrap, validation, entities, templates, and generator control
- YAML configuration backed by Pydantic models with `LOGFORGE__SECTION__KEY` environment overrides
- Entity registry and template loader with validation and pluggable outputs
- Logging configured with rotating file handlers plus console output

## Quick Start

```bash
pip install -e ".[dev]"

# bootstrap local state under ~/.logforge
logforge init

# inspect effective configuration
logforge config show

# validate configuration & ensure filesystem layout
logforge config validate

# start the embedded API server
logforge api start

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

## API & Health

```bash
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8080/api/status

# authenticated CLI calls when API key auth is enabled
logforge --api-key "$LOGFORGE_TOKEN" entities list
logforge --api-key "$LOGFORGE_TOKEN" generators start demo
```

Enable API key auth by setting `api.auth.enabled` in the config or exporting `LOGFORGE__API__AUTH__ENABLED=true`.

## Development

```bash
pip install -e ".[dev]"
ruff check src tests
pytest
```

## License

Licensed under the Apache License 2.0. See `LICENSE` for details.
