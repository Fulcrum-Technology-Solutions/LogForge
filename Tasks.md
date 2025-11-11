# LogForge OSS - Development Tasks

**Project**: LogForge Open-Source Log Generator  
**Status**: Phase 1 - In Progress  
**Last Updated**: 2025-11-11

---

## Phase 1: Foundation + API Server Core (Week 1-2)

**Status**: 🔄 In Progress  
**Goal**: Get project scaffolding, config system, and API server skeleton operational.

### 1.1 Project Structure & Packaging
- [x] Create directory structure per requirements
- [x] Create pyproject.toml with dependencies
- [x] Add Apache 2.0 LICENSE file
- [x] Create basic README.md
- [x] Add .gitignore

### 1.2 Configuration Management
- [x] Create Pydantic models for config validation
- [x] Implement YAML loader with schema validation
- [x] Build default config generator
- [x] Add path expansion support (~/.logforge, env vars)
- [x] Implement config merge logic (CLI > env > file > defaults)

### 1.3 Logging Infrastructure
- [x] Setup Python logging with rotation
- [x] Implement log level configuration
- [x] Create structured log format
- [x] Add module-specific loggers

### 1.4 FastAPI Server Skeleton
- [x] Create FastAPI application
- [x] Implement background thread lifecycle
- [x] Add startup/shutdown handlers
- [x] Implement health check endpoint (GET /api/health)
- [x] Add basic status endpoint (GET /api/status)
- [x] Add CORS middleware
- [x] Implement optional API key auth

### 1.5 CLI Framework
- [x] Setup Click CLI framework
- [x] Implement `logforge init` command
- [x] Implement `logforge config show` command
- [x] Implement `logforge config validate` command
- [x] Add HTTP client wrapper for API calls
- [x] Add error handling & formatting
- [x] Add table output support
- [x] Add JSON output mode (--output json)
- [x] Add API serve command
- [x] Add health/status API commands

### 1.6 Testing & Acceptance
- [ ] Manual smoke test: `logforge init`
- [ ] Manual smoke test: `logforge config show`
- [ ] Verify API server starts and responds
- [ ] Setup basic pytest structure

**Acceptance Criteria**:
- [x] `logforge init` creates default config and directory structure
- [x] `logforge config show` displays current configuration
- [ ] API server starts and responds to health checks
- [ ] Application logging works correctly

---

## Phase 2: Entity Registry + API (Week 3)

**Status**: ⏳ Pending  
**Goal**: File-based entity storage with CRUD operations via CLI/API.  
**Testing**: Lightweight TDD - write tests as building each component.

### 2.1 Entity Storage Layer (Test-First)
- [ ] Write tests for YAML I/O operations
- [ ] Implement YAML file loader
- [ ] Implement YAML file saver with atomic writes
- [ ] Add backup rotation (keep N backups)
- [ ] Add file locking for concurrent access

### 2.2 Entity Validation (Test-First)
- [ ] Create Pydantic models for entities
- [ ] Write validation tests
- [ ] Implement custom validators (IP, MAC, email)
- [ ] Add duplicate detection logic

### 2.3 Entity Registry (Test-First)
- [ ] Write tests for CRUD operations
- [ ] Implement in-memory cache
- [ ] Add random selection methods
- [ ] Implement auto-save mechanism
- [ ] Add entity CRUD operations

### 2.4 Template Functions
- [ ] Create RegistryFunctions wrapper class
- [ ] Implement get_random_user/device/service
- [ ] Implement get_organization methods
- [ ] Write tests for all functions

### 2.5 Entity API Endpoints
- [ ] Implement GET /api/entities (summary)
- [ ] Implement GET /api/entities/{type} (list by type)
- [ ] Implement POST /api/entities/{type} (add)
- [ ] Implement PUT /api/entities/{type}/{id} (update)
- [ ] Implement DELETE /api/entities/{type}/{id} (delete)

### 2.6 Entity CLI Commands
- [ ] Implement `logforge entities list`
- [ ] Implement `logforge entities show`
- [ ] Implement `logforge entities add`
- [ ] Implement `logforge entities import`
- [ ] Implement `logforge entities export`
- [ ] Implement `logforge entities validate`

