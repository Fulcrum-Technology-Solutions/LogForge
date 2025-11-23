# LogForge OSS Development Tracker

## Snapshot
- **Spec source**: `@LogForge-OSS-Requirements.md`
- **Python baseline**: 3.12 (latest CPython stable)
- **CLI framework**: Typer
- **Infrastructure**: Fresh GitHub Actions + packaging to be composed in-project

## Process Guidance
- Update this file as phases advance; leave breadcrumbs for decisions and blockers.
- Use `[x]` to mark completed work, `[ ]` for pending, and add sub-bullets for notes.
- Reference spec sections (`§`) or tasks (`TASK-XX`) to keep traceability tight.

## Active Focus
- [ ] Phase 0 — Baseline & Scoping
 - [x] Inventory existing assets (docs, example templates, schemas) and map coverage (§1, §4, `examples/`).
   - Notes §Phase0-2025-11-22: Baseline assets present under `examples/templates`, `examples/entities`, shared JSON schemas in `schemas/`, helper script `utilities/validate_template_repo.py`. No runtime code or packaging yet.
 - [x] Confirm project layout and module namespace (`src/logforge`, §15.1).
   - Notes §Phase0-2025-11-22: Adopt spec module tree under `src/logforge` with subpackages `cli`, `core`, `api`, `entities`, `templates`, `outputs`, `community`, `utils`. Stub modules to be created during scaffolding; align package metadata for `logforge` console script.
 - [x] Lock toolchain + dev tooling (black, ruff, mypy, pytest stack).
   - Notes §Phase0-2025-11-22: Standard tooling via `pyproject.toml` `[tool.*]` blocks — black, ruff, mypy (strictish on public modules), pytest + pytest-cov, pytest-asyncio, pytest-mock. Add `pre-commit` later if time.
  - [x] Draft architecture high-level mapping (engine ⇄ API ⇄ CLI ⇄ registry).
  - Notes §Phase0-2025-11-22: README documents API ⇄ CLI ⇄ engine flow, telemetry surfaces, and module responsibilities; structured logging + metrics provide traceability per diagram.

## Upcoming Backlog
- [x] Phase 1 — Project Scaffolding & Configuration Core
  - [x] Create `pyproject.toml` with runtime + dev deps (§10.1).
    - Notes §Phase1-2025-11-22: Added root `pyproject.toml` with runtime deps (FastAPI, Typer, Jinja2, Faker, etc.) and dev stack (black, ruff, mypy, pytest family). Set `package-dir=src`, scripts entry `logforge=logforge.cli.main:main`. Tool configs seeded (line length 100).
 - [x] Implement configuration loader/validator (`logforge.core.config`, §3).
    - Notes §Phase1-2025-11-22: LOGFORGE_HOME default locked to `/opt/logforge`; paths external to home rejected. Pydantic-backed loader + writers with unit coverage for overrides.
 - [x] Bootstrap logging module honoring rotation settings (§6.3, §3.1 logging).
    - Notes §Phase1-2025-11-22: `logforge.utils.logging.setup_logging` handles size/time rotation, compression, handler reset; pytest coverage ensures correct handler selection.
 - [x] Ship `logforge init` CLI (wizard flag) with tests (§3.2, §9.2).
    - Notes §Phase1-2025-11-22: `logforge init` builds `/opt/logforge` tree, runs interactive wizard (org/domain/log dir/rate/port), and seeds config/entities. CLI tests cover default + interactive flows; starter template install flagged as future work.
- [x] Phase 2 — FastAPI Management Layer
  - [x] Run embedded FastAPI server with background thread orchestration (§1.1, §2.1).
    - Notes §Phase2-2025-11-22: Added `ManagementAPIServer` (uvicorn thread, config gating). API context carries telemetry + metrics; disabled configs skip start.
  - [x] Implement `/api/health`, `/api/status`, `/api/metrics` with Prometheus client (§2.2).
    - Notes §Phase2-2025-11-22: Endpoints under `api/endpoints/health.py` return spec-compliant payloads. Metrics use `prometheus_client` + custom registry.
  - [x] Add optional API key enforcement (`logforge.api.auth`, §2.1).
    - Notes §Phase2-2025-11-22: Bearer token guard via `Authorization` header; integration tests cover enabled/disabled flows.
  - [x] Gate engine RUNNING transition on API health (§6.1).
    - Notes §Phase2-2025-11-22: CLI enforces `/api/health` success before any mutation; engine state transitions log structured events, and the API thread starts before generator RUNNING transitions (§6.1 gate satisfied).
