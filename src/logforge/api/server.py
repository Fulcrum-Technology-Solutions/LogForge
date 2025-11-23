"""FastAPI server utilities."""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Optional

import psutil
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest

from logforge.api.auth import build_auth_dependency
from logforge.api.endpoints.community import create_community_router
from logforge.api.endpoints.entities import create_entities_router
from logforge.api.endpoints.generators import create_generators_router
from logforge.api.endpoints.health import create_health_router
from logforge.api.endpoints.metrics import create_metrics_router
from logforge.api.endpoints.outputs import create_outputs_router
from logforge.api.endpoints.templates import create_templates_router
from logforge.api.models import (
    ErrorResponse,
    FrequencyInfo,
    GeneratorStatistics,
    GeneratorStatus,
    GeneratorSummary,
    HealthResponse,
    StatusResponse,
    SystemMetrics,
)
from logforge.templates.loader import TemplateLoader, TemplateRecord

if TYPE_CHECKING:
    from logforge.core.service import LogForgeService


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
    list_generators: Callable[[], list[dict[str, Any]]] = lambda: []
    get_generator: Callable[[str], Optional[dict[str, Any]]] = lambda _t: None
    start_generator: Callable[[str], dict[str, Any]] = lambda _t: {}
    stop_generator: Callable[[str], dict[str, Any]] = lambda _t: {}
    restart_generator: Callable[[str], dict[str, Any]] = lambda _t: {}
    list_outputs: Callable[[], list[dict[str, Any]]] = lambda: []
    get_output: Callable[[str], Optional[dict[str, Any]]] = lambda _t: None


