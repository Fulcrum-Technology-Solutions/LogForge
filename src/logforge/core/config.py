from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, HttpUrl, PositiveInt, root_validator, validator, model_validator

LOGFORGE_HOME_ENV = "LOGFORGE_HOME"
DEFAULT_LOGFORGE_HOME = Path("/opt/logforge")
DEFAULT_CONFIG_FILENAME = "config.yaml"


class ConfigError(Exception):
    """Raised when configuration files are invalid or inconsistent."""


def resolve_logforge_home() -> Path:
    """
    Determine the root directory for all LogForge assets.

    Defaults to `/opt/logforge`. Environment overrides are honored but must resolve to an
    absolute path. The directory does not need to exist; callers can create it.
    """

    home = os.environ.get(LOGFORGE_HOME_ENV)
    path = Path(home).expanduser() if home else DEFAULT_LOGFORGE_HOME
    if not path.is_absolute():
        raise ConfigError(f"LOGFORGE_HOME must be absolute: {path!s}")
    return path


def _ensure_within_home(path: Path, home: Path, field_name: str) -> Path:
    """
    Ensure the provided path is contained within the LogForge home directory.
    """

    resolved = (home / path) if not path.is_absolute() else path
    try:
        resolved_resolved = resolved.resolve(strict=False)
    except OSError as exc:
        raise ConfigError(f"Failed to resolve {field_name}: {path!s}") from exc

    if not str(resolved_resolved).startswith(str(home.resolve(strict=False))):
        raise ConfigError(
            f"{field_name} must reside within LOGFORGE_HOME ({home!s}); got {resolved_resolved!s}"
        )
    return resolved_resolved


class EngineConfig(BaseModel):
    max_generators: Optional[int] = Field(default=None, ge=1)
    thread_pool_size: Optional[int] = Field(default=None, ge=1)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


class APIAuthConfig(BaseModel):
    enabled: bool = False
    key: Optional[str] = None


class APIConfig(BaseModel):
    enabled: bool = True
    host: str = "127.0.0.1"
    port: PositiveInt = 8080
    auth: APIAuthConfig = Field(default_factory=APIAuthConfig)


class EntityRegistryConfig(BaseModel):
    path: Path
    auto_save: bool = True
    save_interval: PositiveInt = 60
    backup_enabled: bool = True
    backup_count: PositiveInt = 3

    @validator("path", pre=True)
    def _validate_path(cls, value: Any) -> Path:  # noqa: B902
        return Path(value)


class TemplateCustomizationConfig(BaseModel):
    auto_backup_on_customize: bool = True
    diff_tool: Literal["auto", "vimdiff", "meld", "custom"] = "auto"


class TemplateConfig(BaseModel):
    local_path: Path = Path("templates")
    default_path: Path = Path("templates/default")
    custom_path: Path = Path("templates/custom")
    precedence: Literal["custom_first", "default_first", "explicit"] = "custom_first"
    community_api_url: HttpUrl = Field(default="https://api.logforge.io/v1")
    auto_update_check: bool = True
    cache_ttl: PositiveInt = 3600
    customization: TemplateCustomizationConfig = Field(default_factory=TemplateCustomizationConfig)

    @validator("local_path", "default_path", "custom_path", pre=True)
    def _validate_paths(cls, value: Any) -> Path:  # noqa: B902
        return Path(value)


class LoggingRotationConfig(BaseModel):
    type: Literal["size", "time"] = "size"
    max_size: str = "50MB"
    max_age: str = "24h"
    backup_count: PositiveInt = 5
    compress: bool = False


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    file: Path = Path("logforge.log")
    rotation: LoggingRotationConfig = Field(default_factory=LoggingRotationConfig)
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @validator("file", pre=True)
    def _validate_file(cls, value: Any) -> Path:  # noqa: B902
        return Path(value)


class OutputRetryConfig(BaseModel):
    max_attempts: int = -1
    retry_interval: PositiveInt = 5
    backoff_multiplier: float = 2.0
    max_backoff: PositiveInt = 300

    @validator("max_attempts")
    def _check_max_attempts(cls, value: int) -> int:  # noqa: B902
        if value == 0 or value >= -1:
            return value
        raise ValueError("max_attempts must be >= -1")


