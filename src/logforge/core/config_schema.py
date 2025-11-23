"""Pydantic models for LogForge configuration."""

from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class EngineConfig(BaseModel):
    max_generators: Optional[int] = Field(default=None, ge=1)
    thread_pool_size: Optional[int] = Field(default=None, ge=1)
    log_level: LogLevel = "INFO"


class APIAuthConfig(BaseModel):
    enabled: bool = False
    key: Optional[str] = None

    @model_validator(mode="after")
    def ensure_key_when_enabled(self) -> APIAuthConfig:
        if self.enabled and not self.key:
            raise ValueError("API auth key is required when auth.enabled is true.")
        return self


class APIConfig(BaseModel):
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = Field(8080, ge=1, le=65535)
    auth: APIAuthConfig = APIAuthConfig()


class EntityRegistryConfig(BaseModel):
    path: str
    auto_save: bool = True
    save_interval: int = Field(60, ge=1)
    backup_enabled: bool = True
    backup_count: int = Field(3, ge=0)


class TemplateConfig(BaseModel):
    local_path: str
    default_path: Optional[str] = None
    custom_path: Optional[str] = None
    precedence: Literal["custom_first", "default_first", "explicit"] = "custom_first"
    community_api_url: str
    auto_update_check: bool = True
    cache_ttl: int = Field(3600, ge=0)
    auto_backup_on_customize: Optional[bool] = None
    diff_tool: Optional[str] = "auto"


class LoggingRotationConfig(BaseModel):
    max_size: Optional[str] = None
    max_age: Optional[str] = None
    backup_count: int = Field(5, ge=0)
    compress: bool = True
    type: Literal["size", "time"] = "size"


class LoggingConfig(BaseModel):
    level: LogLevel = "INFO"
    file: str
    rotation: Optional[LoggingRotationConfig] = None
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class OutputRetryConfig(BaseModel):
    max_attempts: int = -1
    retry_interval: int = Field(5, ge=0)
    backoff_multiplier: float = Field(2.0, gt=0)
    max_backoff: int = Field(300, ge=0)


def _default_retry_config() -> OutputRetryConfig:
    return OutputRetryConfig(
        max_attempts=-1,
        retry_interval=5,
        backoff_multiplier=2.0,
        max_backoff=300,
    )


class OutputConfig(BaseModel):
    buffer_size: int = Field(10000, ge=0)
    retry: OutputRetryConfig = Field(default_factory=_default_retry_config)
    definitions: List["OutputDefinition"]


class OutputDefinition(BaseModel):
    name: str
    type: Literal["file", "console", "http", "tcp", "syslog"]
    path: Optional[str] = None
    rotation: Optional[LoggingRotationConfig] = None
    format: Optional[str] = None
    stream: Optional[Literal["stdout", "stderr"]] = None
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[dict[str, Any]] = None
    host: Optional[str] = None
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    protocol: Optional[Literal["tcp", "udp", "tls"]] = None
    delimiter: Optional[str] = None
    syslog_format: Optional[Literal["rfc5424", "rfc3164"]] = None
    facility: Optional[int] = Field(default=None, ge=0, le=23)
    severity: Optional[int] = Field(default=None, ge=0, le=7)
    app_name: Optional[str] = None
    batch_size: Optional[int] = Field(default=None, ge=1)
    batch_interval: Optional[int] = Field(default=None, ge=0)
    timeout: Optional[int] = Field(default=None, ge=1)

    @model_validator(mode="after")
    def ensure_required_fields(self) -> OutputDefinition:
        if self.type == "file" and not self.path:
            raise ValueError("File outputs require 'path'.")
        if self.type == "console" and not self.format:
            raise ValueError("Console outputs require 'format'.")
        if self.type == "http" and not self.url:
            raise ValueError("HTTP outputs require 'url'.")
        if self.type in {"tcp", "syslog"}:
            if not self.host or not self.port:
                raise ValueError(f"{self.type.upper()} outputs require 'host' and 'port'.")
        return self


class FrequencyVariationConfig(BaseModel):
    days: Optional[List[int]] = None
    time: Optional[str] = None
    multiplier: float = Field(1.0, gt=0)

    @field_validator("days")
    def ensure_valid_days(cls, value: Optional[List[int]]) -> Optional[List[int]]:
        if value is None:
            return value
        invalid = [day for day in value if day < 1 or day > 7]
        if invalid:
            raise ValueError("Days must be between 1 (Monday) and 7 (Sunday).")
        return value


class FrequencyConfig(BaseModel):
    base_rate: int = Field(ge=1)
    variation: Optional[List[FrequencyVariationConfig]] = None


class GeneratorConfig(BaseModel):
    name: str
    template: str
    enabled: bool = True
    outputs: List[str]
    frequency: FrequencyConfig


class ConfigModel(BaseModel):
    version: str = "1.0"
    engine: EngineConfig
    api: APIConfig
    entity_registry: EntityRegistryConfig
    templates: TemplateConfig
    logging: LoggingConfig
    outputs: OutputConfig
    generators: List[GeneratorConfig]

    @model_validator(mode="after")
    def ensure_generators_present(self) -> ConfigModel:
        if not self.generators:
            raise ValueError("At least one generator must be defined.")
        return self


def summarize_validation_error(exc: ValidationError) -> str:
    parts = []
    for error in exc.errors():
        loc = ".".join(str(item) for item in error["loc"])
        parts.append(f"{loc}: {error['msg']}")
    return "; ".join(parts)


OutputConfig.model_rebuild()
ConfigModel.model_rebuild()

__all__ = [
    "ConfigModel",
    "EngineConfig",
    "APIConfig",
    "EntityRegistryConfig",
    "TemplateConfig",
    "LoggingConfig",
    "OutputConfig",
    "GeneratorConfig",
    "summarize_validation_error",
]
