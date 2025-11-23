"""Pydantic models for API responses."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from logforge.templates.models import TemplateMetadata


class GeneratorSummary(BaseModel):
    total: int = 0
    running: int = 0
    degraded: int = 0
    error: int = 0


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    uptime: int = 0
    generators: GeneratorSummary = Field(default_factory=GeneratorSummary)
    entity_registry: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    template_cache: Literal["healthy", "degraded", "unhealthy"] = "healthy"


class FrequencyInfo(BaseModel):
    base_rate: int
    current_rate: Optional[int] = None


class GeneratorStatistics(BaseModel):
    events_generated: int = 0
    errors: int = 0
    uptime: int = 0
    last_event: Optional[str] = None


class GeneratorStatus(BaseModel):
    name: str
    state: Literal["STOPPED", "STARTING", "RUNNING", "DEGRADED", "ERROR"]
    template: str
    enabled: bool = True
    frequency: FrequencyInfo
    outputs: list[str]
    statistics: GeneratorStatistics = Field(default_factory=GeneratorStatistics)


class SystemMetrics(BaseModel):
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    threads: int = 0


class StatusResponse(BaseModel):
    uptime: int = 0
    version: str = "0.0.0"
    generators: list[GeneratorStatus] = Field(default_factory=list)
    system: SystemMetrics = Field(default_factory=SystemMetrics)


class TemplateSummary(BaseModel):
    id: str
    name: str
    vendor: str
    product: str
    data_source: str
    version: Optional[str] = None
    location: str


class TemplateListResponse(BaseModel):
    templates: list[TemplateSummary] = Field(default_factory=list)


class TemplateDetailResponse(BaseModel):
    summary: TemplateSummary
    metadata: TemplateMetadata


__all__ = [
    "HealthResponse",
    "StatusResponse",
    "GeneratorStatus",
    "GeneratorSummary",
    "SystemMetrics",
    "TemplateSummary",
    "TemplateListResponse",
    "TemplateDetailResponse",
]
