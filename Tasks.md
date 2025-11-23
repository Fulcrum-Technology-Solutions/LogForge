# LogForge Development Tasks

**Version**: 1.0  
**Status**: Planning  
**Last Updated**: 2025-01-27

This document tracks development tasks, decisions, and progress for the LogForge open-source version. Tasks are organized by development phase and can be used by Agentic Coding Agents to implement the system systematically.

---

## Task Status Legend

- ⬜ **Not Started**: Task not yet begun
- 🔄 **In Progress**: Task actively being worked on
- ✅ **Complete**: Task finished and verified
- ⚠️ **Blocked**: Task waiting on dependency or decision
- 🔍 **Review**: Task complete, needs review/verification

---

## Phase 1: Foundation + API Server Core

**Goal**: Establish project structure, configuration management, and basic API server

### 1.1 Project Setup & Structure

- [ ] ⬜ **TASK-1.1.1**: Create Python package structure
  - **Description**: Set up `src/logforge/` directory structure per section 15.1
  - **Files**: `pyproject.toml`, `src/logforge/__init__.py`, `src/logforge/__main__.py`
  - **Acceptance**: Package installs via `pip install -e .`, imports work
  - **Decisions**: 
    - [ ] Choose Click vs Typer for CLI (recommend Typer for modern async support)
    - [ ] Python version minimum (requirements say >=3.9)

- [ ] ⬜ **TASK-1.1.2**: Configure `pyproject.toml` with dependencies
  - **Description**: Add all required dependencies from section 10.1
  - **Files**: `pyproject.toml`
  - **Acceptance**: All dependencies resolve, package builds
  - **Dependencies**: TASK-1.1.1

- [ ] ⬜ **TASK-1.1.3**: Create module structure skeleton
  - **Description**: Create all empty `__init__.py` files and directory structure
  - **Files**: All directories from section 15.1
  - **Acceptance**: All modules importable (even if empty)
  - **Dependencies**: TASK-1.1.1

### 1.2 Configuration Management

- [ ] ⬜ **TASK-1.2.1**: Implement configuration loader
  - **Description**: YAML config parser with environment variable substitution
  - **Files**: `src/logforge/core/config.py`
  - **Acceptance**: 
    - Loads `config.yaml` from `${LOGFORGE_HOME}`
    - Supports `${VAR}` substitution
    - Validates required sections
  - **Decisions**:
    - [ ] Config validation library (Pydantic recommended)
    - [ ] Default `LOGFORGE_HOME` resolution logic

- [ ] ⬜ **TASK-1.2.2**: Implement configuration schema validation
  - **Description**: Pydantic models for all config sections
  - **Files**: `src/logforge/core/config.py`
  - **Acceptance**: Invalid configs rejected with clear errors
  - **Dependencies**: TASK-1.2.1

- [ ] ⬜ **TASK-1.2.3**: Implement `logforge init` command
  - **Description**: Create default directory structure and config
  - **Files**: `src/logforge/cli/config.py`
  - **Acceptance**:
    - Creates `~/.logforge/` (or `/var/lib/logforge` for service)
    - Generates default `config.yaml`
    - Creates `templates/`, `entities.yaml` structure
  - **Dependencies**: TASK-1.2.1, TASK-1.1.3

- [ ] ⬜ **TASK-1.2.4**: Implement interactive wizard for `logforge init --interactive`
  - **Description**: Prompt user for org name, domain, output dir, etc.
  - **Files**: `src/logforge/cli/config.py`
  - **Acceptance**: Wizard completes and saves config
  - **Dependencies**: TASK-1.2.3

- [ ] ⬜ **TASK-1.2.5**: Implement `logforge config show` command
  - **Description**: Display current configuration
  - **Files**: `src/logforge/cli/config.py`
  - **Acceptance**: Shows formatted config, handles missing config gracefully
  - **Dependencies**: TASK-1.2.1

### 1.3 Logging Infrastructure

- [ ] ⬜ **TASK-1.3.1**: Implement logging setup module
  - **Description**: Configure Python logging with rotation
  - **Files**: `src/logforge/utils/logging.py`
  - **Acceptance**:
    - Logs to `${LOGFORGE_HOME}/logforge.log`
    - Supports rotation (size/time)
    - Configurable log levels
  - **Decisions**:
    - [ ] Logging library (standard library vs structlog)

- [ ] ⬜ **TASK-1.3.2**: Integrate logging throughout core modules
  - **Description**: Add logging statements at appropriate levels
  - **Files**: All core modules
  - **Acceptance**: All modules log appropriately (DEBUG/INFO/WARNING/ERROR)
  - **Dependencies**: TASK-1.3.1

### 1.4 FastAPI Server Foundation

- [ ] ⬜ **TASK-1.4.1**: Create FastAPI application skeleton
  - **Description**: Basic FastAPI app with middleware setup
  - **Files**: `src/logforge/api/server.py`
  - **Acceptance**: Server starts, responds to basic requests
  - **Decisions**:
    - [ ] Uvicorn vs Hypercorn (Uvicorn recommended)
    - [ ] Background thread vs async startup

- [ ] ⬜ **TASK-1.4.2**: Implement API server lifecycle management
  - **Description**: Start/stop API server in background thread
  - **Files**: `src/logforge/api/server.py`
  - **Acceptance**: 
    - Server starts in background thread
    - Graceful shutdown on stop
    - Health check endpoint works
  - **Dependencies**: TASK-1.4.1

