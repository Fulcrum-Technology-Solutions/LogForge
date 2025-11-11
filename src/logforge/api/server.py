"""FastAPI application and server lifecycle management."""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, List, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from logforge.core.config import LogForgeConfig

from .auth import require_api_key
from .endpoints.health import router as health_router

GeneratorProvider = Callable[[], List[dict]]
StatusProvider = Callable[[], str]


def create_app(
    config: LogForgeConfig,
    generator_provider: Optional[GeneratorProvider] = None,
    entity_registry_health: Optional[StatusProvider] = None,
    template_cache_health: Optional[StatusProvider] = None,
) -> FastAPI:
    """Create FastAPI application configured for LogForge."""
    app = FastAPI(
        title="LogForge Management API",
        version=config.version or "1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    app.state.start_time = time.time()
    app.state.config = config
    app.state.get_generators = generator_provider or (lambda: [])
    app.state.entity_registry_health = entity_registry_health or (lambda: "healthy")
    app.state.template_cache_health = template_cache_health or (lambda: "healthy")

    logger = logging.getLogger("logforge.api")

    if config.api.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.api.cors_allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.on_event("startup")
    async def _on_startup() -> None:  # pragma: no cover - event hook
        logger.info("LogForge API starting on %s:%s", config.api.host, config.api.port)

    @app.on_event("shutdown")
    async def _on_shutdown() -> None:  # pragma: no cover - event hook
        logger.info("LogForge API shutting down")

    dependencies = []
    if config.api.auth.enabled and config.api.auth.key:
        dependencies.append(require_api_key(config.api.auth.key))

    app.include_router(health_router, prefix="/api", dependencies=dependencies)
    return app


class APIServer:
    """Embedded Uvicorn server running in a background thread."""

    def __init__(self, config: LogForgeConfig):
        self.config = config
        self.app = create_app(config)
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

    def start(self, *, background: bool = True) -> None:
        """Start the API server."""
        if not self.config.api.enabled:
            raise RuntimeError("API server disabled in configuration")
        if self.is_running:
            return

        uvicorn_config = uvicorn.Config(
            self.app,
            host=self.config.api.host,
            port=self.config.api.port,
            log_level=self.config.logging.level.lower(),
            lifespan="on",
        )
        self._server = uvicorn.Server(uvicorn_config)

        if background:
            thread = threading.Thread(target=self._server.run, daemon=True)
            thread.start()
            self._thread = thread
            self._wait_for_startup()
        else:
            self._server.run()

    def stop(self, *, timeout: float = 5.0) -> None:
        """Stop the API server."""
        if not self._server:
            return
        self._server.should_exit = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        self._server = None
        self._thread = None

    @property
    def is_running(self) -> bool:
        return bool(self._server and self._thread and self._thread.is_alive())

    def _wait_for_startup(self, timeout: float = 5.0) -> None:
        """Wait for Uvicorn server to signal startup."""
        if not self._server:
            return
        started = getattr(self._server, "started", None)
        if started is not None:
            started.wait(timeout=timeout)
        else:  # pragma: no cover - fallback for unexpected uvicorn changes
            time.sleep(min(timeout, 0.5))
