## LogForge OSS

LogForge is a template-driven synthetic log generator with an API-first architecture.

- **Config-first**: YAML configuration validated by Pydantic models.
- **API**: Embedded FastAPI server with health/status endpoints and optional API key auth.
- **CLI**: Click-based commands for init, config management, and API serving.

### Quick Start

```bash
git clone https://github.com/yourusername/logforge.git
cd logforge
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# bootstrap state under ~/.logforge
logforge init

# inspect configuration
logforge config show

# validate configuration
logforge config validate

# start management API (CTRL+C to stop)
logforge api serve
```

### Configuration

- Default config: `~/.logforge/config.yaml`
- Entities file: `~/.logforge/entities.yaml`
- Templates: `~/.logforge/templates/{default,custom}`
- Environment overrides use `LOGFORGE__SECTION__KEY=value`.

### Health Check

Once the API is running:

```bash
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8080/api/status
```

Set an API key by toggling `api.auth.enabled` in the config or export `LOGFORGE__API__AUTH__ENABLED=true`.

### Development

- Format: `black src tests`
- Lint: `ruff check src tests`
- Tests: `pytest`
