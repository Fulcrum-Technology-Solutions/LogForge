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
  - [ ] Inventory existing assets (docs, example templates, schemas) and map coverage (§1, §4, `examples/`).
  - [ ] Confirm project layout and module namespace (`src/logforge`, §15.1).
  - [ ] Lock toolchain + dev tooling (black, ruff, mypy, pytest stack).
  - [ ] Draft architecture high-level mapping (engine ⇄ API ⇄ CLI ⇄ registry).

## Upcoming Backlog
- [ ] Phase 1 — Project Scaffolding & Configuration Core
  - [ ] Create `pyproject.toml` with runtime + dev deps (§10.1).
  - [ ] Implement configuration loader/validator (`logforge.core.config`, §3).
  - [ ] Bootstrap logging module honoring rotation settings (§6.3, §3.1 logging).
  - [ ] Ship `logforge init` CLI (wizard flag) with tests (§3.2, §9.2).
- [ ] Phase 2 — FastAPI Management Layer
  - [ ] Run embedded FastAPI server with background thread orchestration (§1.1, §2.1).
  - [ ] Implement `/api/health`, `/api/status`, `/api/metrics` with Prometheus client (§2.2).
  - [ ] Add optional API key enforcement (`logforge.api.auth`, §2.1).
  - [ ] Gate engine RUNNING transition on API health (§6.1).
- [ ] Phase 3 — Entity Registry
  - [ ] File-backed registry with validation & caching (`logforge.entities.*`, §5).
  - [ ] Template-facing helper functions (registry lookups, §4.3).
  - [ ] `/api/entities` + CLI CRUD + backup flow (§2.2, §9.2, §6.2).
  - [ ] Tests for validation errors, corruption recovery, auto-save timers.
- [ ] Phase 4 — Template System
  - [ ] Loader with precedence (custom vs default, §4.1).
  - [ ] Metadata parser tied to JSON schemas (`schemas/*.json`, §4.2).
  - [ ] Renderer + Faker filters/safety checks (§4.3–§4.6).
  - [ ] CLI/API ops (list/search/install/customize/diff/merge/revert, §9.2, §8).
- [ ] Phase 5 — Community Integration
  - [ ] HTTP client for community API (`logforge.community.client`, §8.1).
  - [ ] Install/update pipelines with checksum validation (§8.2/§8.3).
  - [ ] CLI prompts for collisions with custom templates.
  - [ ] Mocked integration tests for downloads.
- [ ] Phase 6 — Generation Engine Core
  - [ ] Generator models + state machine (`logforge.core.generator`, §6.1).
  - [ ] ThreadPoolExecutor orchestration + rate control (`frequency`, §1.1).
  - [ ] Error recovery + telemetry (`§6.2`, metrics hooks).
  - [ ] `/api/generators` + CLI start/stop/restart/status (§2.2, §9.2).
- [ ] Phase 7 — Output Handler Suite
  - [ ] Base handler with retry/backoff & buffer management (§7, §6.2 Output).
  - [ ] Implement file/console/http/tcp/syslog handlers per spec (§7.1–§7.5).
  - [ ] Output configuration validation (§3.1 outputs).
  - [ ] Fault-injection tests for retries & buffering.
- [ ] Phase 8 — Observability & Metrics
  - [ ] Metrics module instrumentation (counters/gauges/histograms, §2.2).
  - [ ] Structured logging with state transitions (§6.3).
  - [ ] System metrics aggregation for `/api/status` (§2.2 system block).
- [ ] Phase 9 — CLI Orchestration
  - [ ] CLI entrypoint wiring, API health gating, global flags (`logforge.cli.main`, §9.1–§9.3).
  - [ ] JSON + table output formatting, error messaging contract (user rules).
  - [ ] CLI integration tests with Typer runner + API stubs.
- [ ] Phase 10 — Testing & Quality Gates
  - [ ] Unit + integration coverage per §12, enforce ≥80%.
  - [ ] Static analysis hooks (ruff/mypy) + formatter check.
  - [ ] End-to-end scenario: init → install template → run generator → verify outputs.
- [ ] Phase 11 — Packaging, Deployment, Documentation
  - [ ] README, API docs (FastAPI swagger), template guide (§10, §4).
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

