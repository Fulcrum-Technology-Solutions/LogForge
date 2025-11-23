from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class EntityPayload(BaseModel):
    entity: dict


class EntityResponse(BaseModel):
    type: str
    entity: dict


class EntityImportRequest(BaseModel):
    content: str = Field(..., description="YAML content to import.")


class EntityValidationRequest(BaseModel):
    content: str = Field(..., description="YAML content to validate.")


class GeneratorStatisticsModel(BaseModel):
    events_generated: int = 0
    errors: int = 0
    uptime: int = Field(0, description="Generator uptime in seconds.")
    last_event: Optional[str] = None


class GeneratorFrequencyModel(BaseModel):
    base_rate: int = Field(0, description="Configured base rate (events/sec).")
    current_rate: int = Field(0, description="Current calculated rate (events/sec).")


class GeneratorStatusModel(BaseModel):
    name: str
    template: str
    enabled: bool
    state: str
    frequency: GeneratorFrequencyModel = Field(default_factory=GeneratorFrequencyModel)
    outputs: List[str] = Field(default_factory=list)
    statistics: GeneratorStatisticsModel = Field(default_factory=GeneratorStatisticsModel)


class EngineTotalsModel(BaseModel):
    total: int = 0
    running: int = 0
    degraded: int = 0
    error: int = 0


class SystemStatusModel(BaseModel):
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    threads: int = 0


class HealthResponse(BaseModel):
    status: str = "healthy"
    uptime: int = Field(0, description="API uptime in seconds.")
    generators: EngineTotalsModel = Field(default_factory=EngineTotalsModel)
    entity_registry: str = "healthy"
    template_cache: str = "healthy"


class StatusResponse(BaseModel):
    uptime: int = 0
    version: str
    generators: List[GeneratorStatusModel] = Field(default_factory=list)
    system: SystemStatusModel = Field(default_factory=SystemStatusModel)


class GeneratorControlResponse(BaseModel):
    name: str
    state: str
    message: str


class TemplateSummary(BaseModel):
    id: str
    locations: List[str] = Field(default_factory=list)
    name: Optional[str] = None
    vendor: Optional[str] = None
    product: Optional[str] = None
    data_source: Optional[str] = None
    version: Optional[str] = None
    format: Optional[str] = None


class TemplateCollection(BaseModel):
    templates: List[TemplateSummary] = Field(default_factory=list)


class TemplateDetail(BaseModel):
    id: str
    metadata: dict
    locations: List[str] = Field(default_factory=list)


class TemplateInstallRequest(BaseModel):
    template_id: Optional[str] = None
    url: Optional[str] = None
    package: Optional[str] = None  # base64 encoded archive


class TemplateDiffResponse(BaseModel):
    diff: str


class TemplateValidateRequest(BaseModel):
    archive: str  # base64 encoded archive containing template directory