- [ ] ⬜ **TASK-1.4.3**: Implement `GET /api/health` endpoint
  - **Description**: Health check with status, uptime, generator counts
  - **Files**: `src/logforge/api/endpoints/health.py`
  - **Acceptance**: Returns JSON per section 2.2 spec
  - **Dependencies**: TASK-1.4.1

- [ ] ⬜ **TASK-1.4.4**: Implement optional API key authentication
  - **Description**: Bearer token auth middleware
  - **Files**: `src/logforge/api/auth.py`
  - **Acceptance**: 
    - Works when `api.auth.enabled: true`
    - Generates key on first run if missing
    - Rejects requests without valid key
  - **Dependencies**: TASK-1.4.1
  - **Decisions**:
    - [ ] Key storage location (config file vs separate file)

- [ ] ⬜ **TASK-1.4.5**: Implement API startup command
  - **Description**: `logforge api start` command
  - **Files**: `src/logforge/cli/main.py`
  - **Acceptance**: Starts API server, blocks until interrupted
  - **Dependencies**: TASK-1.4.2

### 1.5 CLI Framework Setup

- [ ] ⬜ **TASK-1.5.1**: Set up CLI entry point
  - **Description**: Main CLI command structure with Click/Typer
  - **Files**: `src/logforge/cli/main.py`
  - **Acceptance**: `logforge --help` shows command structure
  - **Dependencies**: TASK-1.1.1

- [ ] ⬜ **TASK-1.5.2**: Implement API connection logic
  - **Description**: HTTP client for CLI to connect to API
  - **Files**: `src/logforge/cli/api_client.py`
  - **Acceptance**: 
    - Connects to local/remote API
    - Handles API key from env/config
    - Graceful error handling for unreachable API
  - **Dependencies**: TASK-1.5.1

- [ ] ⬜ **TASK-1.5.3**: Implement service health check before CLI commands
  - **Description**: Check API health before executing commands
  - **Files**: `src/logforge/cli/api_client.py`
  - **Acceptance**: 
    - Exits with `SERVICE_NOT_RUNNING` if API down
    - Shows helpful error message
  - **Dependencies**: TASK-1.5.2, TASK-1.4.3

---

## Phase 2: Entity Registry + API

**Goal**: File-based entity storage with API endpoints

### 2.1 Entity Storage Layer

- [ ] ⬜ **TASK-2.1.1**: Implement entity YAML file loader
  - **Description**: Load entities from `${LOGFORGE_HOME}/entities.yaml`
  - **Files**: `src/logforge/entities/storage.py`
  - **Acceptance**: 
    - Loads valid YAML
    - Handles missing file (creates default)
    - Validates schema
  - **Dependencies**: TASK-1.2.1

- [ ] ⬜ **TASK-2.1.2**: Implement entity schema validation
  - **Description**: Validate entity structure per section 5.2
  - **Files**: `src/logforge/entities/validator.py`
  - **Acceptance**:
    - Validates required fields
    - Checks email/IP/MAC formats
    - Detects duplicates
    - Clear error messages
  - **Dependencies**: TASK-2.1.1

- [ ] ⬜ **TASK-2.1.3**: Implement entity registry in-memory cache
  - **Description**: In-memory entity storage with auto-save
  - **Files**: `src/logforge/entities/registry.py`
  - **Acceptance**:
    - Fast lookups
    - Auto-save on interval
    - Thread-safe operations
  - **Dependencies**: TASK-2.1.1, TASK-2.1.2

- [ ] ⬜ **TASK-2.1.4**: Implement backup system for entities
  - **Description**: Auto-backup before saves, keep N backups
  - **Files**: `src/logforge/entities/storage.py`
  - **Acceptance**:
    - Creates backups before save
    - Rotates old backups
    - Recovers from backup on corruption
  - **Dependencies**: TASK-2.1.1

### 2.2 Entity Registry Functions

- [ ] ⬜ **TASK-2.2.1**: Implement template-accessible registry functions
  - **Description**: Functions for Jinja2 templates (get_random_user, etc.)
  - **Files**: `src/logforge/entities/functions.py`
  - **Acceptance**: All functions from section 4.3 work
  - **Dependencies**: TASK-2.1.3

- [ ] ⬜ **TASK-2.2.2**: Integrate registry functions into template context
  - **Description**: Make registry available to Jinja2 templates
  - **Files**: `src/logforge/templates/renderer.py`
  - **Acceptance**: Templates can call registry functions
  - **Dependencies**: TASK-2.2.1, TASK-3.1.1 (template renderer)

### 2.3 Entity API Endpoints

- [ ] ⬜ **TASK-2.3.1**: Implement `GET /api/entities` endpoint
  - **Description**: Return entity summary (counts, org info)
  - **Files**: `src/logforge/api/endpoints/entities.py`
  - **Acceptance**: Returns JSON per section 2.2 spec
  - **Dependencies**: TASK-2.1.3, TASK-1.4.1

- [ ] ⬜ **TASK-2.3.2**: Implement `GET /api/entities/{type}` endpoint
  - **Description**: Return entities of specific type (users/devices/services)
  - **Files**: `src/logforge/api/endpoints/entities.py`
  - **Acceptance**: Returns paginated entity list
  - **Dependencies**: TASK-2.3.1

- [ ] ⬜ **TASK-2.3.3**: Implement `POST /api/entities/{type}` endpoint
  - **Description**: Add new entity via API
  - **Files**: `src/logforge/api/endpoints/entities.py`
  - **Acceptance**: 
    - Validates entity
    - Adds to registry
    - Returns created entity
  - **Dependencies**: TASK-2.1.3, TASK-2.1.2