class OutputDefinition(BaseModel):
    name: str
    type: Literal["file", "console", "http", "tcp", "syslog"]
    options: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_options(self) -> "OutputDefinition":
        opts = self.options or {}
        if self.type == "file":
            path = opts.get("path")
            if not isinstance(path, str) or not path:
                raise ValueError("File output requires non-empty 'path'.")
        elif self.type == "console":
            fmt = opts.get("format", "text")
            if fmt not in {"text", "json"}:
                raise ValueError("Console output format must be 'text' or 'json'.")
        elif self.type == "http":
            url = opts.get("url")
            if not isinstance(url, str) or not url:
                raise ValueError("HTTP output requires 'url'.")
            batch_size = opts.get("batch_size", 1)
            if int(batch_size) <= 0:
                raise ValueError("HTTP output batch_size must be > 0.")
        elif self.type == "tcp":
            if not isinstance(opts.get("host"), str) or not opts.get("host"):
                raise ValueError("TCP output requires 'host'.")
            port = opts.get("port")
            if not isinstance(port, int) or not (1 <= port <= 65535):
                raise ValueError("TCP output requires 'port' between 1 and 65535.")
        elif self.type == "syslog":
            if not isinstance(opts.get("host"), str) or not opts.get("host"):
                raise ValueError("Syslog output requires 'host'.")
            port = opts.get("port", 514)
            if not isinstance(port, int) or not (1 <= port <= 65535):
                raise ValueError("Syslog output requires 'port' between 1 and 65535.")
        return self


class OutputsConfig(BaseModel):
    retry: OutputRetryConfig = Field(default_factory=OutputRetryConfig)
    buffer_size: PositiveInt = 10000
    definitions: List[OutputDefinition] = Field(default_factory=list)


class FrequencyVariation(BaseModel):
    days: Optional[List[int]] = None
    time: Optional[str] = None
    multiplier: float = 1.0

    @validator("days", each_item=True)
    def _validate_days(cls, value: int) -> int:  # noqa: B902
        if value < 1 or value > 7:
            raise ValueError("days entries must be between 1 (Monday) and 7 (Sunday)")
        return value


class GeneratorFrequencyConfig(BaseModel):
    base_rate: PositiveInt
    variation: List[FrequencyVariation] = Field(default_factory=list)


class GeneratorConfig(BaseModel):
    name: str
    template: str
    enabled: bool = True
    frequency: GeneratorFrequencyConfig
    outputs: List[str] = Field(default_factory=list)


