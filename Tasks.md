# LogForge Open-Source Version - Task Decomposition

**Version**: 1.0  
**Date**: 2025-01-15  
**Based On**: LogForge-OSS-Requirements.md v1.0, LogForge-UserStory.md v1.0

---

## 1. Project Overview

LogForge is a synthetic event log generator that produces realistic log data from various systems using a template-based architecture. The open-source version provides a complete, production-ready system with an API-first design (embedded FastAPI server), zero-code template configuration, file-based persistence, thread-based concurrent generation, and comprehensive observability. The system supports multiple output handlers (file, console, HTTP, TCP, syslog), entity registry management for realistic data generation, and community template integration. The CLI serves as a thin wrapper around the management API, ensuring all operations are API-driven and enabling remote control capabilities.

**Key Technical Decisions Needed**:
- CLI framework selection (Click vs Typer)
- Threading model implementation details (ThreadPoolExecutor configuration)
- Template precedence system implementation (custom vs default)
- Output handler retry strategy and buffering mechanism
- Entity registry schema validation approach
- Community API client error handling and caching strategy

---

## 2. Task Hierarchy

# Epic 1: Project Foundation & Infrastructure

## Project Structure & Packaging {Priority: High} [4/4 complete]

- [x] Create Python project structure following module layout from requirements {Priority: High}
  - Implemented: Scaffolded `src/logforge` package tree (cli/core/templates/entities/api/outputs/community/utils) with placeholder modules plus root `__main__`, and added `tests/` hierarchy with placeholder test.
  - Tested: Verified directory creation and placeholder test via filesystem inspection (`find`, `ls`), ensuring pytest will discover scaffolding.
  - Files: `src/logforge/**`, `tests/**`
  - Notes: All modules currently stubs; to be replaced while implementing respective epics.
  - Date: 2025-11-23
  - Acceptance: All directories exist (`src/logforge/`, `tests/`, `examples/`)
  - Dependencies: None
  - Notes: Follow structure in section 15.1 of requirements
  - (User Story Phase 1)

- [x] Configure `pyproject.toml` with dependencies and build system {Priority: High}
  - Implemented: Added `pyproject.toml` with setuptools build backend, project metadata, runtime deps (FastAPI, Typer, Faker, etc.), dev extras (pytest stack, ruff, mypy), and CLI entry point wiring per requirements.
  - Tested: Manual review ensuring spec-aligned dependency list and script entry; ready for `pip install -e .` once code implemented.
  - Files: `pyproject.toml`
  - Notes: Includes `[tool.setuptools]` src-layout config plus pytest defaults for future testing; Click kept since Typer builds atop it.
  - Date: 2025-11-23
  - Acceptance: Package installs via `pip install -e .`, all dependencies resolve
  - Dependencies: Project structure
  - Notes: Include all dependencies from requirements section 10.1

- [x] Set up development dependencies and tooling {Priority: High}
  - Implemented: Added `Makefile`, `ruff.toml`, `mypy.ini`, and Black config in `pyproject.toml`; installed project with `pip install -e ".[dev]"` to ensure runtime/dev deps available.
  - Tested: Ran `ruff check src tests`, `black --check src tests`, `pytest`, and `mypy src` to confirm tooling executes successfully.
  - Files: `Makefile`, `ruff.toml`, `mypy.ini`, `pyproject.toml`
  - Notes: Make targets wrap install/lint/format/test/typecheck workflows for future CI integration.
  - Date: 2025-11-23
  - Acceptance: `pytest`, `black`, `ruff`, `mypy` install and run
  - Dependencies: pyproject.toml
  - Notes: Configure in `[project.optional-dependencies]`

- [x] Create package entry points and CLI command registration {Priority: High}
  - Implemented: Built Typer-based CLI with global context, `--version` flag, subcommand groups (config/templates/entities/generators/outputs), helper messaging, and metadata-driven version lookup. Updated `__main__` entry to run the Typer app.
  - Tested: Added CLI unit tests using `typer.testing.CliRunner` for `--version` and `--help`; ran `ruff`, `black --check`, `pytest`, and `mypy` to verify lint/format/tests/type-checking.
  - Files: `src/logforge/__init__.py`, `src/logforge/__main__.py`, `src/logforge/cli/{__init__,main,helpers,config,templates,entities,generators,outputs}.py`, `tests/unit/test_cli_main.py`
  - Notes: Subcommands still stubs but wired for future API-backed implementations per roadmap.
  - Date: 2025-11-23
  - Acceptance: `logforge --version` and `logforge --help` work
  - Dependencies: Project structure, CLI framework
  - Notes: Use `[project.scripts]` in pyproject.toml

## Configuration Management {Priority: High} [5/6 complete]

- [x] Implement YAML configuration loader with environment variable substitution {Priority: High}
  - Implemented: Added recursive loader in `core/config.py` that reads `config.yaml`, enforces location under `LOGFORGE_HOME`, substitutes `${LOGFORGE_HOME}` and other `${VAR}` tokens, expands `~`, and returns a processed dictionary for later Pydantic validation.
  - Tested: Created `tests/unit/test_config_loader.py` covering env substitution, user path expansion, path safety, and missing-variable errors; ran `ruff`, `black --check`, `pytest`, and `mypy`.
  - Files: `src/logforge/core/config.py`, `tests/unit/test_config_loader.py`, `pyproject.toml`
  - Notes: Added `types-PyYAML` dev dependency for typing support; loader currently uses simple home resolution pending dedicated task.
  - Date: 2025-11-23
  - Acceptance: Loads config.yaml, resolves `${LOGFORGE_HOME}`, validates schema
  - Dependencies: Project structure
  - Notes: Support `${VAR}` and `~/.logforge` expansion

- [x] Create configuration schema validator (Pydantic models) {Priority: High}
  - Implemented: Added Pydantic models for all config sections (`core/config_schema.py`) plus helpers to validate dictionaries and integrated `load_validated_config` in `core/config.py`.
  - Tested: Added unit tests covering valid configs, invalid API port, missing outputs, missing generators, and invalid frequency days; ran `ruff`, `black --check`, `pytest`, and `mypy`.
  - Files: `src/logforge/core/config_schema.py`, `src/logforge/core/config.py`, `tests/unit/test_config_schema.py`
  - Notes: Validation errors now surface as `ConfigError` with precise field context; supports optional future extension.
  - Date: 2025-11-23
  - Acceptance: Invalid configs rejected with clear error messages
  - Dependencies: Configuration loader
  - Notes: Validate all sections (api, engine, entity_registry, templates, outputs, generators)

 - [x] Implement `LOGFORGE_HOME` resolution logic {Priority: High}
  - Implemented: Added `core/home.py` with `resolve_logforge_home` that honors explicit overrides, `LOGFORGE_HOME` env var, service mode flag/user detection, and defaults to `~/.logforge` or `/var/lib/logforge` per requirements; integrated loader to use it.
  - Tested: Added `tests/unit/test_home_resolution.py` covering env overrides, service flag, username detection, and interactive default, plus full suite (`ruff`, `black --check`, `pytest`, `mypy`).
  - Files: `src/logforge/core/home.py`, `src/logforge/core/config.py`, `tests/unit/test_home_resolution.py`
  - Notes: Recognizes `LOGFORGE_SERVICE_MODE` env or user `logforge` as service context; resolves paths to absolute.
  - Date: 2025-11-23
  - Acceptance: Defaults to `~/.logforge` for interactive, `/var/lib/logforge` for service user
  - Dependencies: Configuration loader
  - Notes: Check user context (interactive vs service account)