### 2.4 Entity CLI Commands

- [ ] ⬜ **TASK-2.4.1**: Implement `logforge entities list` command
  - **Description**: List all entities or filter by type
  - **Files**: `src/logforge/cli/entities.py`
  - **Acceptance**: Shows formatted entity list
  - **Dependencies**: TASK-2.3.1, TASK-1.5.2

- [ ] ⬜ **TASK-2.4.2**: Implement `logforge entities show` command
  - **Description**: Show specific entity details
  - **Files**: `src/logforge/cli/entities.py`
  - **Acceptance**: Shows formatted entity info
  - **Dependencies**: TASK-2.3.2

- [ ] ⬜ **TASK-2.4.3**: Implement `logforge entities add` command
  - **Description**: Interactive entity creation
  - **Files**: `src/logforge/cli/entities.py`
  - **Acceptance**: Prompts for fields, validates, creates entity
  - **Dependencies**: TASK-2.3.3

- [ ] ⬜ **TASK-2.4.4**: Implement `logforge entities import/export` commands
  - **Description**: Import/export entities from/to YAML
  - **Files**: `src/logforge/cli/entities.py`
  - **Acceptance**: 
    - Import validates and merges
    - Export creates valid YAML
  - **Dependencies**: TASK-2.1.1, TASK-2.1.2

- [ ] ⬜ **TASK-2.4.5**: Implement `logforge entities validate` command
  - **Description**: Validate entity file without loading
  - **Files**: `src/logforge/cli/entities.py`
  - **Acceptance**: Reports all validation errors
  - **Dependencies**: TASK-2.1.2

---

## Phase 3: Template System + Community Integration

**Goal**: Template rendering, discovery, and community API integration

### 3.1 Template Rendering Engine

- [ ] ⬜ **TASK-3.1.1**: Implement Jinja2 template loader
  - **Description**: Load templates from filesystem with precedence
  - **Files**: `src/logforge/templates/loader.py`
  - **Acceptance**:
    - Resolves templates per precedence rules (custom_first/default_first)
    - Handles missing templates
    - Caches loaded templates
  - **Dependencies**: TASK-1.2.1

- [ ] ⬜ **TASK-3.1.2**: Implement template renderer with context
  - **Description**: Render Jinja2 templates with registry and faker
  - **Files**: `src/logforge/templates/renderer.py`
  - **Acceptance**:
    - Renders templates correctly
    - Provides registry functions
    - Provides faker object
    - Provides custom filters (now, random_int, etc.)
  - **Dependencies**: TASK-3.1.1, TASK-2.2.1

- [ ] ⬜ **TASK-3.1.3**: Implement custom Jinja2 filters
  - **Description**: now(), format_datetime(), random_int(), random_choice()
  - **Files**: `src/logforge/templates/filters.py`
  - **Acceptance**: All filters work in templates
  - **Dependencies**: TASK-3.1.2

- [ ] ⬜ **TASK-3.1.4**: Integrate Faker library
  - **Description**: Make faker available to templates
  - **Files**: `src/logforge/templates/renderer.py`
  - **Acceptance**: All faker methods accessible in templates
  - **Dependencies**: TASK-3.1.2

### 3.2 Template Metadata & Validation

- [ ] ⬜ **TASK-3.2.1**: Implement metadata.yaml parser
  - **Description**: Parse and validate template metadata
  - **Files**: `src/logforge/templates/loader.py`
  - **Acceptance**:
    - Loads metadata.yaml
    - Validates required fields
    - Handles missing metadata
  - **Dependencies**: TASK-3.1.1

- [ ] ⬜ **TASK-3.2.2**: Implement template validator
  - **Description**: Validate templates per section 4.5
  - **Files**: `src/logforge/templates/validator.py`
  - **Acceptance**:
    - Validates Jinja2 syntax
    - Checks metadata presence
    - Validates registry function calls
    - Detects unsafe operations
  - **Dependencies**: TASK-3.1.1, TASK-3.2.1

- [ ] ⬜ **TASK-3.2.3**: Implement `logforge templates validate` command
  - **Description**: Validate template file or directory
  - **Files**: `src/logforge/cli/templates.py`
  - **Acceptance**: Reports all validation errors clearly
  - **Dependencies**: TASK-3.2.2

### 3.3 Template Discovery

- [ ] ⬜ **TASK-3.3.1**: Implement local template scanner
  - **Description**: Scan filesystem for templates
  - **Files**: `src/logforge/templates/loader.py`
  - **Acceptance**:
    - Discovers all templates in default/ and custom/
    - Builds template registry
    - Handles precedence correctly
  - **Dependencies**: TASK-3.1.1, TASK-3.2.1

- [ ] ⬜ **TASK-3.3.2**: Implement template cache with TTL
  - **Description**: Cache template metadata and content
  - **Files**: `src/logforge/templates/loader.py`
  - **Acceptance**:
    - Caches templates
    - Respects TTL
    - Invalidates on file changes
  - **Dependencies**: TASK-3.3.1

### 3.4 Community API Client

- [ ] ⬜ **TASK-3.4.1**: Implement HTTP client for community API
  - **Description**: Client for `https://api.logforge.io/v1`
  - **Files**: `src/logforge/community/client.py`
  - **Acceptance**:
    - Handles all endpoints from section 8.1
    - Error handling
    - Retry logic
  - **Decisions**:
    - [ ] HTTP library (requests vs httpx)