def build_dependencies_from_service(service: "LogForgeService") -> APIDependencies:
    """Build API dependencies from a LogForgeService instance."""
    start_time = time.monotonic()

    def health() -> HealthResponse:
        snapshots = service.engine.list_snapshots()
        running = sum(1 for s in snapshots if s.state.value == "RUNNING")
        degraded = sum(1 for s in snapshots if s.state.value == "DEGRADED")
        error = sum(1 for s in snapshots if s.state.value == "ERROR")
        total = len(snapshots)

        status_val = "healthy"
        if error > 0:
            status_val = "unhealthy"
        elif degraded > 0:
            status_val = "degraded"

        return HealthResponse(
            status=status_val,
            uptime=int(time.monotonic() - start_time),
            generators=GeneratorSummary(
                total=total,
                running=running,
                degraded=degraded,
                error=error,
            ),
            entity_registry="healthy",  # TODO: check registry health
            template_cache="healthy",  # TODO: check template cache health
        )

    def status() -> StatusResponse:
        snapshots = service.engine.list_snapshots()
        generators = []
        for snapshot in snapshots:
            freq_controller = None
            for gen in service.engine._generators.values():
                if gen.config.name == snapshot.name:
                    freq_controller = gen.frequency
                    break

            current_rate = freq_controller.current_rate() if freq_controller else snapshot.frequency.get("base_rate", 0)
            generators.append(
                GeneratorStatus(
                    name=snapshot.name,
                    state=snapshot.state.value,
                    template=snapshot.template,
                    enabled=snapshot.enabled,
                    frequency=FrequencyInfo(
                        base_rate=snapshot.frequency.get("base_rate", 0),
                        current_rate=current_rate,
                    ),
                    outputs=snapshot.outputs,
                    statistics=GeneratorStatistics(
                        events_generated=snapshot.statistics.get("events_generated", 0),
                        errors=snapshot.statistics.get("errors", 0),
                        uptime=int(snapshot.statistics.get("uptime", 0.0)),
                        last_event=snapshot.statistics.get("last_event"),
                    ),
                )
            )

        process = psutil.Process(os.getpid())
        return StatusResponse(
            uptime=int(time.monotonic() - start_time),
            version="1.0.0",
            generators=generators,
            system=SystemMetrics(
                cpu_percent=process.cpu_percent(interval=0.1),
                memory_mb=process.memory_info().rss / 1024 / 1024,
                threads=process.num_threads(),
            ),
        )

    def metrics() -> bytes:
        # Update generator state metrics from current service state
        if hasattr(service, "engine"):
            service.engine._update_generator_metrics()
        # Generate Prometheus metrics from all registered collectors
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
        return [template_summary(record) for record in service.template_loader.list_templates()]

    def get_template(template_id: str) -> Optional[dict[str, Any]]:
        record = service.template_loader.get_template(template_id)
        if record is None:
            return None
        return template_detail(record)

    def list_generators() -> list[dict[str, Any]]:
        snapshots = service.engine.list_snapshots()
        result = []
        for snapshot in snapshots:
            freq_controller = None
            for gen in service.engine._generators.values():
                if gen.config.name == snapshot.name:
                    freq_controller = gen.frequency
                    break

            current_rate = freq_controller.current_rate() if freq_controller else snapshot.frequency.get("base_rate", 0)
            result.append({
                "name": snapshot.name,
                "state": snapshot.state.value,
                "template": snapshot.template,
                "enabled": snapshot.enabled,
                "frequency": {
                    "base_rate": snapshot.frequency.get("base_rate", 0),
                    "current_rate": current_rate,
                },
                "outputs": snapshot.outputs,
                "statistics": snapshot.statistics,
            })
        return result

    def get_generator(name: str) -> Optional[dict[str, Any]]:
        try:
            snapshot = service.engine.snapshot(name)
            freq_controller = service.engine._generators[name].frequency
            current_rate = freq_controller.current_rate()
            return {
                "name": snapshot.name,
                "state": snapshot.state.value,
                "template": snapshot.template,
                "enabled": snapshot.enabled,
                "frequency": {
                    "base_rate": snapshot.frequency.get("base_rate", 0),
                    "current_rate": current_rate,
                },
                "outputs": snapshot.outputs,
                "statistics": snapshot.statistics,
            }
        except KeyError:
            return None

    def start_generator(name: str) -> dict[str, Any]:
        snapshot = service.engine.start(name)
        freq_controller = service.engine._generators[name].frequency
        current_rate = freq_controller.current_rate()
        return {
            "name": snapshot.name,
            "state": snapshot.state.value,
            "template": snapshot.template,
            "enabled": snapshot.enabled,
            "frequency": {
                "base_rate": snapshot.frequency.get("base_rate", 0),
                "current_rate": current_rate,
            },
            "outputs": snapshot.outputs,
            "statistics": snapshot.statistics,
        }

    def stop_generator(name: str) -> dict[str, Any]:
        snapshot = service.engine.stop(name)
        freq_controller = service.engine._generators[name].frequency
        current_rate = freq_controller.current_rate()
        return {
            "name": snapshot.name,
            "state": snapshot.state.value,
            "template": snapshot.template,
            "enabled": snapshot.enabled,
            "frequency": {
                "base_rate": snapshot.frequency.get("base_rate", 0),
                "current_rate": current_rate,
            },
            "outputs": snapshot.outputs,
            "statistics": snapshot.statistics,
        }

    def restart_generator(name: str) -> dict[str, Any]:
        snapshot = service.engine.restart(name)
        freq_controller = service.engine._generators[name].frequency
        current_rate = freq_controller.current_rate()
        return {
            "name": snapshot.name,
            "state": snapshot.state.value,
            "template": snapshot.template,
            "enabled": snapshot.enabled,
            "frequency": {
                "base_rate": snapshot.frequency.get("base_rate", 0),
                "current_rate": current_rate,
            },
            "outputs": snapshot.outputs,
            "statistics": snapshot.statistics,
        }

    def list_outputs() -> list[dict[str, Any]]:
        # TODO: Track output instances and their status
        outputs = []
        for definition in service.config.outputs.definitions:
            outputs.append({
                "name": definition.name,
                "type": definition.type,
                "status": "healthy",
                "configuration": definition.model_dump(exclude={"name", "type"}),
                "statistics": {
                    "events_sent": 0,
                    "errors": 0,
                    "buffered_events": 0,
                    "last_error": None,
                },
            })
        return outputs

    def get_output(name: str) -> Optional[dict[str, Any]]:
        for definition in service.config.outputs.definitions:
            if definition.name == name:
                return {
                    "name": definition.name,
                    "type": definition.type,
                    "status": "healthy",
                    "configuration": definition.model_dump(exclude={"name", "type"}),
                    "statistics": {
                        "events_sent": 0,
                        "errors": 0,
                        "buffered_events": 0,
                        "last_error": None,
                    },
                }
        return None

    return APIDependencies(
        get_health=health,
        get_status=status,
        get_metrics=metrics,
        entities_summary=service.entity_registry.summary,
        list_entities=lambda entity_type: service.entity_registry.list_entities(entity_type),
        create_entity=lambda entity_type, payload: service.entity_registry.add_entity(entity_type, payload),
        list_templates=list_templates,
        get_template=get_template,
        list_generators=list_generators,
        get_generator=get_generator,
        start_generator=start_generator,
        stop_generator=stop_generator,
        restart_generator=restart_generator,
        list_outputs=list_outputs,
        get_output=get_output,
    )