- [x] Create default configuration generator for `logforge init` {Priority: High}
  - Implemented: Added `core/default_config.py` to assemble default config dictionaries, ensure directory scaffolding, and persist YAML safely (no overwrite unless requested); defaults aligned with spec (templates, outputs, generators).
  - Tested: `tests/unit/test_default_config_generator.py` verifies dict validity, file writing/validation, overwrite protection, and directory creation; ran `ruff`, `black --check`, `pytest`, `mypy`.
  - Files: `src/logforge/core/default_config.py`, `tests/unit/test_default_config_generator.py`
  - Notes: Uses schema validator to guarantee generated config remains compliant as models evolve.
  - Date: 2025-11-23
  - Acceptance: `logforge init` creates valid config.yaml with sensible defaults
  - Dependencies: Configuration schema, LOGFORGE_HOME resolution
  - Notes: Include all required sections with defaults from requirements

- [x] Implement interactive wizard for `logforge init --interactive` {Priority: High}
  - Implemented: Added Typer-based `logforge init` command with `--interactive` wizard prompting for org info, log dir, API port, base rate, and starter templates plus configurable overrides feeding into the default config generator; config/entities files written safely under the resolved LOGFORGE_HOME.
  - Tested: New CLI test covers `logforge init` execution with custom LOGFORGE_HOME; default config generator tests updated for option overrides, file writes, overwrite protection, and entity scaffolding; ran `ruff`, `black --check`, `pytest`, and `mypy`.
  - Files: `src/logforge/cli/main.py`, `src/logforge/core/default_config.py`, `tests/unit/test_cli_main.py`, `tests/unit/test_default_config_generator.py`
  - Notes: Template install prompt currently informational pending future download support.
  - Date: 2025-11-23
  - Acceptance: Wizard prompts for org name, domain, output dir, API port, template install
  - Dependencies: Default config generator
  - Notes: Optional enhancement, can be deferred

  - [x] Create CLI commands: `config show`, `config set`, `config validate` {Priority: High}
    - Implemented: Added Typer subcommands that load/validate config via schema, support JSON/YAML output, mutate dot-path keys, and re-write config safely under LOGFORGE_HOME until API endpoints exist.
    - Tested: New CLI + unit tests (`tests/unit/test_cli_config.py`) covering show/validate/set flows against temp LOGFORGE_HOME; suite (`ruff`, `black --check`, `pytest`, `mypy`) run.
    - Files: `src/logforge/cli/config.py`, `tests/unit/test_cli_config.py`
    - Notes: Currently operates on local files; will switch to API once configuration endpoints land.
    - Date: 2025-11-23
  - Acceptance: Commands work via API calls, display/update config correctly
  - Dependencies: Configuration loader, API endpoints
  - Notes: CLI is thin wrapper around API

## Logging Infrastructure {Priority: High} [3/3 complete]

- [x] Set up Python logging with file rotation {Priority: High}
  - Implemented: Added `utils/logging.py` to configure root logging based on schema, including size/time rotation handlers that honor `${LOGFORGE_HOME}` paths and ensure log files live under the resolved home.
  - Tested: `tests/unit/test_logging_setup.py` verifies log writing and rotation-ready handler creation via real file output; full lint/format/test/type checks executed.
  - Files: `src/logforge/utils/logging.py`, `tests/unit/test_logging_setup.py`
  - Notes: Uses RotatingFileHandler/TimedRotatingFileHandler with size/time parsing helpers.
  - Date: 2025-11-23
  - Acceptance: Logs written to `${LOGFORGE_HOME}/logforge.log` with rotation
  - Dependencies: LOGFORGE_HOME resolution
  - Notes: Use RotatingFileHandler, configurable max_size and backup_count

- [x] Implement structured logging with configurable levels {Priority: High}
  - Implemented: Logging setup honors config-defined level/format; helper `get_logger` centralizes logger creation to enforce consistent formatting.
  - Tested: Logging tests inspect produced log files to confirm messages recorded; `pytest` suite covers context manager behavior.
  - Files: `src/logforge/utils/logging.py`, `tests/unit/test_logging_setup.py`
  - Notes: Format string fully configurable via config schema.
  - Date: 2025-11-23
  - Dependencies: Logging setup
  - Notes: Support format string from config

- [x] Create logging utility module with context managers {Priority: High}
  - Implemented: Introduced `log_context` context manager logging start/complete/failure events and exported `configure_logging`, `get_logger` for reuse.
  - Tested: Logging tests assert context manager emits start/complete markers to log file.
  - Files: `src/logforge/utils/logging.py`, `tests/unit/test_logging_setup.py`
  - Notes: Centralized in `utils/logging.py`
  - Date: 2025-11-23
  - Dependencies: Logging infrastructure
  - Notes: Centralized in `utils/logging.py`

---

# Epic 2: API Server Core

## FastAPI Application Setup {Priority: High}

- [ ] Create FastAPI application skeleton with basic routing
  - Acceptance: Server starts, responds to basic requests
  - Dependencies: Project structure
  - Notes: Base app in `api/server.py`

- [ ] Implement embedded server lifecycle (background thread)
  - Acceptance: Server starts in background thread, doesn't block main process
  - Dependencies: FastAPI app
  - Notes: Use uvicorn in thread, manage lifecycle

- [ ] Create API configuration model (host, port, auth settings)
  - Acceptance: API configurable via config.yaml, defaults to 127.0.0.1:8080
  - Dependencies: Configuration management
  - Notes: Support optional API key authentication

- [ ] Implement API key authentication (optional)
  - Acceptance: When enabled, requires `Authorization: Bearer <key>` header
  - Dependencies: API configuration
  - Notes: Generate key on first run if enabled, store securely

- [ ] Create API startup/shutdown hooks
  - Acceptance: Server initializes dependencies on startup, cleans up on shutdown
  - Dependencies: FastAPI app
  - Notes: Connect to engine, entity registry, template loader

## Health & Status Endpoints {Priority: High}

- [ ] Implement `GET /api/health` endpoint
  - Acceptance: Returns status (healthy/degraded/unhealthy), uptime, generator counts
  - Dependencies: FastAPI app, engine integration
  - Notes: Check all subsystems (generators, entity registry, template cache)

- [ ] Implement `GET /api/status` endpoint
  - Acceptance: Returns detailed status with generator states, system metrics
  - Dependencies: Health endpoint, metrics collection
  - Notes: Include CPU, memory, thread counts

- [ ] Implement `GET /api/metrics` endpoint (Prometheus format)
  - Acceptance: Returns Prometheus-compatible metrics
  - Dependencies: Metrics collection
  - Notes: Counters, gauges, histograms as specified

- [ ] Create health check dependency injection
  - Acceptance: All endpoints can check service health
  - Dependencies: Health endpoint
  - Notes: FastAPI dependency for health validation

## API Error Handling {Priority: Medium}

- [ ] Implement global exception handlers
  - Acceptance: All API errors return consistent JSON format
  - Dependencies: FastAPI app
  - Notes: Standard error response structure

- [ ] Create API response models (Pydantic)
  - Acceptance: All endpoints use typed request/response models
  - Dependencies: FastAPI app
  - Notes: Models in `api/models.py`

