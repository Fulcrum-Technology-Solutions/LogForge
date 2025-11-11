"""FastAPI application and server lifecycle management."""

from __future__ import annotations

import os
import threading
import time
from typing import Optional

import psutil
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from logforge.api.auth import APIKeyAuth, ensure_api_key, get_auth_dependency
from logforge.api.endpoints.entities import router as entities_router
from logforge.api.endpoints.generators import router as generators_router
from logforge.api.endpoints.system import router as system_router
from logforge.api.endpoints.templates import router as templates_router
from logforge.core.config import APIAuthConfig, LogForgeConfig
from logforge.core.engine import GenerationEngine
from logforge.entities.registry import EntityRegistry
from logforge.outputs.manager import OutputManager
from logforge.templates.manager import TemplateManager
from logforge.utils.logging import get_logger

logger = get_logger(__name__)


def _system_snapshot() -> dict[str, float]:
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / (1024 ** 2)
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_mb": round(memory_mb, 2),
        "threads": process.num_threads(),
    }


def create_app(config: LogForgeConfig) -> FastAPI:
    """Configure and return the FastAPI application."""
    auth_settings: APIAuthConfig = ensure_api_key(config.api.auth)
    app = FastAPI(
        title="LogForge API",
        version=config.version or "1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    cors_origins = config.api.cors_allow_origins or []
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    dependencies = []
    if auth_settings.enabled:
        dependencies.append(get_auth_dependency(config))

    app.include_router(system_router, dependencies=dependencies)
    app.include_router(entities_router, dependencies=dependencies)
    app.include_router(templates_router, dependencies=dependencies)
    app.include_router(generators_router, dependencies=dependencies)

    auth_guard = APIKeyAuth(auth_settings)
    entity_registry = EntityRegistry.from_config(config)
    template_manager = TemplateManager(config, entity_registry)
    output_manager = OutputManager(config)
    generation_engine = GenerationEngine(config, template_manager, output_manager)

    app.state.config = config
    app.state.start_time = time.time()
    app.state.auth_settings = auth_settings
    app.state.auth_guard = lambda token: auth_guard(authorization=token)
    app.state.system_provider = _system_snapshot
    app.state.entity_registry = entity_registry
    app.state.template_manager = template_manager
    app.state.output_manager = output_manager
    app.state.generation_engine = generation_engine

    @app.on_event("startup")
    async def _startup() -> None:
        app.state.start_time = time.time()
        entity_registry.load()
        template_manager.list_templates()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        if config.entity_registry.auto_save:
            entity_registry.save()
        generation_engine.stop_all()

    return app


class APIServer:
    """Embedded Uvicorn server running in a background thread."""

    def __init__(self, config: LogForgeConfig):
        self.config = config
        self.app = create_app(config)
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self, *, background: bool = True, log_level: Optional[str] = None) -> None:
        """Start the API server."""
        if not self.config.api.enabled:
            logger.info("API server disabled via configuration; skipping start.")
            return
        if self.is_running:
            logger.info(
                "API server already running on %s:%s",
                self.config.api.host,
                self.config.api.port,
            )
            return

        log_level_value = (log_level or self.config.logging.level).lower()
        uvicorn_config = uvicorn.Config(
            self.app,
            host=self.config.api.host,
            port=self.config.api.port,
            log_level=log_level_value,
            lifespan="on",
        )
        self._server = uvicorn.Server(uvicorn_config)

        if background:
            logger.info(
                "Starting API server in background on %s:%s",
                self.config.api.host,
                self.config.api.port,
            )
            self._thread = threading.Thread(target=self._server.run, name="logforge-api", daemon=True)
            self._thread.start()
            self._wait_for_startup()
        else:
            logger.info(
                "Starting API server in foreground on %s:%s",
                self.config.api.host,
                self.config.api.port,
            )
            self._server.run()

    def stop(self, *, timeout: float = 5.0) -> None:
        """Stop the API server."""
        if not self._server:
            logger.info("API server not running.")
            return
        logger.info("Stopping API server...")
        self._server.should_exit = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            logger.info("API server thread joined.")
        self._server = None
        self._thread = None

    def restart(self) -> None:
        """Restart the API server."""
        logger.info("Restarting API server...")
        self.stop()
        self.start()

    def _wait_for_startup(self, timeout: float = 5.0) -> None:
        """Wait for Uvicorn server to signal startup."""
        if not self._server:
            return
        started = getattr(self._server, "started", None)
        if started is not None:
            started.wait(timeout=timeout)
        else:
            time.sleep(min(timeout, 0.5))
