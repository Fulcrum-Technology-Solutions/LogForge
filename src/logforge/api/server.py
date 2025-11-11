from __future__ import annotations

import os
import threading
import time
from typing import Optional

import psutil
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from logforge.api.auth import APIKeyAuth, ensure_api_key
from logforge.api.endpoints.system import router as system_router
from logforge.core.config import ApiAuthSettings, LogForgeConfig
from logforge.utils.logging import get_logger

logger = get_logger(__name__)


def _system_snapshot() -> dict[str, float]:
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / (1024**2)
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_mb": round(memory_mb, 2),
        "threads": process.num_threads(),
    }


def create_app(config: LogForgeConfig) -> FastAPI:
    auth_settings: ApiAuthSettings = ensure_api_key(config.api.auth)
    app = FastAPI(
        title="LogForge API",
        version=config.version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(system_router)

    auth_guard = APIKeyAuth(auth_settings)

    app.state.config = config
    app.state.start_time = time.time()
    app.state.auth_guard = lambda token: auth_guard(authorization=token)
    app.state.system_provider = _system_snapshot
    app.state.auth_settings = auth_settings

    @app.on_event("startup")
    async def _startup() -> None:
        app.state.start_time = time.time()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        ...

    return app


class ApiServer:
    def __init__(self, config: LogForgeConfig) -> None:
        self._config = config
        self._app = create_app(config)
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def app(self) -> FastAPI:
        return self._app

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self, *, background: bool = True, log_level: str = "info") -> None:
        if not self._config.api.enabled:
            logger.info("API server disabled via configuration; skipping start.")
            return
        if self.is_running:
            logger.info("API server already running on %s:%s", self._config.api.host, self._config.api.port)
            return

        uvicorn_config = uvicorn.Config(
            app=self._app,
            host=self._config.api.host,
            port=self._config.api.port,
            log_level=log_level,
            lifespan="on",
        )
        self._server = uvicorn.Server(uvicorn_config)

        if background:
            logger.info("Starting API server in background on %s:%s", self._config.api.host, self._config.api.port)
            self._thread = threading.Thread(target=self._server.run, name="logforge-api", daemon=True)
            self._thread.start()
        else:
            logger.info("Starting API server in foreground on %s:%s", self._config.api.host, self._config.api.port)
            self._server.run()

    def stop(self, *, timeout: float = 5.0) -> None:
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
        logger.info("Restarting API server...")
        self.stop()
        self.start()