- [ ] ⬜ **TASK-3.4.2**: Implement template search functionality
  - **Description**: Search remote templates
  - **Files**: `src/logforge/community/client.py`
  - **Acceptance**: Returns search results
  - **Dependencies**: TASK-3.4.1

- [ ] ⬜ **TASK-3.4.3**: Implement template download and installation
  - **Description**: Download ZIP, extract to default/
  - **Files**: `src/logforge/community/client.py`
  - **Acceptance**:
    - Downloads template packages
    - Extracts to correct location
    - Validates package structure
    - Handles conflicts with custom templates
  - **Dependencies**: TASK-3.4.1, TASK-3.3.1

- [ ] ⬜ **TASK-3.4.4**: Implement template version checking
  - **Description**: Compare local vs remote versions
  - **Files**: `src/logforge/community/client.py`
  - **Acceptance**: Identifies outdated templates
  - **Dependencies**: TASK-3.4.1, TASK-3.3.1

### 3.5 Template API Endpoints

- [ ] ⬜ **TASK-3.5.1**: Implement `GET /api/templates` endpoint
  - **Description**: List all templates with metadata
  - **Files**: `src/logforge/api/endpoints/templates.py`
  - **Acceptance**: Returns template list per section 2.2 spec
  - **Dependencies**: TASK-3.3.1, TASK-1.4.1

- [ ] ⬜ **TASK-3.5.2**: Implement `GET /api/templates/{template_id}` endpoint
  - **Description**: Get detailed template information
  - **Files**: `src/logforge/api/endpoints/templates.py`
  - **Acceptance**: Returns full template details
  - **Dependencies**: TASK-3.5.1

### 3.6 Template CLI Commands

- [ ] ⬜ **TASK-3.6.1**: Implement `logforge templates list` command
  - **Description**: List templates with location and version
  - **Files**: `src/logforge/cli/templates.py`
  - **Acceptance**: Shows precedence indicators, versions
  - **Dependencies**: TASK-3.5.1, TASK-1.5.2

- [ ] ⬜ **TASK-3.6.2**: Implement `logforge templates search` command
  - **Description**: Search community templates
  - **Files**: `src/logforge/cli/templates.py`
  - **Acceptance**: Shows search results
  - **Dependencies**: TASK-3.4.2

- [ ] ⬜ **TASK-3.6.3**: Implement `logforge templates info` command
  - **Description**: Show template details
  - **Files**: `src/logforge/cli/templates.py`
  - **Acceptance**: Shows both default and custom if both exist
  - **Dependencies**: TASK-3.5.2

- [ ] ⬜ **TASK-3.6.4**: Implement `logforge templates install` command
  - **Description**: Install template from community
  - **Files**: `src/logforge/cli/templates.py`
  - **Acceptance**: 
    - Installs to default/
    - Warns if custom exists
    - Handles vendor-level installs
  - **Dependencies**: TASK-3.4.3

- [ ] ⬜ **TASK-3.6.5**: Implement `logforge templates update` command
  - **Description**: Update outdated templates
  - **Files**: `src/logforge/cli/templates.py`
  - **Acceptance**: 
    - Updates default/ templates only
    - Warns about custom versions
  - **Dependencies**: TASK-3.4.4, TASK-3.4.3

### 3.7 Template Customization Workflow

- [ ] ⬜ **TASK-3.7.1**: Implement `logforge templates customize` command
  - **Description**: Copy default template to custom/
  - **Files**: `src/logforge/cli/templates.py`
  - **Acceptance**: 
    - Copies template
    - Sets up precedence
    - Optionally opens editor
  - **Dependencies**: TASK-3.3.1

- [ ] ⬜ **TASK-3.7.2**: Implement `logforge templates diff` command
  - **Description**: Show differences between custom and default
  - **Files**: `src/logforge/cli/templates.py`
  - **Acceptance**: Shows diff using configured tool
  - **Dependencies**: TASK-3.7.1
  - **Decisions**:
    - [ ] Diff tool integration (built-in vs external)

- [ ] ⬜ **TASK-3.7.3**: Implement `logforge templates merge` command
  - **Description**: Merge default changes into custom
  - **Files**: `src/logforge/cli/templates.py`
  - **Acceptance**: 
    - Attempts merge
    - Handles conflicts interactively
  - **Dependencies**: TASK-3.7.2

- [ ] ⬜ **TASK-3.7.4**: Implement `logforge templates revert` command
  - **Description**: Remove custom version, use default
  - **Files**: `src/logforge/cli/templates.py`
  - **Acceptance**: 
    - Removes custom template
    - Confirms action
  - **Dependencies**: TASK-3.7.1

- [ ] ⬜ **TASK-3.7.5**: Implement `logforge templates create` command
  - **Description**: Interactive template creation wizard
  - **Files**: `src/logforge/cli/templates.py`
  - **Acceptance**: 
    - Creates template structure
    - Generates metadata
    - Creates in custom/
  - **Dependencies**: TASK-3.2.1

---

## Phase 4: Event Generation Engine + API

**Goal**: Generator lifecycle, threading, frequency control, error recovery

### 4.1 Generator State Machine

- [ ] ⬜ **TASK-4.1.1**: Implement GeneratorState enum
  - **Description**: STOPPED, STARTING, RUNNING, DEGRADED, ERROR, STOPPING
  - **Files**: `src/logforge/core/generator.py`
  - **Acceptance**: All states defined
  - **Dependencies**: TASK-1.1.3

