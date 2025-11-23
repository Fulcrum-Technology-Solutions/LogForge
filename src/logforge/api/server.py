from __future__ import annotations

import asyncio
import logging
import threading
from typing import Optional

import uvicorn
from fastapi import FastAPI

from logforge import __version__
from logforge.api.context import APIContext
from logforge.api.endpoints import health as health_endpoints
from logforge.api.endpoints import entities as entities_endpoints
from logforge.api.endpoints import generators as generators_endpoints
from logforge.api.endpoints import templates as templates_endpoints
from logforge.core.config import LogForgeConfig
from logforge.core.engine import GenerationEngine
from logforge.core.telemetry import EngineTelemetryProvider, NullEngineTelemetry
from logforge.entities.functions import RegistryFunctions
from logforge.entities.registry import EntityRegistry
from logforge.outputs.factory import OutputFactory
from logforge.community.client import CommunityClient
from logforge.templates.engine import TemplateEngine
from logforge.templates.loader import TemplateLoader
from logforge.templates.metadata import MetadataLoader
from logforge.templates.renderer import TemplateRenderer
from logforge.templates.manager import TemplateManager
from logforge.utils.metrics import MetricsRegistry

LOGGER = logging.getLogger(__name__)


def create_app(context: APIContext) -> FastAPI:
    app = FastAPI(
        title="LogForge Management API",
        version=__version__,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.include_router(health_endpoints.router, prefix="/api", tags=["core"])
    app.include_router(entities_endpoints.router, prefix="/api", tags=["entities"])
    app.include_router(generators_endpoints.router, prefix="/api", tags=["generators"])
    app.include_router(templates_endpoints.router, prefix="/api", tags=["templates"])
    app.state.context = context
    return app


class ManagementAPIServer:
    def __init__(
        self,
        config: LogForgeConfig,
        telemetry: Optional[EngineTelemetryProvider] = None,
        metrics: Optional[MetricsRegistry] = None,
        entity_registry: Optional[EntityRegistry] = None,
    ) -> None:
        self._config = config

        metrics_registry = metrics or MetricsRegistry()
        registry = entity_registry or EntityRegistry(config.entity_registry)

        template_loader = TemplateLoader(config.templates)
        metadata_loader = MetadataLoader(config.templates, template_loader)
        renderer = TemplateRenderer(config.templates.local_path, RegistryFunctions(registry))
        template_engine = TemplateEngine(template_loader, metadata_loader, renderer)
        template_manager = TemplateManager(config.templates, template_loader, metadata_loader)
        community_client = CommunityClient(config.templates.community_api_url)
        output_factory = OutputFactory(config.outputs)
        outputs = output_factory.create_all(metrics_registry)

        self._generation_engine = GenerationEngine(template_engine, metrics=metrics_registry, outputs=outputs)
        for generator_config in config.generators:
            asyncio.run(self._generation_engine.register_generator(generator_config))

        self._context = APIContext(
            config=config,
            telemetry=self._generation_engine,
            metrics=metrics_registry,
            entity_registry=registry,
            engine=self._generation_engine,
            template_engine=template_engine,
            template_manager=template_manager,
            community_client=community_client,
        )
        self._app = create_app(self._context)
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[uvicorn.Server] = None

    @property
    def app(self) -> FastAPI:
        return self._app

    @property
    def context(self) -> APIContext:
        return self._context

    def start(self) -> None:
        api_config = self._config.api
        if not api_config.enabled:
            LOGGER.info("Management API disabled via configuration; skipping start.")
            return

        if self._thread and self._thread.is_alive():
            LOGGER.debug("Management API already running.")
            return

        uvicorn_config = uvicorn.Config(
            self._app,
            host=api_config.host,
            port=api_config.port,
            log_level=self._config.engine.log_level.lower(),
            lifespan="on",
        )
        self._server = uvicorn.Server(uvicorn_config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        LOGGER.info("Management API server starting on %s:%s", api_config.host, api_config.port)

    def stop(self) -> None:
        if not self._server:
            return
        LOGGER.info("Stopping Management API server.")
        self._server.should_exit = True
        if self._thread:
            self._thread.join(timeout=5)
        self._server = None
        self._thread = None