### 2.7 Integration Tests
- [ ] Test full workflow: add → validate → export → import
- [ ] Test API CRUD operations
- [ ] Test backup recovery scenario

**Acceptance Criteria**:
- [ ] Entities can be added/imported/exported via CLI
- [ ] Registry functions work correctly
- [ ] Entity validation catches errors
- [ ] API endpoints return proper entity data

---

## Phase 3: Template System + Community Integration (Week 4-5)

**Status**: ⏳ Pending  
**Goal**: Template discovery, rendering, validation, and community API client.  
**Testing**: Lightweight TDD for clear requirements.

### 3.1 Template Metadata Parser (Test-First)
- [ ] Create TemplateMetadata Pydantic model
- [ ] Write metadata parsing tests
- [ ] Implement metadata.yaml parser
- [ ] Add schema validation

### 3.2 Custom Jinja2 Filters (Test-First)
- [ ] Write tests for custom filters
- [ ] Implement now() function
- [ ] Implement format_datetime() filter
- [ ] Implement random_int() function
- [ ] Implement random_choice() function

### 3.3 Template Renderer (Test-First)
- [ ] Write rendering tests with registry
- [ ] Create TemplateRenderer class
- [ ] Setup Jinja2 environment
- [ ] Integrate Faker library
- [ ] Add custom filters to Jinja2
- [ ] Implement render() method

### 3.4 Template Validator (Test-First)
- [ ] Write validation tests
- [ ] Implement Jinja2 syntax validation
- [ ] Add metadata presence check
- [ ] Add unsafe operation detection
- [ ] Verify registry function references

### 3.5 Community API Client
- [ ] Create CommunityAPIClient class
- [ ] Implement list_vendors()
- [ ] Implement get_vendor()
- [ ] Implement search_templates()
- [ ] Implement download_template()
- [ ] Implement download_vendor_package()

### 3.6 Template Installation
- [ ] Create TemplateInstaller class
- [ ] Implement install_template()
- [ ] Implement install_vendor()
- [ ] Implement update_templates()
- [ ] Add ZIP extraction logic

### 3.7 Template API Endpoints
- [ ] Implement GET /api/templates (list)
- [ ] Implement GET /api/templates/{id} (details)
- [ ] Implement POST /api/templates/install
- [ ] Implement POST /api/templates/validate

### 3.8 Template CLI Commands
- [ ] Implement `logforge templates list`
- [ ] Implement `logforge templates search`
- [ ] Implement `logforge templates info`
- [ ] Implement `logforge templates install`
- [ ] Implement `logforge templates validate`
- [ ] Implement `logforge templates customize`
- [ ] Implement `logforge templates diff`
- [ ] Implement `logforge templates revert`

### 3.9 Copy Example Templates
- [ ] Copy Windows Event Log template from server
- [ ] Copy simple JSON log template
- [ ] Verify templates in correct structure

**Acceptance Criteria**:
- [ ] Templates render correctly with registry and faker
- [ ] Templates can be discovered locally and remotely
- [ ] Templates can be installed from community
- [ ] Template validation catches errors

---

## Phase 4: Event Generation Engine + API (Week 6-7)

**Status**: ⏳ Pending  
**Goal**: Core generator with state machine, threading, frequency control.  
**Testing**: Integration tests FIRST - define end-to-end behavior, then build.

### 4.1 Integration Test Scenarios (Write First)
- [ ] Write test: generator start/stop lifecycle
- [ ] Write test: multiple generators concurrent
- [ ] Write test: frequency variation by time
- [ ] Write test: template error → ERROR state
- [ ] Write test: output failure → DEGRADED state

### 4.2 Generator State Machine
- [ ] Create GeneratorState enum
- [ ] Create Generator class
- [ ] Implement start() method
- [ ] Implement stop() method
- [ ] Implement _run_loop() method
- [ ] Add state transitions
- [ ] Add statistics tracking