---

# Epic 3: Entity Registry System

## Entity Storage Layer {Priority: High}

- [ ] Implement YAML file reader/writer for entities
  - Acceptance: Reads/writes `${LOGFORGE_HOME}/entities.yaml` correctly
  - Dependencies: LOGFORGE_HOME resolution
  - Notes: Atomic writes, handle file locks

- [ ] Create entity schema models (organization, users, devices, services)
  - Acceptance: Pydantic models validate all entity types
  - Dependencies: Project structure
  - Notes: Support custom attributes field

- [ ] Implement in-memory entity cache
  - Acceptance: Entities loaded into memory, fast lookups
  - Dependencies: Entity storage, schema models
  - Notes: Cache in `entities/registry.py`

- [ ] Create auto-save mechanism with configurable interval
  - Acceptance: Changes saved to disk every N seconds (default 60)
  - Dependencies: Entity cache, storage layer
  - Notes: Background thread for periodic saves

- [ ] Implement backup system (N backups on save)
  - Acceptance: Creates backups before overwriting, keeps N copies
  - Dependencies: Entity storage
  - Notes: Configurable backup_count (default 3)

## Entity Validation {Priority: High}

- [ ] Implement entity schema validation
  - Acceptance: Rejects invalid entities (duplicate usernames, invalid IPs, etc.)
  - Dependencies: Entity schema models
  - Notes: Validation in `entities/validator.py`

- [ ] Create validation rules for all entity types
  - Acceptance: Validates emails, IPs, MAC addresses, FQDNs, uniqueness
  - Dependencies: Entity validation
  - Notes: Use regex and standard libraries

- [ ] Implement validation error reporting with line numbers
  - Acceptance: Errors show file path, line number, field, and fix suggestions
  - Dependencies: Entity validation
  - Notes: Parse YAML with line tracking

## Entity Registry Functions {Priority: High}

- [ ] Implement registry functions for template access
  - Acceptance: `get_random_user()`, `get_random_device()`, `get_random_service()` work
  - Dependencies: Entity cache
  - Notes: Functions in `entities/functions.py`, exposed to templates

- [ ] Implement specific entity lookup functions
  - Acceptance: `get_user(name)`, `get_device(hostname)`, etc. work
  - Dependencies: Entity cache
  - Notes: Return None if not found, handle gracefully

- [ ] Implement organization access functions
  - Acceptance: `get_organization()`, `get_organization_field()`, `get_organization_contact()` work
  - Dependencies: Entity cache
  - Notes: Return organization dict or specific fields

## Entity API Endpoints {Priority: High}

- [ ] Implement `GET /api/entities` endpoint
  - Acceptance: Returns organization summary and entity counts
  - Dependencies: Entity registry, API server
  - Notes: Summary view

- [ ] Implement `GET /api/entities/{type}` endpoint
  - Acceptance: Returns list of entities by type (users/devices/services)
  - Dependencies: Entity registry, API server
  - Notes: Support pagination if needed

- [ ] Implement `POST /api/entities` endpoint (create entity)
  - Acceptance: Creates new entity, validates, saves to registry
  - Dependencies: Entity validation, API server
  - Notes: Return created entity or validation errors

## Entity CLI Commands {Priority: Medium}

- [ ] Implement `logforge entities list` command
  - Acceptance: Lists all entities or filtered by type
  - Dependencies: Entity API endpoints
  - Notes: CLI wrapper around API

- [ ] Implement `logforge entities show` command
  - Acceptance: Shows specific entity details
  - Dependencies: Entity API endpoints
  - Notes: Format output nicely

- [ ] Implement `logforge entities add` command (interactive)
  - Acceptance: Interactive prompts for adding entities
  - Dependencies: Entity API endpoints
  - Notes: Validate input before sending to API

- [ ] Implement `logforge entities import` and `export` commands
  - Acceptance: Imports/exports entities.yaml files
  - Dependencies: Entity API endpoints
  - Notes: Validate on import

- [ ] Implement `logforge entities validate` command
  - Acceptance: Validates entities.yaml file and reports errors
  - Dependencies: Entity validation
  - Notes: Can validate without API running

---

# Epic 4: Template System

## Template Loader & Discovery {Priority: High}

- [ ] Implement filesystem template scanner
  - Acceptance: Discovers templates in `${LOGFORGE_HOME}/templates/default/` and `custom/`
  - Dependencies: LOGFORGE_HOME resolution
  - Notes: Recursive directory scanning, follow hierarchy

- [ ] Implement template precedence resolution
  - Acceptance: Checks custom/ first, falls back to default/ (configurable)
  - Dependencies: Template scanner
  - Notes: Support custom_first, default_first, explicit modes

- [ ] Create template metadata parser
  - Acceptance: Parses metadata.yaml files, validates schema
  - Dependencies: Template scanner
  - Notes: Validate against template.schema.json

- [ ] Implement template cache with TTL
  - Acceptance: Caches template metadata, invalidates after TTL
  - Dependencies: Template metadata parser
  - Notes: Configurable cache_ttl (default 3600s)

## Template Rendering Engine {Priority: High}

- [ ] Integrate Jinja2 template engine
  - Acceptance: Renders template.j2 files correctly
  - Dependencies: Template loader
  - Notes: Configure Jinja2 environment

- [ ] Create custom Jinja2 filters (now, format_datetime, random_int, random_choice)
  - Acceptance: All custom filters work in templates
  - Dependencies: Jinja2 integration
  - Notes: Filters in `templates/filters.py`

- [ ] Integrate Faker library for synthetic data
  - Acceptance: `fake` object available in templates, generates realistic data
  - Dependencies: Jinja2 integration
  - Notes: Expose Faker instance as `fake` in template context

- [ ] Create template rendering context builder
  - Acceptance: Context includes registry functions, faker, filters, built-ins
  - Dependencies: Registry functions, Faker, filters
  - Notes: Context in `templates/renderer.py`

- [ ] Implement template variable substitution
  - Acceptance: Generator-level variables override template defaults
  - Dependencies: Template rendering
  - Notes: Support context overrides from generator config

## Template Validation {Priority: High}

- [ ] Implement Jinja2 syntax validation
  - Acceptance: Catches syntax errors before runtime
  - Dependencies: Template loader
  - Notes: Use Jinja2 parser

- [ ] Implement template safety checks (no eval, exec, file access)
  - Acceptance: Rejects unsafe template operations
  - Dependencies: Template validation
  - Notes: Sandbox Jinja2 environment

- [ ] Implement metadata validation against schema
  - Acceptance: Validates metadata.yaml against template.schema.json
  - Dependencies: Template metadata parser
  - Notes: Use JSON schema validator

- [ ] Create `logforge templates validate` command
  - Acceptance: Validates template files and reports errors
  - Dependencies: Template validation
  - Notes: Can validate without API running

## Template Customization Workflow {Priority: Medium}

- [ ] Implement `logforge templates customize` command
  - Acceptance: Copies default template to custom/, preserves structure
  - Dependencies: Template loader, file operations
  - Notes: Sets up precedence override automatically

- [ ] Implement `logforge templates diff` command
  - Acceptance: Shows differences between custom and default versions
  - Dependencies: Template loader
  - Notes: Use configured diff tool or built-in

- [ ] Implement `logforge templates merge` command
  - Acceptance: Attempts to merge default changes into custom (interactive)
  - Dependencies: Template diff
  - Notes: Git-style merge with conflict resolution