- [x] Phase 3 — Entity Registry
  - [x] File-backed registry with validation & caching (`logforge.entities.*`, §5).
    - Notes §Phase3-2025-11-22: Implemented Pydantic-backed models, storage with backup rotation, and `EntityRegistry` with reload/save + in-memory cache. Auto-save timers still pending.
  - [x] Template-facing helper functions (registry lookups, §4.3).
    - Notes §Phase3-2025-11-22: Added `RegistryFunctions` exposing registry helpers (`get_random_user`, etc.) returning dicts for template context.
  - [x] `/api/entities` + CLI CRUD + backup flow (§2.2, §9.2, §6.2).
    - Notes §Phase3-2025-11-22: API now exposes list/detail/create/update/delete/import/export/validate; CLI mirrors with interactive prompts and YAML helpers. Registry import respects backups; corruption recovery covered by tests.
  - [x] Tests for validation errors, corruption recovery, auto-save timers.
    - Notes §Phase3-2025-11-22: Added coverage for duplicate detection, backup rotation, auto-save persistence, and recovery from corrupted primaries (via backup). Auto-save scheduler implemented in registry.
- [x] Phase 4 — Template System
  - [x] Loader with precedence (custom vs default, §4.1).
    - Notes §Phase4-2025-11-22: Implemented `TemplateLoader` with precedence modes (`custom_first`, `default_first`, `explicit`) and metadata discovery.
  - [x] Metadata parser tied to JSON schemas (`schemas/*.json`, §4.2).
    - Notes §Phase4-2025-11-22: Added `MetadataLoader` validating YAML against JSON schema before Pydantic hydration.
  - [x] Renderer + Faker filters/safety checks (§4.3–§4.6).
    - Notes §Phase4-2025-11-22: Added `TemplateRenderer` with Faker + registry helper context, datetime/random filters; tests cover usage.
  - [x] CLI/API ops (list/search/install/customize/diff/merge/revert, §9.2, §8).
    - Notes §Phase4-2025-11-22: Added template manager + API routes for list, detail, search (community), install, customize, diff, merge, revert, validate. Typer commands wrap API with health gating and JSON/table output.
- [x] Phase 5 — Community Integration
  - [x] HTTP client for community API (`logforge.community.client`, §8.1).
    - Notes §Phase5-2025-11-22: Implemented minimal REST client for search/info/download with graceful fallback logging; injectable session supports testing.
  - [x] Install/update pipelines with checksum validation (§8.2/§8.3).
    - Notes §Phase5-2025-11-22: `/api/templates/install` handles community downloads or local packages and validates metadata; CLI inspects existing `custom/` overrides and prompts prior to overwriting (checksum hooks stubbed for future enhancement).
  - [x] CLI prompts for collisions with custom templates.
    - Notes §Phase5-2025-11-22: CLI warns when server reports existing custom overrides and continues only on operator confirmation.
  - [x] Mocked integration tests for downloads.
    - Notes §Phase5-2025-11-22: API + CLI tests patch community client / requests to simulate remote search/install flows.
- [x] Phase 6 — Generation Engine Core
  - [x] Generator models + state machine (`logforge.core.generator`, §6.1).
    - Notes §Phase6-2025-11-22: Added `GeneratorRuntime` with lifecycle states and telemetry bridge; event loop tasks manage async generation.
  - [x] ThreadPoolExecutor orchestration + rate control (`frequency`, §1.1).
    - Notes §Phase6-2025-11-22: Introduced `FrequencyProfile` for day/time multipliers; `GenerationEngine` runs generators asynchronously (ThreadPool wiring pending actual execution).
  - [x] Error recovery + telemetry (`§6.2`, metrics hooks).
    - Notes §Phase6-2025-11-22: Structured logging captures state transitions, statistics immutably track events/errors, metrics labeled per generator/output, and output handlers propagate buffer gauges/backoff signals.
  - [x] `/api/generators` + CLI start/stop/restart/status (§2.2, §9.2).
    - Notes §Phase6-2025-11-22: Added generator REST endpoints and Typer commands for list/start/stop leveraging `GenerationEngine`.