### 4.3 Frequency Control
- [ ] Write tests for frequency calculations
- [ ] Create FrequencyController class
- [ ] Implement time-of-day matching
- [ ] Implement day-of-week matching
- [ ] Calculate rate with multipliers

### 4.4 Generation Engine
- [ ] Create GenerationEngine class
- [ ] Setup ThreadPoolExecutor
- [ ] Implement initialize_generators()
- [ ] Implement start_generator()
- [ ] Implement stop_generator()
- [ ] Implement start_all()
- [ ] Implement stop_all()
- [ ] Add system health aggregation

### 4.5 Error Recovery Logic
- [ ] Implement template error handler
- [ ] Add smart retry for transient errors
- [ ] Implement output error handler
- [ ] Add DEGRADED state transitions

### 4.6 Generator API Endpoints
- [ ] Implement GET /api/generators (list)
- [ ] Implement GET /api/generators/{name} (details)
- [ ] Implement POST /api/generators/{name}/start
- [ ] Implement POST /api/generators/{name}/stop
- [ ] Implement POST /api/generators/{name}/restart

### 4.7 Generator CLI Commands
- [ ] Implement `logforge start`
- [ ] Implement `logforge stop`
- [ ] Implement `logforge restart`
- [ ] Implement `logforge status`
- [ ] Implement `logforge list`

### 4.8 Run Integration Tests
- [ ] Execute all integration tests
- [ ] Iterate until passing

**Acceptance Criteria**:
- [ ] Generators start/stop correctly via CLI and API
- [ ] Multiple generators run concurrently
- [ ] Frequency variation works
- [ ] State transitions work correctly
- [ ] Error recovery behaves as specified

---

## Phase 5: Output Handlers + Metrics (Week 8-9)

**Status**: ⏳ Pending  
**Goal**: All output handlers with retry logic, buffering, and Prometheus metrics.  
**Testing**: Mini-TDD - test before each handler.

### 5.1 Base Output Handler (Test Interface First)
- [ ] Write tests for base handler interface
- [ ] Create OutputHandler abstract base class
- [ ] Implement write() with retry logic
- [ ] Add buffer management
- [ ] Implement exponential backoff
- [ ] Add state management (HEALTHY/DEGRADED)

### 5.2 File Output Handler (Test First)
- [ ] Write file output tests
- [ ] Implement FileOutputHandler
- [ ] Add path variable substitution
- [ ] Implement rotation logic (size-based)
- [ ] Implement rotation logic (time-based)
- [ ] Add compression support

### 5.3 Console Output Handler (Test First)
- [ ] Write console output tests
- [ ] Implement ConsoleOutputHandler
- [ ] Add JSON format support
- [ ] Add text format support
- [ ] Support stdout/stderr selection

### 5.4 HTTP Output Handler (Test First)
- [ ] Write HTTP output tests
- [ ] Implement HTTPOutputHandler
- [ ] Add event batching
- [ ] Implement header env var substitution
- [ ] Add timeout handling

### 5.5 TCP Output Handler (Test First)
- [ ] Write TCP output tests
- [ ] Implement TCPOutputHandler
- [ ] Add connection management
- [ ] Implement keepalive
- [ ] Add delimiter support

### 5.6 Syslog Output Handler (Test First)
- [ ] Write syslog output tests
- [ ] Implement SyslogOutputHandler
- [ ] Add RFC5424 format support
- [ ] Add RFC3164 format support
- [ ] Implement facility/severity mapping

### 5.7 Output Handler Manager
- [ ] Create OutputManager class
- [ ] Implement handler factory
- [ ] Add multi-output write support
- [ ] Handle output failures gracefully

### 5.8 Prometheus Metrics
- [ ] Create MetricsCollector class
- [ ] Add events_generated_total counter
- [ ] Add errors_total counter
- [ ] Add generators_running gauge
- [ ] Add memory_usage_bytes gauge
- [ ] Add template_render_seconds histogram
- [ ] Add output_latency_seconds histogram
- [ ] Implement GET /api/metrics endpoint