- [ ] Implement `logforge templates revert` command
  - Acceptance: Removes custom version, reverts to default
  - Dependencies: Template loader
  - Notes: Prompts for confirmation

- [ ] Implement `logforge templates create` command (interactive wizard)
  - Acceptance: Interactive template creator for custom templates
  - Dependencies: Template validation
  - Notes: Creates in custom/ directory

## Template API Endpoints {Priority: High}

- [ ] Implement `GET /api/templates` endpoint
  - Acceptance: Returns list of all templates with metadata
  - Dependencies: Template loader, API server
  - Notes: Include local/remote version info

- [ ] Implement `GET /api/templates/{template_id}` endpoint
  - Acceptance: Returns detailed template information
  - Dependencies: Template loader, API server
  - Notes: Show both default and custom if both exist

## Community Integration {Priority: Medium}

- [ ] Create community API client (HTTP client)
  - Acceptance: Connects to `https://api.logforge.io/v1`, handles errors
  - Dependencies: HTTP client library
  - Notes: Client in `community/client.py`

- [ ] Implement template search functionality
  - Acceptance: Searches remote templates by query, vendor, product
  - Dependencies: Community API client
  - Notes: Support pagination

- [ ] Implement template package downloader
  - Acceptance: Downloads .forge packages, verifies signatures
  - Dependencies: Community API client
  - Notes: Handle network errors, retries

- [ ] Implement template package installer
  - Acceptance: Extracts .forge packages to default/ directory
  - Dependencies: Package downloader
  - Notes: Validate package structure, update registry

- [ ] Implement template update checker
  - Acceptance: Checks for remote updates, compares versions
  - Dependencies: Community API client, template loader
  - Notes: Configurable auto_update_check

- [ ] Implement `logforge templates list` command
  - Acceptance: Lists templates with location and version info
  - Dependencies: Template loader, community client
  - Notes: Show precedence indicators

- [ ] Implement `logforge templates search` command
  - Acceptance: Searches community templates
  - Dependencies: Community API client
  - Notes: Format results nicely

- [ ] Implement `logforge templates install` command
  - Acceptance: Installs templates from repository or local .forge file
  - Dependencies: Package installer
  - Notes: Warn if custom version exists

- [ ] Implement `logforge templates update` command
  - Acceptance: Updates outdated default/ templates
  - Dependencies: Update checker, package installer
  - Notes: Never touches custom/ templates

- [ ] Implement `logforge templates download` command (for air-gapped)
  - Acceptance: Downloads .forge packages to local path
  - Dependencies: Package downloader
  - Notes: For offline installation

---

# Epic 5: Event Generation Engine

## Generator Core Class {Priority: High}

- [ ] Create Generator class with state machine
  - Acceptance: States (STOPPED, STARTING, RUNNING, DEGRADED, ERROR) work correctly
  - Dependencies: Project structure
  - Notes: State machine in `core/generator.py`

- [ ] Implement generator lifecycle methods (start, stop, restart)
  - Acceptance: Generators transition states correctly, cleanup on stop
  - Dependencies: Generator class
  - Notes: Async methods for non-blocking operations

- [ ] Implement generator event generation loop
  - Acceptance: Generates events at configured frequency
  - Dependencies: Generator class, template renderer
  - Notes: Main generation loop in separate thread

- [ ] Implement frequency calculation with time-based variation
  - Acceptance: Adjusts rate based on time of day, day of week multipliers
  - Dependencies: Generator class
  - Notes: Frequency logic in `core/frequency.py`

- [ ] Implement generator statistics tracking
  - Acceptance: Tracks events_generated, errors, uptime, last_event
  - Dependencies: Generator class
  - Notes: Thread-safe counters

## Thread Pool Management {Priority: High}

- [ ] Implement ThreadPoolExecutor with dynamic sizing
  - Acceptance: Auto-sizes based on CPU cores × 5 (configurable)
  - Dependencies: Generator class
  - Notes: Engine manages pool in `core/engine.py`

- [ ] Implement generator thread assignment
  - Acceptance: Each generator runs in separate thread from pool
  - Dependencies: Thread pool
  - Notes: Coordinate thread lifecycle

- [ ] Implement graceful shutdown for all generators
  - Acceptance: All generators stop cleanly, threads join within timeout
  - Dependencies: Generator lifecycle, thread pool
  - Notes: Handle stuck threads

## Generator Configuration {Priority: High}

- [ ] Create generator configuration model
  - Acceptance: Parses generator config from config.yaml
  - Dependencies: Configuration management
  - Notes: Support name, template, enabled, frequency, outputs

- [ ] Implement generator-to-output mapping
  - Acceptance: Generators route events to configured outputs
  - Dependencies: Generator class, output handlers
  - Notes: Multiple outputs per generator

- [ ] Implement generator-to-template binding
  - Acceptance: Generators load and use specified templates
  - Dependencies: Generator class, template loader
  - Notes: Validate template exists before starting

## Error Recovery & Handling {Priority: High}

- [ ] Implement smart error recovery for template rendering failures
  - Acceptance: Transient errors retry, config errors stay in ERROR state
  - Dependencies: Generator class
  - Notes: Distinguish error types (EntityNotFound vs TemplateSyntaxError)

- [ ] Implement output failure handling (DEGRADED state)
  - Acceptance: Output failures transition generator to DEGRADED, retry with backoff
  - Dependencies: Generator class, output handlers
  - Notes: Continue generating, buffer events

- [ ] Implement entity registry corruption handling
  - Acceptance: Invalid entities.yaml transitions generators to ERROR, prevents new starts
  - Dependencies: Generator class, entity validation
  - Notes: Attempt backup restore if enabled

- [ ] Create error logging with context
  - Acceptance: Errors logged with template location, line number, context
  - Dependencies: Logging infrastructure
  - Notes: Detailed error messages for debugging

## Generator API Endpoints {Priority: High}

- [ ] Implement `GET /api/generators` endpoint
  - Acceptance: Returns list of all generators with states
  - Dependencies: Generator engine, API server
  - Notes: Summary view

- [ ] Implement `GET /api/generators/{name}` endpoint
  - Acceptance: Returns detailed generator information
  - Dependencies: Generator engine, API server
  - Notes: Include statistics, frequency, outputs

- [ ] Implement `POST /api/generators/{name}/start` endpoint
  - Acceptance: Starts generator, returns new state
  - Dependencies: Generator engine, API server
  - Notes: Validate template exists, outputs available

- [ ] Implement `POST /api/generators/{name}/stop` endpoint
  - Acceptance: Stops generator gracefully
  - Dependencies: Generator engine, API server
  - Notes: Wait for thread to finish

- [ ] Implement `POST /api/generators/{name}/restart` endpoint
  - Acceptance: Restarts generator (stop then start)
  - Dependencies: Start/stop endpoints
  - Notes: Atomic operation

## Generator CLI Commands {Priority: Medium}

- [ ] Implement `logforge generators list` command
  - Acceptance: Lists all generators with status
  - Dependencies: Generator API endpoints
  - Notes: Format as table

- [ ] Implement `logforge generators add` command (interactive)
  - Acceptance: Interactive prompts for creating generator from template
  - Dependencies: Generator API endpoints, template loader
  - Notes: Select outputs, configure frequency