- [ ] ⬜ **TASK-4.1.2**: Implement Generator class with state management
  - **Description**: Generator class with state transitions
  - **Files**: `src/logforge/core/generator.py`
  - **Acceptance**:
    - State transitions work correctly
    - Thread-safe state changes
    - State history tracking
  - **Dependencies**: TASK-4.1.1

- [ ] ⬜ **TASK-4.1.3**: Implement state transition validation
  - **Description**: Ensure valid state transitions per section 6.1
  - **Files**: `src/logforge/core/generator.py`
  - **Acceptance**: Invalid transitions rejected
  - **Dependencies**: TASK-4.1.2

### 4.2 Frequency Control

- [ ] ⬜ **TASK-4.2.1**: Implement frequency calculation logic
  - **Description**: Calculate rate based on time/day variations
  - **Files**: `src/logforge/core/frequency.py`
  - **Acceptance**:
    - Base rate works
    - Time-based multipliers apply
    - Day-of-week multipliers apply
  - **Dependencies**: TASK-1.2.1

- [ ] ⬜ **TASK-4.2.2**: Integrate frequency into generator loop
  - **Description**: Use frequency to control event generation rate
  - **Files**: `src/logforge/core/generator.py`
  - **Acceptance**: Events generated at correct rate
  - **Dependencies**: TASK-4.2.1, TASK-4.1.2

### 4.3 Event Generation Loop

- [ ] ⬜ **TASK-4.3.1**: Implement main generation loop
  - **Description**: Loop that renders templates and sends to outputs
  - **Files**: `src/logforge/core/generator.py`
  - **Acceptance**:
    - Renders templates at correct rate
    - Sends events to outputs
    - Handles stop signal
  - **Dependencies**: TASK-4.1.2, TASK-3.1.2, TASK-5.1.1 (output handlers)

- [ ] ⬜ **TASK-4.3.2**: Implement event statistics tracking
  - **Description**: Track events generated, errors, uptime
  - **Files**: `src/logforge/core/generator.py`
  - **Acceptance**: Statistics accurate and accessible
  - **Dependencies**: TASK-4.3.1

### 4.4 Thread Pool Management

- [ ] ⬜ **TASK-4.4.1**: Implement ThreadPoolExecutor setup
  - **Description**: Dynamic thread pool for generators
  - **Files**: `src/logforge/core/engine.py`
  - **Acceptance**:
    - Auto-sizes based on CPU cores
    - Configurable max threads
    - Handles thread lifecycle
  - **Dependencies**: TASK-4.1.2

- [ ] ⬜ **TASK-4.4.2**: Implement generator thread management
  - **Description**: Start/stop generators in thread pool
  - **Files**: `src/logforge/core/engine.py`
  - **Acceptance**:
    - Multiple generators run concurrently
    - Threads cleaned up on stop
  - **Dependencies**: TASK-4.4.1, TASK-4.3.1

### 4.5 Error Handling & Recovery

- [ ] ⬜ **TASK-4.5.1**: Implement template rendering error handling
  - **Description**: Catch template errors, transition to ERROR state
  - **Files**: `src/logforge/core/generator.py`
  - **Acceptance**:
    - Catches rendering errors
    - Logs detailed error info
    - Transitions to ERROR state
    - Continues other generators
  - **Dependencies**: TASK-4.3.1, TASK-4.1.2

- [ ] ⬜ **TASK-4.5.2**: Implement smart retry logic for transient errors
  - **Description**: Retry entity not found, don't retry syntax errors
  - **Files**: `src/logforge/core/generator.py`
  - **Acceptance**:
    - Retries transient errors
    - Stays in ERROR for config errors
  - **Dependencies**: TASK-4.5.1

- [ ] ⬜ **TASK-4.5.3**: Implement entity registry corruption handling
  - **Description**: Handle corrupted entities.yaml
  - **Files**: `src/logforge/core/engine.py`
  - **Acceptance**:
    - Detects corruption
    - Attempts backup recovery
    - Stops affected generators
  - **Dependencies**: TASK-2.1.4, TASK-4.1.2

### 4.6 Generator API Endpoints

- [ ] ⬜ **TASK-4.6.1**: Implement `GET /api/generators` endpoint
  - **Description**: List all generators
  - **Files**: `src/logforge/api/endpoints/generators.py`
  - **Acceptance**: Returns generator list per spec
  - **Dependencies**: TASK-4.1.2, TASK-1.4.1

- [ ] ⬜ **TASK-4.6.2**: Implement `GET /api/generators/{name}` endpoint
  - **Description**: Get generator details
  - **Files**: `src/logforge/api/endpoints/generators.py`
  - **Acceptance**: Returns full generator info
  - **Dependencies**: TASK-4.6.1

- [ ] ⬜ **TASK-4.6.3**: Implement `POST /api/generators/{name}/start` endpoint
  - **Description**: Start a generator
  - **Files**: `src/logforge/api/endpoints/generators.py`
  - **Acceptance**: Starts generator, returns state
  - **Dependencies**: TASK-4.4.2

- [ ] ⬜ **TASK-4.6.4**: Implement `POST /api/generators/{name}/stop` endpoint
  - **Description**: Stop a generator
  - **Files**: `src/logforge/api/endpoints/generators.py`
  - **Acceptance**: Stops generator gracefully
  - **Dependencies**: TASK-4.6.3

- [ ] ⬜ **TASK-4.6.5**: Implement `POST /api/generators/{name}/restart` endpoint
  - **Description**: Restart a generator
  - **Files**: `src/logforge/api/endpoints/generators.py`
  - **Acceptance**: Stops then starts generator
  - **Dependencies**: TASK-4.6.3, TASK-4.6.4