### 5.9 Enhanced Status Endpoint
- [ ] Add system metrics (CPU, memory, threads)
- [ ] Update GET /api/status response

### 5.10 Integration Testing
- [ ] Test file output rotation
- [ ] Test HTTP output batching
- [ ] Test output failure recovery
- [ ] Test multiple outputs per generator

**Acceptance Criteria**:
- [ ] Events written to all output types correctly
- [ ] File rotation works (size and time-based)
- [ ] Retry logic recovers from transient failures
- [ ] Metrics endpoint returns valid Prometheus format
- [ ] Buffering prevents event loss during outages

---

## Phase 6: Deployment + Documentation (Week 10)

**Status**: ⏳ Pending  
**Goal**: Docker, documentation, example configs, smoke tests.  
**Testing**: Manual + smoke tests.

### 6.1 Dockerfile
- [ ] Create multi-stage Dockerfile
- [ ] Add non-root user
- [ ] Add health check
- [ ] Configure volumes
- [ ] Smoke test build and run

### 6.2 Docker Compose
- [ ] Create docker-compose.yml
- [ ] Add volume mounts
- [ ] Configure environment variables
- [ ] Add health checks

### 6.3 Example Configurations
- [ ] Create simple-config.yaml
- [ ] Create multi-generator.yaml
- [ ] Create http-output.yaml
- [ ] Create entities-example.yaml

### 6.4 Example Templates
- [ ] Add Windows Event Log example
- [ ] Add JSON log example
- [ ] Add Syslog format example

### 6.5 README.md
- [ ] Write Quick Start section
- [ ] Write Installation section
- [ ] Write Configuration section
- [ ] Write Usage section
- [ ] Write Templates section
- [ ] Write Development section
- [ ] Add License section

### 6.6 API Documentation
- [ ] Enable FastAPI auto-docs
- [ ] Verify OpenAPI schema
- [ ] Test /api/docs endpoint
- [ ] Test /api/redoc endpoint

### 6.7 Template Development Guide
- [ ] Create docs/template-guide.md
- [ ] Document template structure
- [ ] Document metadata format
- [ ] Document available functions
- [ ] Add example walkthrough

### 6.8 CLI Help Text
- [ ] Add help text to all commands
- [ ] Test all --help flags

### 6.9 Smoke Test Checklist
- [ ] Fresh install: pip install -e .
- [ ] Init: logforge init
- [ ] Add entities
- [ ] List templates
- [ ] Start generator
- [ ] Check status
- [ ] View logs
- [ ] API health check
- [ ] API docs access
- [ ] Stop generator
- [ ] Docker build and run

### 6.10 Version and Release Prep
- [ ] Set version in __init__.py
- [ ] Verify pyproject.toml complete
- [ ] Create CHANGELOG.md
- [ ] Tag repo: git tag v1.0.0

**Acceptance Criteria**:
- [ ] Docker image builds and runs correctly
- [ ] docker-compose provides working example
- [ ] Documentation is complete and accurate
- [ ] Package installs cleanly via pip
- [ ] Example templates work out of the box

---

## Progress Summary

| Phase | Status | Progress | Completion Date |
|-------|--------|----------|-----------------|
| Phase 1 | 🔄 In Progress | 80% | - |
| Phase 2 | ⏳ Pending | 0% | - |
| Phase 3 | ⏳ Pending | 0% | - |
| Phase 4 | ⏳ Pending | 0% | - |
| Phase 5 | ⏳ Pending | 0% | - |
| Phase 6 | ⏳ Pending | 0% | - |

**Overall Progress**: 0/6 phases complete (0%)

---

## Notes & Decisions

### 2025-11-11
- Created execution plan
- Starting Phase 1 development
- Community API exists and can be modified if needed
- Templates exist on server, will copy base ones for testing
- Testing approach: Phase 1 tests after stabilization, Phases 2-3 lightweight TDD, Phase 4 integration-first, Phase 5 mini-TDD, Phase 6 manual/smoke
- Python 3.9+ required
- Using Click for CLI framework
- Using FastAPI for API server
- Using Pydantic for validation