- [ ] Implement `logforge generators apply` command (bulk YAML)
  - Acceptance: Creates multiple generators from YAML file
  - Dependencies: Generator API endpoints
  - Notes: Validate before applying

- [ ] Implement `logforge generators validate` command
  - Acceptance: Validates generator YAML configuration
  - Dependencies: Generator configuration model
  - Notes: Check templates exist, outputs valid

- [ ] Implement `logforge generators status` command
  - Acceptance: Shows runtime status of generators
  - Dependencies: Generator API endpoints
  - Notes: Real-time metrics

- [ ] Implement `logforge generators metrics` command
  - Acceptance: Shows detailed metrics for specific generator
  - Dependencies: Generator API endpoints
  - Notes: Events, rates, entity usage

- [ ] Implement `logforge generators enable/disable` commands
  - Acceptance: Enables/disables generators without deleting
  - Dependencies: Generator API endpoints
  - Notes: Non-destructive

- [ ] Implement `logforge generators reload` command
  - Acceptance: Reloads generator configuration from config.yaml
  - Dependencies: Generator API endpoints
  - Notes: Apply config changes without restart

---

# Epic 6: Output Handlers

## Base Output Handler {Priority: High}

- [ ] Create abstract OutputHandler base class
  - Acceptance: Defines interface (write, write_batch, close)
  - Dependencies: Project structure
  - Notes: Base class in `outputs/base.py`

- [ ] Implement output handler factory
  - Acceptance: Creates appropriate handler based on type (file, console, http, etc.)
  - Dependencies: Base handler, output configuration
  - Notes: Factory in `outputs/__init__.py`

- [ ] Implement output configuration model
  - Acceptance: Parses output definitions from config.yaml
  - Dependencies: Configuration management
  - Notes: Support all output types and their specific configs

## File Output Handler {Priority: High}

- [ ] Implement file output with variable substitution
  - Acceptance: Supports `{generator}`, `{date}`, `{timestamp}` in paths
  - Dependencies: Base handler
  - Notes: Handler in `outputs/file.py`

- [ ] Implement file rotation (size-based)
  - Acceptance: Rotates when file exceeds max_size
  - Dependencies: File output
  - Notes: Atomic rotation, compressed archives

- [ ] Implement file rotation (time-based)
  - Acceptance: Rotates based on time intervals (daily, etc.)
  - Dependencies: File output
  - Notes: Configurable max_age

- [ ] Implement rotated file compression
  - Acceptance: Compresses rotated files with gzip
  - Dependencies: File rotation
  - Notes: .gz extension

- [ ] Implement per-generator file separation
  - Acceptance: Each generator writes to separate file by default
  - Dependencies: File output
  - Notes: Configurable filename pattern

## Console Output Handler {Priority: Medium}

- [ ] Implement console output with JSON format
  - Acceptance: Outputs JSONL (one JSON object per line)
  - Dependencies: Base handler
  - Notes: Handler in `outputs/console.py`

- [ ] Implement console output with text format
  - Acceptance: Outputs human-readable formatted text
  - Dependencies: Console output
  - Notes: Pretty formatting

- [ ] Implement stdout/stderr selection
  - Acceptance: Configurable stream (stdout or stderr)
  - Dependencies: Console output
  - Notes: Default stdout

## HTTP Output Handler {Priority: High}

- [ ] Implement HTTP output with POST requests
  - Acceptance: Sends events via HTTP POST to configured URL
  - Dependencies: Base handler
  - Notes: Handler in `outputs/http.py`

- [ ] Implement event batching
  - Acceptance: Batches events (size-based or time-based triggers)
  - Dependencies: HTTP output
  - Notes: Configurable batch_size and batch_interval

- [ ] Implement HTTP headers with environment variable substitution
  - Acceptance: Supports `${VAR_NAME}` in headers
  - Dependencies: HTTP output
  - Notes: Resolve env vars at runtime

- [ ] Implement JSON array wrapping for batches
  - Acceptance: Wraps batched events in JSON array
  - Dependencies: HTTP batching
  - Notes: Single events as objects

- [ ] Implement request timeout handling
  - Acceptance: Configurable timeout, handles timeouts gracefully
  - Dependencies: HTTP output
  - Notes: Default 30s

## TCP Output Handler {Priority: Medium}

- [ ] Implement TCP socket output
  - Acceptance: Connects to TCP server, sends events
  - Dependencies: Base handler
  - Notes: Handler in `outputs/tcp.py`

- [ ] Implement event delimiter configuration
  - Acceptance: Configurable delimiter (default newline)
  - Dependencies: TCP output
  - Notes: Delimiter between events

- [ ] Implement TCP keepalive
  - Acceptance: Maintains connection with keepalive
  - Dependencies: TCP output
  - Notes: Configurable

## Syslog Output Handler {Priority: Medium}

- [ ] Implement syslog protocol output (RFC 5424)
  - Acceptance: Formats events as RFC 5424 syslog messages
  - Dependencies: Base handler
  - Notes: Handler in `outputs/syslog.py`

- [ ] Implement syslog protocol output (RFC 3164)
  - Acceptance: Formats events as RFC 3164 syslog messages
  - Dependencies: Syslog output
  - Notes: Legacy format support

- [ ] Implement syslog facility and severity configuration
  - Acceptance: Configurable facility and severity
  - Dependencies: Syslog output
  - Notes: Default local0, info

- [ ] Implement TCP/UDP protocol selection
  - Acceptance: Supports TCP, UDP, TLS protocols
  - Dependencies: Syslog output
  - Notes: Configurable protocol

## Retry Logic & Buffering {Priority: High}

- [ ] Implement exponential backoff retry mechanism
  - Acceptance: Retries with increasing delays (5s, 10s, 20s, etc.)
  - Dependencies: All output handlers
  - Notes: Configurable max_attempts, retry_interval, backoff_multiplier, max_backoff

- [ ] Implement event buffering during outages
  - Acceptance: Buffers events in memory when output unavailable
  - Dependencies: All output handlers
  - Notes: Configurable buffer_size (default 10000)

- [ ] Implement buffer overflow handling
  - Acceptance: Drops oldest events when buffer full, logs warning
  - Dependencies: Event buffering
  - Notes: Prevent memory exhaustion

- [ ] Implement buffer flush on recovery
  - Acceptance: Flushes buffered events when output recovers
  - Dependencies: Event buffering, retry logic
  - Notes: Maintain order if possible

## Output API Endpoints {Priority: Medium}

- [ ] Implement `GET /api/outputs` endpoint
  - Acceptance: Returns list of all outputs with status
  - Dependencies: Output handlers, API server
  - Notes: Include connection status, metrics

- [ ] Implement output test functionality
  - Acceptance: Tests output connectivity and configuration
  - Dependencies: Output handlers
  - Notes: Send test event, verify delivery

## Output CLI Commands {Priority: Medium}

- [ ] Implement `logforge outputs list` command
  - Acceptance: Lists all outputs with status and metrics
  - Dependencies: Output API endpoints
  - Notes: Format as table

- [ ] Implement `logforge outputs add` command (interactive)
  - Acceptance: Interactive prompts for adding output
  - Dependencies: Output API endpoints
  - Notes: Test connection before saving

- [ ] Implement `logforge outputs test` command
  - Acceptance: Tests output connectivity
  - Dependencies: Output test functionality
  - Notes: Detailed test results