class LogForgeConfig(BaseModel):
    version: str = "1.0"
    engine: EngineConfig = Field(default_factory=EngineConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    entity_registry: EntityRegistryConfig
    templates: TemplateConfig = Field(default_factory=TemplateConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    outputs: OutputsConfig = Field(default_factory=OutputsConfig)
    generators: List[GeneratorConfig] = Field(default_factory=list)

    @root_validator(pre=True)
    def _merge_templates(cls, values: Dict[str, Any]) -> Dict[str, Any]:  # noqa: B902
        """
        Support legacy template customization keys sitting at the root.
        """

        template_section = values.get("templates", {})
        customization_keys = {
            "auto_backup_on_customize",
            "diff_tool",
        }
        if customization_keys & template_section.keys():
            customization_values = {
                key: template_section.pop(key)
                for key in customization_keys
                if key in template_section
            }
            template_section["customization"] = customization_values
            values["templates"] = template_section
        return values


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except FileNotFoundError as exc:
        raise ConfigError(f"Configuration file not found: {path!s}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path!s}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("Configuration file must contain a mapping at the top level.")
    return data


def _apply_home_paths(config: LogForgeConfig, home: Path) -> LogForgeConfig:
    # entity registry path
    config.entity_registry.path = _ensure_within_home(
        config.entity_registry.path, home, "entity_registry.path"
    )

    # templates paths
    for field_name in ("local_path", "default_path", "custom_path"):
        current = getattr(config.templates, field_name)
        setattr(config.templates, field_name, _ensure_within_home(current, home, f"templates.{field_name}"))

    # logging file
    config.logging.file = _ensure_within_home(config.logging.file, home, "logging.file")

    return config


def load_config(config_path: Optional[Path] = None) -> LogForgeConfig:
    """
    Load and validate the LogForge configuration file.

    If `config_path` is not provided, defaults to `${LOGFORGE_HOME}/config.yaml`.
    """

    home = resolve_logforge_home()
    resolved_config_path = config_path or (home / DEFAULT_CONFIG_FILENAME)

    if not resolved_config_path.is_absolute():
        resolved_config_path = (home / resolved_config_path).resolve()

    data = _load_yaml(resolved_config_path)
    try:
        config = LogForgeConfig.parse_obj(data)
    except Exception as exc:  # pydantic ValidationError
        raise ConfigError(f"Configuration validation failed: {exc}") from exc

    config = _apply_home_paths(config, home)

    return config


def default_config_dict(
    *,
    log_output_dir: Optional[Path] = None,
    default_event_rate: Optional[int] = None,
    api_port: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Provide a seed configuration dictionary matching the OSS requirements.
    """

    output_base = Path(log_output_dir) if log_output_dir else Path("/var/log/logforge")
    generator_rate = default_event_rate or 10
    generator_path = str(output_base / "{generator}.log")

    return {
        "version": "1.0",
        "engine": {
            "max_generators": 10,
            "thread_pool_size": None,
            "log_level": "INFO",
        },
        "api": {
            "enabled": True,
            "host": "127.0.0.1",
            "port": api_port or 8080,
            "auth": {"enabled": False, "key": None},
        },
        "entity_registry": {
            "path": "entities.yaml",
            "auto_save": True,
            "save_interval": 60,
            "backup_enabled": True,
            "backup_count": 3,
        },
        "templates": {
            "local_path": "templates",
            "default_path": "templates/default",
            "custom_path": "templates/custom",
            "precedence": "custom_first",
            "community_api_url": "https://api.logforge.io/v1",
            "auto_update_check": True,
            "cache_ttl": 3600,
            "customization": {
                "auto_backup_on_customize": True,
                "diff_tool": "auto",
            },
        },
        "logging": {
            "level": "INFO",
            "file": "logforge.log",
            "rotation": {
                "type": "size",
                "max_size": "50MB",
                "max_age": "24h",
                "backup_count": 5,
                "compress": False,
            },
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "outputs": {
            "retry": {
                "max_attempts": -1,
                "retry_interval": 5,
                "backoff_multiplier": 2.0,
                "max_backoff": 300,
            },
            "buffer_size": 10000,
            "definitions": [
                {
                    "name": "default_file",
                    "type": "file",
                    "options": {
                        "path": generator_path,
                        "rotation": {
                            "type": "size",
                            "max_size": "100MB",
                            "max_age": "7d",
                            "compress": True,
                        },
                    },
                },
                {
                    "name": "console_json",
                    "type": "console",
                    "options": {"format": "json"},
                },
            ],
        },
        "generators": [
            {
                "name": "windows_security",
                "template": "microsoft/windows/eventlog/security",
                "enabled": True,
                "frequency": {
                    "base_rate": generator_rate,
                    "variation": [
                        {
                            "days": [1, 2, 3, 4, 5],
                            "time": "09:00-17:00",
                            "multiplier": 2.0,
                        },
                        {
                            "days": [6, 7],
                            "multiplier": 0.5,
                        },
                    ],
                },
                "outputs": ["default_file", "console_json"],
            }
        ],
    }


def write_default_config(
    *,
    target_path: Optional[Path] = None,
    overwrite: bool = False,
    config_data: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Write the default configuration YAML to the given path.
    """

    home = resolve_logforge_home()
    destination = target_path or (home / DEFAULT_CONFIG_FILENAME)
    if not destination.is_absolute():
        destination = home / destination

    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not overwrite:
        raise ConfigError(f"Config already exists: {destination!s}")

    data = config_data or default_config_dict()

    with destination.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)

    return destination


def default_entities_dict(
    *,
    organization_name: str = "Example Organization",
    domain: str = "example.com",
) -> Dict[str, Any]:
    admin_email = f"admin@{domain}"

    return {
        "organization": {
            "name": organization_name,
            "domain": domain,
            "contacts": {"admin": admin_email},
            "attributes": {"industry": "Technology"},
        },
        "users": [
            {
                "username": "admin",
                "email": admin_email,
                "full_name": "Example Admin",
                "department": "Engineering",
                "role": "Administrator",
            }
        ],
        "devices": [
            {
                "hostname": "app-01",
                "ip_address": "192.168.1.100",
                "mac_address": "00:11:22:33:44:55",
                "os": "Ubuntu 22.04",
                "owner": "admin",
            }
        ],
        "services": [
            {
                "name": "example_service",
                "description": "Example service placeholder",
                "url": "https://service.example.com",
                "port": 443,
                "protocol": "https",
            }
        ],
    }


def write_default_entities(
    *,
    target_path: Optional[Path] = None,
    overwrite: bool = False,
    organization_name: str = "Example Organization",
    domain: str = "example.com",
) -> Path:
    home = resolve_logforge_home()
    destination = target_path or (home / "entities.yaml")
    if not destination.is_absolute():
        destination = home / destination

    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not overwrite:
        raise ConfigError(f"Entities file already exists: {destination!s}")

    with destination.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            default_entities_dict(
                organization_name=organization_name,
                domain=domain,
            ),
            handle,
            sort_keys=False,
        )

    return destination

