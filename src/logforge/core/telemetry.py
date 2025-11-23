from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Protocol


class GeneratorState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class GeneratorStatistics:
    events_generated: int = 0
    errors: int = 0
    uptime_seconds: int = 0
    last_event: Optional[str] = None


@dataclass(frozen=True)
class GeneratorTelemetry:
    name: str
    template: str
    enabled: bool
    state: GeneratorState
    frequency_base_rate: int = 0
    frequency_current_rate: int = 0
    outputs: List[str] = field(default_factory=list)
    statistics: GeneratorStatistics = field(default_factory=GeneratorStatistics)


@dataclass(frozen=True)
class EngineTotals:
    total: int = 0
    running: int = 0
    degraded: int = 0
    error: int = 0


@dataclass(frozen=True)
class SystemTelemetry:
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    threads: int = 0


@dataclass(frozen=True)
class EngineSnapshot:
    uptime_seconds: int = 0
    totals: EngineTotals = field(default_factory=EngineTotals)
    generators: List[GeneratorTelemetry] = field(default_factory=list)
    system: SystemTelemetry = field(default_factory=SystemTelemetry)
    entity_registry_status: str = "healthy"
    template_cache_status: str = "healthy"


class EngineTelemetryProvider(Protocol):
    def snapshot(self) -> EngineSnapshot:
        ...


class NullEngineTelemetry(EngineTelemetryProvider):
    def snapshot(self) -> EngineSnapshot:
        return EngineSnapshot()