- [ ] Implement `logforge outputs enable/disable` commands
  - Acceptance: Enables/disables outputs
  - Dependencies: Output API endpoints
  - Notes: Non-destructive

- [ ] Implement `logforge outputs metrics` command
  - Acceptance: Shows detailed output metrics
  - Dependencies: Output API endpoints
  - Notes: Events sent, errors, retries

---

# Epic 7: CLI Interface

## CLI Framework Setup {Priority: High}

- [ ] Choose and integrate CLI framework (Click or Typer)
  - Acceptance: CLI framework installed and configured
  - Dependencies: Project structure
  - Notes: Decision needed - see Decision Log

- [ ] Create CLI command structure and grouping
  - Acceptance: Commands organized (templates, generators, entities, outputs, etc.)
  - Dependencies: CLI framework
  - Notes: Follow structure from requirements section 9.2

- [ ] Implement API connection handling (local/remote)
  - Acceptance: CLI connects to API via `--api-url` or env var
  - Dependencies: CLI framework, API server
  - Notes: Default localhost:8080

- [ ] Implement API key handling for CLI
  - Acceptance: CLI sends API key in Authorization header if configured
  - Dependencies: API connection
  - Notes: From `--api-key` or env var

- [ ] Implement service health check before commands
  - Acceptance: CLI checks API health, exits with error if unavailable
  - Dependencies: API connection, health endpoint
  - Notes: Error message suggests starting service

## Service Management Commands {Priority: High}

- [ ] Implement `logforge start` command (foreground)
  - Acceptance: Starts service in foreground, shows logs
  - Dependencies: API server, engine
  - Notes: Ctrl+C stops gracefully

- [ ] Implement `logforge stop` command
  - Acceptance: Stops foreground service gracefully
  - Dependencies: Service start
  - Notes: Only works for foreground process

- [ ] Implement `logforge service install` command
  - Acceptance: Creates systemd service file, sets up user/directories
  - Dependencies: Systemd available
  - Notes: Creates /etc/systemd/system/logforge.service

- [ ] Implement `logforge service start/stop/restart/status` commands
  - Acceptance: Wrappers around systemctl commands
  - Dependencies: Service install
  - Notes: Use systemctl under the hood

- [ ] Implement `logforge status` command
  - Acceptance: Shows overall service status, generators, outputs
  - Dependencies: Status API endpoint
  - Notes: Format as table, support --watch

- [ ] Implement `logforge health` command
  - Acceptance: Comprehensive health check with suggestions
  - Dependencies: Health API endpoint
  - Notes: Check all subsystems

## Monitoring Commands {Priority: Medium}

- [ ] Implement `logforge metrics` command
  - Acceptance: Shows aggregated metrics (last hour)
  - Dependencies: Metrics API endpoint
  - Notes: Format nicely, show by generator/output

- [ ] Implement `logforge logs` command
  - Acceptance: Views service logs with filtering
  - Dependencies: Logging infrastructure
  - Notes: Support --follow, --level, --generator, --since

## One-Shot Generation Command {Priority: Medium}

- [ ] Implement `logforge generate once` command
  - Acceptance: Generates N events to file or output, exits
  - Dependencies: Generator engine, template renderer
  - Notes: For ad-hoc testing, doesn't require service running

- [ ] Implement historical event generation (backdated)
  - Acceptance: Generates events with timestamps in specified time range
  - Dependencies: One-shot generation
  - Notes: Distribute events across time range

- [ ] Implement stdout output for one-shot
  - Acceptance: Can output to stdout for piping
  - Dependencies: One-shot generation
  - Notes: Support --format json

## CLI Output Formatting {Priority: Medium}

- [ ] Implement table formatting for list commands
  - Acceptance: Commands output formatted tables
  - Dependencies: CLI commands
  - Notes: Use library like tabulate or rich

- [ ] Implement JSON output option (`--output json`)
  - Acceptance: Commands support JSON output for scripting
  - Dependencies: CLI commands
  - Notes: Machine-readable format

- [ ] Implement progress bars for long operations
  - Acceptance: Shows progress for install, generate operations
  - Dependencies: CLI commands
  - Notes: Use library like tqdm or rich

---

# Epic 8: Metrics & Observability

## Metrics Collection {Priority: High}

- [ ] Implement Prometheus metrics collection
  - Acceptance: Collects counters, gauges, histograms
  - Dependencies: prometheus-client library
  - Notes: Metrics in `utils/metrics.py`

- [ ] Implement event generation metrics
  - Acceptance: Tracks events_generated_total, errors_total per generator
  - Dependencies: Metrics collection
  - Notes: Counter metrics

- [ ] Implement system metrics
  - Acceptance: Tracks generators_running, memory_usage_bytes, CPU percent
  - Dependencies: Metrics collection
  - Notes: Gauge metrics, update periodically

- [ ] Implement performance metrics
  - Acceptance: Tracks template_render_seconds, output_latency_seconds
  - Dependencies: Metrics collection
  - Notes: Histogram metrics

- [ ] Expose metrics via `/api/metrics` endpoint
  - Acceptance: Returns Prometheus-compatible format
  - Dependencies: Metrics collection, API server
  - Notes: Text format, Prometheus can scrape

---

# Epic 9: Deployment & Packaging

## Docker Deployment {Priority: Medium}

- [ ] Create Dockerfile with multi-stage build
  - Acceptance: Docker image builds successfully
  - Dependencies: Python package
  - Notes: Follow requirements section 10.2

- [ ] Create docker-compose.yml with examples
  - Acceptance: docker-compose up works, service starts
  - Dependencies: Dockerfile
  - Notes: Include volumes, environment variables

- [ ] Implement health check in Dockerfile
  - Acceptance: Docker health check uses API health endpoint
  - Dependencies: Dockerfile, health endpoint
  - Notes: HEALTHCHECK instruction

- [ ] Create logforge user in container
  - Acceptance: Container runs as non-root user
  - Dependencies: Dockerfile
  - Notes: User ID 1000, proper permissions

## Systemd Integration {Priority: Low}

- [ ] Create systemd service unit file
  - Acceptance: Service file follows requirements section 10.3
  - Dependencies: Python package
  - Notes: Template for installation

- [ ] Implement service installation logic
  - Acceptance: `logforge service install` creates service file
  - Dependencies: Service unit file, CLI commands
  - Notes: Sets permissions, creates directories

## PyPI Packaging {Priority: Medium}

- [ ] Configure package metadata for PyPI
  - Acceptance: Package can be uploaded to PyPI
  - Dependencies: pyproject.toml
  - Notes: All required metadata present

- [ ] Create release build process
  - Acceptance: Can build wheel and source distribution
  - Dependencies: Package configuration
  - Notes: Use `python -m build`

- [ ] Test package installation from wheel
  - Acceptance: Package installs cleanly via pip
  - Dependencies: Package build
  - Notes: Test in clean environment

---

# Epic 10: Testing & Quality

## Unit Tests {Priority: High}

- [ ] Set up pytest test framework
  - Acceptance: pytest runs, finds tests
  - Dependencies: Development dependencies
  - Notes: Configure pytest.ini

- [ ] Write unit tests for template rendering
  - Acceptance: Tests verify template rendering with various inputs
  - Dependencies: Template system
  - Notes: Test all filters, registry functions

- [ ] Write unit tests for entity registry
  - Acceptance: Tests verify CRUD operations, validation
  - Dependencies: Entity registry
  - Notes: Test all entity types