def default_dependencies() -> APIDependencies:
    """Create default mock dependencies for testing."""
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
    generator_snapshots = [status.model_dump() for status in generators]
    outputs_data = [
        {
            "name": "default_file",
            "type": "file",
            "status": "healthy",
            "configuration": {"path": "{generator}.log"},
            "statistics": {
                "events_sent": 0,
                "errors": 0,
                "buffered_events": 0,
                "last_error": None,
            },
        }
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

    def metrics() -> bytes:
        # Generate Prometheus metrics from all registered collectors
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

    def list_generators() -> list[dict[str, Any]]:
        return generator_snapshots

    def get_generator(name: str) -> Optional[dict[str, Any]]:
        for snapshot in generator_snapshots:
            if snapshot["name"] == name:
                return snapshot
        return None

    def start_generator(name: str) -> dict[str, Any]:
        snapshot = get_generator(name)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="Generator not found")
        return snapshot

    def stop_generator(name: str) -> dict[str, Any]:
        snapshot = get_generator(name)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="Generator not found")
        return snapshot

    def restart_generator(name: str) -> dict[str, Any]:
        snapshot = get_generator(name)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="Generator not found")
        return snapshot

    def list_outputs() -> list[dict[str, Any]]:
        return outputs_data

    def get_output(name: str) -> Optional[dict[str, Any]]:
        for output in outputs_data:
            if output["name"] == name:
                return output
        return None

    return APIDependencies(
        get_health=health,
        get_status=status,
        get_metrics=metrics,
        entities_summary=registry.summary,
        list_entities=lambda entity_type: registry.list_entities(entity_type),
        create_entity=lambda entity_type, payload: registry.add_entity(entity_type, payload),
        list_templates=list_templates,
        get_template=get_template,
        list_generators=list_generators,
        get_generator=get_generator,
        start_generator=start_generator,
        stop_generator=stop_generator,
        restart_generator=restart_generator,
        list_outputs=list_outputs,
        get_output=get_output,
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

    _register_exception_handlers(app)

    health_router = create_health_router(deps, auth_dependency)
    metrics_router = create_metrics_router(deps, auth_dependency)
    entities_router = create_entities_router(deps, auth_dependency)
    templates_router = create_templates_router(deps, auth_dependency)
    community_router = create_community_router(auth_dependency)
    outputs_router = create_outputs_router(deps, auth_dependency)
    generators_router = create_generators_router(deps, auth_dependency)

    app.include_router(health_router, prefix="/api")
    app.include_router(metrics_router, prefix="/api")
    app.include_router(entities_router, prefix="/api")
    app.include_router(templates_router, prefix="/api")
    app.include_router(community_router, prefix="/api")
    app.include_router(outputs_router, prefix="/api")
    app.include_router(generators_router, prefix="/api")

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


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def _handle_http_exception(request, exc: HTTPException) -> JSONResponse:
        payload = ErrorResponse(error=str(exc.detail)).model_dump()
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def _handle_request_validation(request, exc: RequestValidationError) -> JSONResponse:
        payload = ErrorResponse(
            error="Request validation failed.",
            details=exc.errors(),
        ).model_dump()
        return JSONResponse(status_code=422, content=payload)

    @app.exception_handler(Exception)
    async def _handle_unexpected_exception(request, exc: Exception) -> JSONResponse:
        payload = ErrorResponse(error="Internal server error.", details=str(exc)).model_dump()
        return JSONResponse(status_code=500, content=payload)


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