- [ ] ⬜ **TASK-4.6.6**: Implement `GET /api/status` endpoint
  - **Description**: Detailed system status
  - **Files**: `src/logforge/api/endpoints/health.py`
  - **Acceptance**: Returns status per section 2.2 spec
  - **Dependencies**: TASK-4.6.1, TASK-4.3.2

### 4.7 Generator CLI Commands

- [ ] ⬜ **TASK-4.7.1**: Implement `logforge generators list` command
  - **Description**: List all generators
  - **Files**: `src/logforge/cli/generators.py`
  - **Acceptance**: Shows formatted generator list
  - **Dependencies**: TASK-4.6.1, TASK-1.5.2

- [ ] ⬜ **TASK-4.7.2**: Implement `logforge generators start` command
  - **Description**: Start generator(s)
  - **Files**: `src/logforge/cli/generators.py`
  - **Acceptance**: Starts generator, shows status
  - **Dependencies**: TASK-4.6.3

- [ ] ⬜ **TASK-4.7.3**: Implement `logforge generators stop` command
  - **Description**: Stop generator(s)
  - **Files**: `src/logforge/cli/generators.py`
  - **Acceptance**: Stops generator gracefully
  - **Dependencies**: TASK-4.6.4

- [ ] ⬜ **TASK-4.7.4**: Implement `logforge status` command
  - **Description**: Show system status
  - **Files**: `src/logforge/cli/main.py`
  - **Acceptance**: 
    - Shows table format by default
    - JSON format with --output json
  - **Dependencies**: TASK-4.6.6, TASK-1.5.2

---

## Phase 5: Output Handlers + Metrics

**Goal**: All output types, retry logic, buffering, metrics

### 5.1 Output Handler Base

- [ ] ⬜ **TASK-5.1.1**: Implement base OutputHandler abstract class
  - **Description**: Abstract base for all output handlers
  - **Files**: `src/logforge/outputs/base.py`
  - **Acceptance**:
    - Defines write() and write_batch() methods
    - Defines close() method
    - Error handling interface
  - **Dependencies**: TASK-1.1.3

- [ ] ⬜ **TASK-5.1.2**: Implement output handler factory
  - **Description**: Create output handlers from config
  - **Files**: `src/logforge/outputs/__init__.py`
  - **Acceptance**: Creates correct handler type from config
  - **Dependencies**: TASK-5.1.1, TASK-1.2.1

### 5.2 File Output Handler

- [ ] ⬜ **TASK-5.2.1**: Implement file output handler
  - **Description**: Write events to file
  - **Files**: `src/logforge/outputs/file.py`
  - **Acceptance**:
    - Writes events to file
    - Handles path variables ({generator}, {date})
    - Atomic writes
  - **Dependencies**: TASK-5.1.1

- [ ] ⬜ **TASK-5.2.2**: Implement file rotation (size-based)
  - **Description**: Rotate file when size threshold reached
  - **Files**: `src/logforge/outputs/file.py`
  - **Acceptance**:
    - Rotates at max_size
    - Compresses rotated files
    - Keeps N rotated files
  - **Dependencies**: TASK-5.2.1

- [ ] ⬜ **TASK-5.2.3**: Implement file rotation (time-based)
  - **Description**: Rotate file on time interval
  - **Files**: `src/logforge/outputs/file.py`
  - **Acceptance**:
    - Rotates on schedule
    - Date-based naming
  - **Dependencies**: TASK-5.2.1

### 5.3 Console Output Handler

- [ ] ⬜ **TASK-5.3.1**: Implement console output handler
  - **Description**: Write to stdout/stderr
  - **Files**: `src/logforge/outputs/console.py`
  - **Acceptance**:
    - JSON format (JSONL)
    - Text format
    - Configurable stream
  - **Dependencies**: TASK-5.1.1

### 5.4 HTTP Output Handler

- [ ] ⬜ **TASK-5.4.1**: Implement HTTP output handler
  - **Description**: POST events to HTTP endpoint
  - **Files**: `src/logforge/outputs/http.py`
  - **Acceptance**:
    - Sends HTTP POST requests
    - Handles headers (env var substitution)
    - Configurable timeout
  - **Dependencies**: TASK-5.1.1

- [ ] ⬜ **TASK-5.4.2**: Implement HTTP batching
  - **Description**: Batch events for efficiency
  - **Files**: `src/logforge/outputs/http.py`
  - **Acceptance**:
    - Batches by size
    - Batches by time interval
    - Wraps in JSON array
  - **Dependencies**: TASK-5.4.1

### 5.5 TCP Output Handler

- [ ] ⬜ **TASK-5.5.1**: Implement TCP output handler
  - **Description**: Send events over TCP socket
  - **Files**: `src/logforge/outputs/tcp.py`
  - **Acceptance**:
    - Connects to TCP server
    - Sends events with delimiter
    - Handles reconnection
  - **Dependencies**: TASK-5.1.1

### 5.6 Syslog Output Handler

- [ ] ⬜ **TASK-5.6.1**: Implement syslog output handler
  - **Description**: Send events via syslog protocol
  - **Files**: `src/logforge/outputs/syslog.py`
  - **Acceptance**:
    - Supports RFC 5424 and RFC 3164
    - Configurable facility/severity
    - TCP and UDP protocols
  - **Dependencies**: TASK-5.1.1

### 5.7 Retry Logic & Buffering