- [ ] Write unit tests for configuration management
  - Acceptance: Tests verify config loading, validation, defaults
  - Dependencies: Configuration management
  - Notes: Test edge cases

- [ ] Write unit tests for output handlers
  - Acceptance: Tests verify each output type works correctly
  - Dependencies: Output handlers
  - Notes: Mock external dependencies

- [ ] Write unit tests for API endpoints
  - Acceptance: Tests verify all endpoints return correct responses
  - Dependencies: API server
  - Notes: Use httpx or similar for testing

- [ ] Write unit tests for generator state machine
  - Acceptance: Tests verify all state transitions
  - Dependencies: Generator engine
  - Notes: Test error cases

- [ ] Write unit tests for frequency calculation
  - Acceptance: Tests verify time-based rate adjustments
  - Dependencies: Frequency logic
  - Notes: Test various time patterns

## Integration Tests {Priority: High}

- [ ] Write integration tests for generator lifecycle
  - Acceptance: Tests verify generators start/stop with real templates
  - Dependencies: All core components
  - Notes: End-to-end generator flow

- [ ] Write integration tests for output handler retry logic
  - Acceptance: Tests verify retry and buffering during outages
  - Dependencies: Output handlers, generator engine
  - Notes: Mock network failures

- [ ] Write integration tests for community API client
  - Acceptance: Tests verify template download and installation
  - Dependencies: Community client
  - Notes: Mock HTTP responses

- [ ] Write integration tests for CLI commands
  - Acceptance: Tests verify CLI commands work end-to-end
  - Dependencies: CLI, API server
  - Notes: Test with subprocess or click.testing

- [ ] Write integration tests for multi-generator concurrency
  - Acceptance: Tests verify multiple generators run simultaneously
  - Dependencies: Generator engine, thread pool
  - Notes: Verify no race conditions

## End-to-End Tests {Priority: Medium}

- [ ] Write E2E test for complete workflow
  - Acceptance: Test: init → install templates → start generators → verify output
  - Dependencies: All components
  - Notes: Full user journey

- [ ] Write E2E test for Docker deployment
  - Acceptance: Test: build image → run container → verify service
  - Dependencies: Docker setup
  - Notes: Test in CI

- [ ] Write E2E test for API authentication
  - Acceptance: Test: enable auth → verify API key required
  - Dependencies: API authentication
  - Notes: Test with and without key

## Test Coverage {Priority: High}

- [ ] Configure pytest-cov for coverage reporting
  - Acceptance: Coverage reports generated
  - Dependencies: pytest setup
  - Notes: Target 80% minimum

- [ ] Achieve 100% coverage for critical paths
  - Acceptance: Generator lifecycle, error handling fully covered
  - Dependencies: Unit tests
  - Notes: Focus on error paths

- [ ] Set up coverage reporting in CI
  - Acceptance: Coverage reported in CI pipeline
  - Dependencies: Coverage configuration
  - Notes: Fail if below threshold

---

# Epic 11: Documentation

## README & Quick Start {Priority: High}

- [ ] Create comprehensive README.md
  - Acceptance: README includes installation, quick start, examples
  - Dependencies: None
  - Notes: Follow requirements section 10.1

- [ ] Create quick start guide
  - Acceptance: User can go from install to generating logs in <5 minutes
  - Dependencies: README
  - Notes: Step-by-step with examples

- [ ] Create installation instructions
  - Acceptance: Clear instructions for pip, Docker, systemd
  - Dependencies: README
  - Notes: Include prerequisites

## API Documentation {Priority: High}

- [ ] Generate OpenAPI/Swagger documentation
  - Acceptance: API docs available at `/docs` endpoint
  - Dependencies: FastAPI app
  - Notes: FastAPI auto-generates from code

- [ ] Document all API endpoints
  - Acceptance: All endpoints have descriptions, examples
  - Dependencies: API server
  - Notes: Use FastAPI docstrings

## Template Development Guide {Priority: Medium}

- [ ] Create template development guide
  - Acceptance: Guide explains how to create custom templates
  - Dependencies: Template system
  - Notes: Include examples, best practices

- [ ] Document template metadata schema
  - Acceptance: Complete reference for metadata.yaml fields
  - Dependencies: Template system
  - Notes: Include all fields and constraints

- [ ] Create template examples (2-3 bundled)
  - Acceptance: Example templates work out of the box
  - Dependencies: Template system
  - Notes: Include in examples/ directory

## User Documentation {Priority: Medium}

- [ ] Create CLI command reference
  - Acceptance: All commands documented with examples
  - Dependencies: CLI commands
  - Notes: Can be auto-generated from help text

- [ ] Create configuration reference
  - Acceptance: All config options documented with defaults
  - Dependencies: Configuration management
  - Notes: Include examples for each section

- [ ] Create troubleshooting guide
  - Acceptance: Common errors and solutions documented
  - Dependencies: Error handling
  - Notes: Based on error scenarios from user story

- [ ] Create deployment guide
  - Acceptance: Docker and systemd deployment documented
  - Dependencies: Deployment setup
  - Notes: Include production considerations

---

# Epic 12: Example Templates & Entities

## Example Templates {Priority: Medium}

- [ ] Create example Windows Security Event Log template
  - Acceptance: Template generates realistic Windows security events
  - Dependencies: Template system
  - Notes: Use existing examples as reference

- [ ] Create example Palo Alto firewall template
  - Acceptance: Template generates realistic firewall logs
  - Dependencies: Template system
  - Notes: Use existing examples as reference

- [ ] Create example entity registry file
  - Acceptance: Sample entities.yaml with realistic data
  - Dependencies: Entity registry
  - Notes: Include in examples/ directory

- [ ] Validate all example templates
  - Acceptance: All examples pass validation
  - Dependencies: Example templates, template validation
  - Notes: Test rendering

---

## 3. Decision Log

### Decision: CLI Framework Selection

**Context**: Need to choose between Click and Typer for CLI implementation. Both are Python CLI frameworks with different approaches.

**Options**: 
- Option A: Click - Mature, widely used, decorator-based, extensive ecosystem
- Option B: Typer - Modern, type-hint based, built on Click, better IDE support

**Decision**: Typer (pending confirmation)

**Rationale**: Typer provides better type safety, cleaner code with type hints, and modern Python practices. Built on Click so has compatibility. Better developer experience with IDE autocomplete.

**Implications**: All CLI commands use Typer, type hints required for all command functions, may need to handle Click compatibility for some advanced features.

**Revisit If**: Type hints prove problematic, or need Click-specific features not available in Typer.

---

### Decision: Template Precedence System Implementation

**Context**: Need to implement custom/ vs default/ template resolution. Requirements specify custom_first as default, but need to decide on implementation approach.

**Options**:
- Option A: Filesystem-based resolution (check custom/ first, fall back to default/)
- Option B: Registry-based resolution (maintain index of template locations)
- Option C: Hybrid (filesystem with in-memory cache)

**Decision**: Option C - Hybrid approach (pending confirmation)

**Rationale**: Filesystem-based is simple and transparent, but caching improves performance. Hybrid gives best of both - simple filesystem semantics with performance optimization.

**Implications**: Template loader must scan both directories, maintain cache of resolved paths, invalidate cache on template changes.

**Revisit If**: Performance issues with filesystem scanning, or need more complex resolution rules.

---

