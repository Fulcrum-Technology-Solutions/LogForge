"""FastAPI server utilities."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable, Optional

import uvicorn
from fastapi import FastAPI
from prometheus_client import Counter, Gauge, generate_latest

from logforge.api.auth import build_auth_dependency
from logforge.api.endpoints.entities import create_entities_router
from logforge.api.endpoints.health import create_health_router
from logforge.api.endpoints.metrics import create_metrics_router
from logforge.api.endpoints.templates import create_templates_router
from logforge.api.models import (
    FrequencyInfo,
    GeneratorStatistics,
    GeneratorStatus,
    GeneratorSummary,
    HealthResponse,
    StatusResponse,
    SystemMetrics,
)
from logforge.templates.loader import TemplateLoader, TemplateRecord


@dataclass
class APIDependencies:
    get_health: Callable[[], HealthResponse]
    get_status: Callable[[], StatusResponse]
    get_metrics: Callable[[], bytes]
    on_startup: Callable[[], None] = lambda: None
    on_shutdown: Callable[[], None] = lambda: None
    entities_summary: Callable[[], dict[str, Any]] = lambda: {}
    list_entities: Callable[[str], list[dict[str, Any]]] = lambda _t: []
    create_entity: Callable[[str, dict[str, Any]], dict[str, Any]] = lambda _t, data: data
    list_templates: Callable[[], list[dict[str, Any]]] = lambda: []
    get_template: Callable[[str], Optional[dict[str, Any]]] = lambda _t: None


def default_dependencies() -> APIDependencies:
    from logforge.entities.registry import EntityRegistry

    registry = EntityRegistry()
    template_loader = TemplateLoader()
    generators = [
        GeneratorStatus(
            name="windows_security",
            state="RUNNING",
            template="microsoft/windows/eventlog/security",
            frequency=FrequencyInfo(base_rate=10, current_rate=10),
            outputs=["default_file"],
            statistics=GeneratorStatistics(events_generated=0, errors=0, uptime=0),
        )
    ]

    def health() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            uptime=0,
            generators=GeneratorSummary(total=1, running=1, degraded=0, error=0),
            entity_registry="healthy",
            template_cache="healthy",
        )

    def status() -> StatusResponse:
        return StatusResponse(
            uptime=0,
            version="0.0.0",
            generators=generators,
            system=SystemMetrics(cpu_percent=0.0, memory_mb=0.0, threads=1),
        )

    request_counter = Counter("api_requests_total", "Total API requests")
    health_gauge = Gauge("generator_count", "Total generators", ["state"])

    def metrics() -> bytes:
        request_counter.inc()
        health_summary = health()
        health_gauge.labels("running").set(health_summary.generators.running)
        health_gauge.labels("degraded").set(health_summary.generators.degraded)
        health_gauge.labels("error").set(health_summary.generators.error)
        return generate_latest()

    def template_summary(record: TemplateRecord) -> dict[str, Any]:
        metadata = record.metadata
        return {
            "id": record.template_id,
            "name": metadata.name,
            "vendor": metadata.vendor,
            "product": metadata.product,
            "data_source": metadata.data_source,
            "version": metadata.version,
            "location": record.location,
        }

    def template_detail(record: TemplateRecord) -> dict[str, Any]:
        return {
            "summary": template_summary(record),
            "metadata": record.metadata.model_dump(),
        }

    def list_templates() -> list[dict[str, Any]]:
        return [template_summary(record) for record in template_loader.list_templates()]

    def get_template(template_id: str) -> Optional[dict[str, Any]]:
        record = template_loader.get_template(template_id)
        if record is None:
            return None
        return template_detail(record)

    return APIDependencies(
        get_health=health,
        get_status=status,
        get_metrics=metrics,
        entities_summary=registry.summary,
        list_entities=lambda entity_type: registry.list_entities(entity_type),
        create_entity=lambda entity_type, payload: registry.add_entity(entity_type, payload),
        list_templates=list_templates,
        get_template=get_template,
    )


@dataclass
class APISettings:
    host: str = "127.0.0.1"
    port: int = 8080
    auth_enabled: bool = False
    api_key: Optional[str] = None


def create_app(
    *,
    settings: Optional[APISettings] = None,
    dependencies: Optional[APIDependencies] = None,
) -> FastAPI:
    """Create a FastAPI application with configured routers."""

    settings = settings or APISettings()
    deps = dependencies or default_dependencies()
    auth_dependency = build_auth_dependency(settings.auth_enabled, settings.api_key)

    app = FastAPI(
        title="LogForge Management API",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    health_router = create_health_router(deps, auth_dependency)
    metrics_router = create_metrics_router(deps, auth_dependency)
    entities_router = create_entities_router(deps, auth_dependency)
    templates_router = create_templates_router(deps, auth_dependency)

    app.include_router(health_router, prefix="/api")
    app.include_router(metrics_router, prefix="/api")
    app.include_router(entities_router, prefix="/api")
    app.include_router(templates_router, prefix="/api")

    @app.get("/api/healthz", include_in_schema=False)
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.on_event("startup")
    async def _startup() -> None:
        deps.on_startup()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        deps.on_shutdown()

    return app


class APIServer:
    """Background FastAPI server runner."""

    def __init__(self, app: FastAPI, settings: Optional[APISettings] = None):
        self.settings = settings or APISettings()
        self.app = app
        self.config = uvicorn.Config(
            app,
            host=self.settings.host,
            port=self.settings.port,
            log_level="info",
        )
        self.server = uvicorn.Server(self.config)
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _run() -> None:
            self.server.run()

        self._thread = threading.Thread(target=_run, name="uvicorn-server", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        if not self._thread:
            return
        self.server.should_exit = True
        self._thread.join(timeout)


__all__ = ["create_app", "APIServer", "APISettings", "APIDependencies", "default_dependencies"]