- [ ] ⬜ **TASK-5.7.1**: Implement retry logic with exponential backoff
  - **Description**: Retry failed outputs with backoff
  - **Files**: `src/logforge/outputs/base.py`
  - **Acceptance**:
    - Exponential backoff per config
    - Max backoff cap
    - Configurable max attempts
  - **Dependencies**: TASK-5.1.1

- [ ] ⬜ **TASK-5.7.2**: Implement event buffering
  - **Description**: Buffer events during output failures
  - **Files**: `src/logforge/outputs/base.py`
  - **Acceptance**:
    - Buffers up to buffer_size
    - Drops oldest when full
    - Flushes on recovery
  - **Dependencies**: TASK-5.7.1

- [ ] ⬜ **TASK-5.7.3**: Implement DEGRADED state on output failure
  - **Description**: Transition generator to DEGRADED when output fails
  - **Files**: `src/logforge/core/generator.py`
  - **Acceptance**:
    - Transitions to DEGRADED
    - Recovers to RUNNING on success
  - **Dependencies**: TASK-5.7.1, TASK-4.1.2

### 5.8 Prometheus Metrics

- [ ] ⬜ **TASK-5.8.1**: Implement metrics collection
  - **Description**: Collect Prometheus-compatible metrics
  - **Files**: `src/logforge/utils/metrics.py`
  - **Acceptance**:
    - Counters: events_generated_total, errors_total
    - Gauges: generators_running, memory_usage_bytes
    - Histograms: template_render_seconds, output_latency_seconds
  - **Dependencies**: TASK-1.1.3

- [ ] ⬜ **TASK-5.8.2**: Integrate metrics into generators
  - **Description**: Update metrics from generator events
  - **Files**: `src/logforge/core/generator.py`
  - **Acceptance**: Metrics update correctly
  - **Dependencies**: TASK-5.8.1, TASK-4.3.1

- [ ] ⬜ **TASK-5.8.3**: Implement `GET /api/metrics` endpoint
  - **Description**: Return Prometheus metrics
  - **Files**: `src/logforge/api/endpoints/health.py`
  - **Acceptance**: Returns valid Prometheus format
  - **Dependencies**: TASK-5.8.1, TASK-1.4.1

---

## Phase 6: Deployment + Documentation

**Goal**: Docker, systemd, documentation, examples

### 6.1 Docker Deployment

- [ ] ⬜ **TASK-6.1.1**: Create Dockerfile
  - **Description**: Multi-stage build per section 10.2
  - **Files**: `Dockerfile`
  - **Acceptance**:
    - Builds successfully
    - Creates logforge user
    - Sets up LOGFORGE_HOME
    - Health check works
  - **Dependencies**: TASK-1.1.2

- [ ] ⬜ **TASK-6.1.2**: Create docker-compose.yml
  - **Description**: Docker Compose configuration
  - **Files**: `docker-compose.yml`
  - **Acceptance**:
    - Starts container
    - Volumes mounted correctly
    - Health check configured
  - **Dependencies**: TASK-6.1.1

- [ ] ⬜ **TASK-6.1.3**: Test Docker deployment
  - **Description**: Verify Docker setup works end-to-end
  - **Files**: N/A
  - **Acceptance**:
    - Container starts
    - API accessible
    - Can run init and start generators
  - **Dependencies**: TASK-6.1.2, All previous phases

### 6.2 Systemd Integration

- [ ] ⬜ **TASK-6.2.1**: Create systemd service unit
  - **Description**: Service file per section 10.3
  - **Files**: `logforge.service`
  - **Acceptance**: Service file valid
  - **Dependencies**: TASK-1.4.5

- [ ] ⬜ **TASK-6.2.2**: Test systemd service
  - **Description**: Verify service works
  - **Files**: N/A
  - **Acceptance**:
    - Service starts/stops
    - Logs to journal
    - Auto-restart works
  - **Dependencies**: TASK-6.2.1

### 6.3 Documentation

- [ ] ⬜ **TASK-6.3.1**: Update README.md
  - **Description**: Complete README with quick start
  - **Files**: `README.md`
  - **Acceptance**:
    - Installation instructions
    - Quick start guide
    - Basic usage examples
  - **Dependencies**: All functional tasks

- [ ] ⬜ **TASK-6.3.2**: Generate API documentation
  - **Description**: OpenAPI/Swagger docs from FastAPI
  - **Files**: Auto-generated from FastAPI
  - **Acceptance**: 
    - Available at `/docs`
    - All endpoints documented
  - **Dependencies**: All API tasks

- [ ] ⬜ **TASK-6.3.3**: Create template development guide
  - **Description**: Guide for creating custom templates
  - **Files**: `docs/template-development.md`
  - **Acceptance**:
    - Template structure explained
    - Registry functions documented
    - Faker usage examples
    - Custom filters explained
  - **Dependencies**: TASK-3.1.2, TASK-3.1.3

- [ ] ⬜ **TASK-6.3.4**: Create deployment guide
  - **Description**: Deployment instructions
  - **Files**: `docs/deployment.md`
  - **Acceptance**:
    - Docker instructions
    - Systemd instructions
    - Configuration examples
  - **Dependencies**: TASK-6.1.1, TASK-6.2.1

### 6.4 Example Templates

- [ ] ⬜ **TASK-6.4.1**: Create example Windows Security Event Log template
  - **Description**: Working example template
  - **Files**: `examples/templates/microsoft/windows/eventlog/security/`
  - **Acceptance**: Template works, generates valid output
  - **Dependencies**: TASK-3.1.2