### Decision: Threading Model for Generators

**Context**: Requirements specify ThreadPoolExecutor with dynamic sizing. Need to decide on thread management strategy.

**Options**:
- Option A: One thread per generator (simple, predictable)
- Option B: ThreadPoolExecutor with shared pool (efficient, dynamic)
- Option C: Async/await with asyncio (modern, but more complex)

**Decision**: Option B - ThreadPoolExecutor with shared pool (as specified)

**Rationale**: Matches requirements exactly, provides good resource utilization, Python standard library, proven approach. ThreadPoolExecutor handles thread lifecycle automatically.

**Implications**: Must manage thread assignment, ensure thread-safe operations, handle graceful shutdown of all threads.

**Revisit If**: Performance issues, or need async I/O for outputs (would require asyncio).

---

### Decision: Output Handler Retry Strategy

**Context**: Requirements specify exponential backoff with unlimited retries by default. Need to decide on retry implementation details.

**Options**:
- Option A: Per-handler retry logic (each handler implements own retry)
- Option B: Centralized retry manager (shared retry logic)
- Option C: Library-based (use tenacity or similar)

**Decision**: Option B - Centralized retry manager (pending confirmation)

**Rationale**: Consistent retry behavior across all handlers, easier to test and maintain, configurable per-handler but shared implementation.

**Implications**: Create retry manager utility, all handlers use it, must handle different error types appropriately.

**Revisit If**: Need handler-specific retry logic, or retry library provides better features.

---

### Decision: Entity Registry Schema Validation Approach

**Context**: Need to validate entity registry YAML against schema. Multiple approaches possible.

**Options**:
- Option A: Pydantic models with validation (type-safe, Python-native)
- Option B: JSON Schema validation (standard, language-agnostic)
- Option C: Custom validation functions (flexible, but more code)

**Decision**: Option A - Pydantic models (pending confirmation)

**Rationale**: Already using Pydantic for API models, consistent approach, excellent error messages, type safety, easy to extend.

**Implications**: All entity types must have Pydantic models, validation happens on load, clear error messages with field-level details.

**Revisit If**: Need to share schema with other tools, or JSON Schema provides better validation features.

---

### Decision: Community API Client Error Handling

**Context**: Community API client needs robust error handling for network issues, timeouts, etc.

**Options**:
- Option A: Fail-fast (raise exceptions immediately)
- Option B: Retry with backoff (automatic retries)
- Option C: Degraded mode (cache results, work offline)

**Decision**: Option C - Degraded mode with caching (pending confirmation)

**Rationale**: Users may work in air-gapped environments, should gracefully handle network failures, cache template metadata for offline use.

**Implications**: Implement caching layer, detect network failures, provide clear error messages, support offline template operations.

**Revisit If**: Network reliability is always guaranteed, or retry logic is sufficient.

---

### Decision: Configuration File Location Enforcement

**Context**: Requirements specify all config must be under LOGFORGE_HOME. Need to decide on enforcement strategy.

**Options**:
- Option A: Strict validation (reject paths outside LOGFORGE_HOME)
- Option B: Warning only (allow but warn)
- Option C: Auto-relocate (move configs to LOGFORGE_HOME)

**Decision**: Option A - Strict validation (as specified)

**Rationale**: Requirements explicitly state "CLI refuses to mutate configuration outside that root". Security and consistency benefits.

**Implications**: Validate all file paths in config, reject invalid paths with clear error, update CLI to enforce.

**Revisit If**: Users need flexibility for special deployment scenarios.

---

## 4. Validation Checklist

- [x] All requirements sections covered (1-16 from requirements doc)
- [x] No duplicate or orphaned tasks
- [x] Dependencies mapped (explicit dependencies in each task)
- [x] Major decisions documented with rationale (7 decisions in Decision Log)
- [x] Tasks are independently actionable (each task has clear acceptance criteria)
- [x] User stories referenced where applicable (Phase references in relevant tasks)
- [x] Priorities assigned (High/Medium/Low based on blocking nature)
- [x] Development phases aligned (tasks organized by epic, matching phase structure)

---

## 5. Notes & Clarifications Needed

### Requirements Clarifications

1. **Template Package Format**: Requirements mention `.forge` files but don't specify exact archive format. Assumed tar.gz based on context, but should confirm.

2. **API Server Lifecycle**: Requirements state "auto-started with service" but also mention optional disable. Need clarification on when API can be disabled if generators require it.

3. **Entity Registry Backup Restore**: Requirements mention attempting backup restore on corruption, but don't specify automatic vs manual. Assumed automatic with user notification.

4. **Output Handler TLS**: Requirements mention TLS for syslog but don't specify certificate handling. Need to decide on certificate validation approach.

5. **Community API Authentication**: Requirements don't specify if community API requires authentication. Assumed public API, but should confirm.

6. **Template Versioning**: Requirements mention version in metadata but don't specify version comparison logic for updates. Need to clarify semver handling.

7. **Generator Frequency Calculation**: Requirements specify time-based multipliers but don't specify exact calculation (average over period vs instant rate). Need to clarify implementation.

---

**End of Tasks.md**

---
# Development Log

## 2025-11-23
- ✅ Completed: Project structure scaffolding (Project Structure & Packaging)
  - Created full `src/logforge` module tree with placeholder files plus `tests/` skeleton and placeholder unit test to unblock future tasks.
- ✅ Completed: pyproject configuration (Project Structure & Packaging)
  - Established setuptools/pyproject metadata, runtime + dev dependencies, CLI entry point, and pytest defaults to enable editable installs and future tooling setup.
- ✅ Completed: Dev tooling setup (Project Structure & Packaging)
  - Added Makefile + lint/typecheck configs, installed dev dependencies, and validated `ruff`, `black`, `pytest`, `mypy` runs for baseline CI readiness.
- ✅ Completed: CLI entry & version command (Project Structure & Packaging)
  - Delivered Typer CLI scaffold (`logforge --help/--version`), subcommand grouping, helper messaging, unit tests, and metadata-driven `__version__` propagation.
  - ✅ Completed: Config loader w/ env substitution (Configuration Management)
    - Implemented YAML loader with `${VAR}` expansion + safety checks, plus unit tests for env substitution, path enforcement, and `~` expansion.
  - ✅ Completed: LOGFORGE_HOME resolver (Configuration Management)
    - Added service/interactive home detection module with env/user heuristics, wired into loader, and covered with dedicated unit tests.
  - ✅ Completed: Config schema validation (Configuration Management)
    - Added Pydantic config models, loader integration, and regression tests for invalid ports, outputs, generators, and frequency definitions.
  - ✅ Completed: Default config generator (Configuration Management)
    - Delivered schema-backed default config builder/writer with directory scaffolding helpers and overwrite safety checks.
- ✅ Completed: Interactive init wizard (Configuration Management)
  - Implemented `logforge init` command with an interactive wizard plus CLI tests and configurable defaults feeding the config/entity generators.
- ✅ Completed: Config CLI commands (Configuration Management)
  - Added Typer subcommands for `config show/set/validate`, leveraging schema validation and file-based mutations pending API endpoints, with comprehensive CLI tests.
- ✅ Completed: Logging utilities (Logging Infrastructure)
  - Delivered centralized logging configuration + context manager with size/time rotation support and tests ensuring logs write to `${LOGFORGE_HOME}` (`tests/unit/test_logging_setup.py`).