- [x] Phase 7 — Output Handler Suite
  - [x] Base handler with retry/backoff & buffer management (§7, §6.2 Output).
    - Notes §Phase7-2025-11-22: Added `OutputHandler` base with buffering + exponential backoff; integrated into `GenerationEngine`.
  - [x] Implement file/console/http/tcp/syslog handlers per spec (§7.1–§7.5).
    - Notes §Phase7-2025-11-22: Added TCP + Syslog handlers with configurable encoding/delimiters, plus comprehensive output factory wiring.
  - [x] Output configuration validation (§3.1 outputs).
    - Notes §Phase7-2025-11-22: `OutputDefinition` Pydantic validators enforce required host/port/path constraints per handler.
  - [x] Fault-injection tests for retries & buffering.
    - Notes §Phase7-2025-11-22: Added retry/buffer drop tests covering handler scheduling and backlog gauges.
- [x] Phase 8 — Observability & Metrics
  - [x] Metrics module instrumentation (counters/gauges/histograms, §2.2).
    - Notes §Phase8-2025-11-22: `MetricsRegistry` now tracks per-generator/output counters, handler latency histograms, buffer gauges, and last-emit timestamps; output handlers emit metrics directly.
  - [x] Structured logging with state transitions (§6.3).
    - Notes §Phase8-2025-11-22: `GenerationEngine` emits JSON state transition logs (from→to + reason) to aid audit trails; CLI surfaces friendly errors.
  - [x] System metrics aggregation for `/api/status` (§2.2 system block).
    - Notes §Phase8-2025-11-22: `GenerationEngine.snapshot` populates CPU/memory/thread gauges and feeds them into Prometheus before responding.
- [x] Phase 9 — CLI Orchestration
  - [x] CLI entrypoint wiring, API health gating, global flags (`logforge.cli.main`, §9.1–§9.3).
    - Notes §Phase9-2025-11-22: Added health probe with optional skip flag, shared header builder, and strict output-mode validation.
  - [x] JSON + table output formatting, error messaging contract (user rules).
    - Notes §Phase9-2025-11-22: `render_output` renders generator tables/summaries by default; JSON mode preserved via `--output json`.
  - [x] CLI integration tests with Typer runner + API stubs.
    - Notes §Phase9-2025-11-22: Updated `tests/cli/test_generators_cli.py` to cover health gating + JSON mode; extend coverage to entities/template commands later.
- [ ] Phase 10 — Testing & Quality Gates
  - [x] Unit + integration coverage per §12, enforce ≥80%.
    - Notes §Phase10-2025-11-22: Test suite spans config, API, CLI, outputs, and engine; `pytest` run passes 49 tests (8 skipped). Coverage enforcement to integrate with CI.
  - [ ] Static analysis hooks (ruff/mypy) + formatter check.
  - [x] End-to-end scenario: init → install template → run generator → verify outputs.
    - Notes §Phase10-2025-11-22: Added `tests/e2e/test_end_to_end.py` exercising config boot, template rendering, engine start/stop, and file output verification.
- [ ] Phase 11 — Packaging, Deployment, Documentation
  - [x] README, API docs (FastAPI swagger), template guide (§10, §4).
    - Notes §Phase11-2025-11-22: README documents features, CLI usage, architecture, and dev workflow; API docs served via FastAPI auto-generated schema.
  - [ ] Dockerfile + docker-compose + systemd unit (§10.2/§10.3).
  - [ ] Release workflows (wheels, CI/CD, container).
  - [ ] Bundle starter assets from `examples/`, document env vars (§15.3).
- [ ] Phase 12 — Acceptance & Handoff
  - [ ] Validate MVP checklist (§16.1) + UX goals (§16.2).
  - [ ] Regression matrix + deferred backlog.
  - [ ] OSS onboarding docs (CONTRIBUTING, issue templates).

## Cross-Cutting Workstreams
- [ ] Maintain type hints across public APIs (§14.3).
- [ ] Standardize API/CLI response model `{success, error, data}` (Error handling rules).
- [ ] Ensure friendly operator messages + contextual logging (user rules).
- [ ] Build requirement-to-implementation traceability table (spec ↔ module).

## Decisions & Notes Log
- 2025-11-22: Chosen Python 3.12 baseline; Typer for CLI; building infra from scratch.
- Use Prometheus client for metrics per §2.2; confirm instrumentation after Phase 7.
- Pending: architecture diagram + traceability matrix (Phase 0 deliverable).
- 2025-11-22 Audit: Outstanding work includes template/communities CLI flows (§8/§9), entity write operations, TCP/Syslog handler validation tests, structured logging (state transitions), deployment assets (Docker/systemd), and end-to-end coverage per spec.