- [ ] ⬜ **TASK-6.4.2**: Create example Palo Alto firewall template
  - **Description**: Second example template
  - **Files**: `examples/templates/paloalto/firewall/traffic/`
  - **Acceptance**: Template works, generates valid output
  - **Dependencies**: TASK-3.1.2

- [ ] ⬜ **TASK-6.4.3**: Bundle example templates with package
  - **Description**: Include examples in package
  - **Files**: `pyproject.toml`, package data
  - **Acceptance**: Examples available after install
  - **Dependencies**: TASK-6.4.1, TASK-6.4.2

### 6.5 Testing & Quality

- [ ] ⬜ **TASK-6.5.1**: Write unit tests for core modules
  - **Description**: Unit tests for critical paths
  - **Files**: `tests/`
  - **Acceptance**: 80%+ coverage
  - **Dependencies**: All core tasks

- [ ] ⬜ **TASK-6.5.2**: Write integration tests
  - **Description**: End-to-end workflow tests
  - **Files**: `tests/integration/`
  - **Acceptance**: All workflows tested
  - **Dependencies**: All functional tasks

- [ ] ⬜ **TASK-6.5.3**: Set up CI/CD pipeline
  - **Description**: GitHub Actions or similar
  - **Files**: `.github/workflows/`
  - **Acceptance**:
    - Runs tests on PR
    - Builds package
    - Lints code
  - **Dependencies**: TASK-6.5.1, TASK-6.5.2

### 6.6 Package Publishing

- [ ] ⬜ **TASK-6.6.1**: Prepare PyPI package
  - **Description**: Final package preparation
  - **Files**: `pyproject.toml`, `MANIFEST.in`
  - **Acceptance**: Package builds and validates
  - **Dependencies**: All tasks

- [ ] ⬜ **TASK-6.6.2**: Publish to PyPI (or test PyPI)
  - **Description**: Publish package
  - **Files**: N/A
  - **Acceptance**: Package installable via pip
  - **Dependencies**: TASK-6.6.1

---

## Decision Log

Track important architectural and implementation decisions here.

### D-1: CLI Framework Choice
- **Status**: ⚠️ Pending
- **Options**: Click vs Typer
- **Recommendation**: Typer (modern, async support, better type hints)
- **Decision**: _[To be decided]_

### D-2: HTTP Client Library
- **Status**: ⚠️ Pending
- **Options**: requests vs httpx
- **Recommendation**: httpx (async support, modern API)
- **Decision**: _[To be decided]_

### D-3: Logging Library
- **Status**: ⚠️ Pending
- **Options**: Standard library vs structlog
- **Recommendation**: Standard library (simpler, fewer dependencies)
- **Decision**: _[To be decided]_

### D-4: Config Validation Library
- **Status**: ⚠️ Pending
- **Options**: Pydantic vs custom validation
- **Recommendation**: Pydantic (already dependency, excellent validation)
- **Decision**: _[To be decided]_

### D-5: API Key Storage
- **Status**: ⚠️ Pending
- **Options**: Config file vs separate file
- **Recommendation**: Separate `.api_key` file (security best practice)
- **Decision**: _[To be decided]_

### D-6: Diff Tool Integration
- **Status**: ⚠️ Pending
- **Options**: Built-in diff vs external tools (vimdiff, meld)
- **Recommendation**: Built-in with fallback to external
- **Decision**: _[To be decided]_

---

## Progress Summary

**Overall Progress**: 0% (0/150+ tasks complete)

**By Phase**:
- Phase 1: 0% (0/20 tasks)
- Phase 2: 0% (0/15 tasks)
- Phase 3: 0% (0/25 tasks)
- Phase 4: 0% (0/25 tasks)
- Phase 5: 0% (0/20 tasks)
- Phase 6: 0% (0/20 tasks)

**Next Steps**:
1. Review and approve decision log items
2. Begin Phase 1: Project setup and structure
3. Set up development environment
4. Create initial project skeleton

---

## Notes for Agentic Coding Agents

### Task Execution Guidelines

1. **Dependencies**: Always check task dependencies before starting. Use the dependency chain to understand prerequisites.

2. **Acceptance Criteria**: Each task has specific acceptance criteria. Verify these are met before marking complete.

3. **Decision Points**: Tasks marked with "Decisions" require choices. Document decisions in the Decision Log section.

4. **File Structure**: Follow the module structure from section 15.1 of requirements. Create files in appropriate locations.

5. **Testing**: Write tests alongside implementation. Don't defer testing to Phase 6.

6. **Error Handling**: Implement comprehensive error handling from the start. Follow patterns from section 6.2.

7. **Logging**: Add logging statements as you implement. Use appropriate levels (DEBUG/INFO/WARNING/ERROR).

8. **Code Quality**: 
   - Use type hints for all public APIs
   - Add docstrings to all modules/classes/functions
   - Follow PEP 8 style guidelines
   - Use ruff/black for formatting

9. **Configuration**: All configuration should be loaded from `config.yaml` via the config module. Use environment variables for overrides.

10. **API First**: Remember this is API-first architecture. CLI commands are thin wrappers around API calls.

### Common Patterns

- **State Management**: Use state machine pattern for generators
- **Error Recovery**: Implement retry logic with exponential backoff
- **Thread Safety**: Use locks/queues for thread-safe operations
- **Template Context**: Provide registry, faker, and filters to all templates
- **Output Buffering**: Buffer events during failures, flush on recovery

---

**Last Updated**: 2025-01-27  
**Next Review**: After Phase 1 completion

