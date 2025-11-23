from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List

from logforge.core.config import GeneratorConfig
from logforge.core.frequency import FrequencyProfile
from logforge.core.telemetry import GeneratorStatistics, GeneratorTelemetry, GeneratorState
from logforge.templates.engine import TemplateEngine
from logforge.outputs.base import OutputHandler

LOGGER = logging.getLogger(__name__)


class GeneratorLifecycleState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


@dataclass
class GeneratorRuntime:
    config: GeneratorConfig
    engine: TemplateEngine
    frequency: FrequencyProfile
    state: GeneratorLifecycleState = GeneratorLifecycleState.STOPPED
    statistics: GeneratorStatistics = field(default_factory=GeneratorStatistics)
    task: Optional[asyncio.Task] = None
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)
    outputs: List[OutputHandler] = field(default_factory=list)

    def to_telemetry(self) -> GeneratorTelemetry:
        return GeneratorTelemetry(
            name=self.config.name,
            template=self.config.template,
            enabled=self.config.enabled,
            state=GeneratorState(self.state.value),
            frequency_base_rate=self.config.frequency.base_rate,
            frequency_current_rate=self.frequency.current_rate(),
            outputs=[handler.name for handler in self.outputs],
            statistics=self.statistics,
        )

