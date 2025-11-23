from __future__ import annotations

from __future__ import annotations

from dataclasses import dataclass

from logforge.community.client import CommunityClient
from logforge.core.config import LogForgeConfig
from logforge.core.engine import GenerationEngine
from logforge.core.telemetry import EngineTelemetryProvider, NullEngineTelemetry
from logforge.entities.registry import EntityRegistry
from logforge.templates.engine import TemplateEngine
from logforge.templates.manager import TemplateManager
from logforge.utils.metrics import MetricsRegistry


@dataclass
class APIContext:
    config: LogForgeConfig
    telemetry: EngineTelemetryProvider = NullEngineTelemetry()
    metrics: MetricsRegistry = MetricsRegistry()
    entity_registry: EntityRegistry | None = None
    engine: GenerationEngine | None = None
    template_engine: TemplateEngine | None = None
    template_manager: TemplateManager | None = None
    community_client: CommunityClient | None = None

    def with_overrides(
        self,
        *,
        telemetry: EngineTelemetryProvider | None = None,
        metrics: MetricsRegistry | None = None,
        entity_registry: EntityRegistry | None = None,
        engine: GenerationEngine | None = None,
        template_engine: TemplateEngine | None = None,
        template_manager: TemplateManager | None = None,
        community_client: CommunityClient | None = None,
    ) -> "APIContext":
        return APIContext(
            config=self.config,
            telemetry=telemetry or self.telemetry,
            metrics=metrics or self.metrics,
            entity_registry=entity_registry or self.entity_registry,
            engine=engine or self.engine,
            template_engine=template_engine or self.template_engine,
            template_manager=template_manager or self.template_manager,
            community_client=community_client or self.community_client,
        )

