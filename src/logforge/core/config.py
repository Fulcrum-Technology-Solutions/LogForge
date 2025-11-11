"""Configuration management for LogForge."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

DEFAULT_CONFIG_VERSION = "1.0"
ENV_PREFIX = "LOGFORGE"
ENV_SEPARATOR = "__"
ENV_MAPPING_PREFIX = f"{ENV_PREFIX}_"


class ConfigError(RuntimeError):
    """Raised when configuration loading fails."""


def expand_path(path: Optional[str | Path]) -> Optional[str]:
    """Expand user and environment variables in a filesystem path."""
    if path is None:
        return None
    return os.path.expandvars(os.path.expanduser(str(path)))


def _expand_path_to_path(path: str | Path) -> Path:
    expanded = expand_path(path)
    if not expanded:
        raise ValueError("Path expansion produced an empty result")
    return Path(expanded).resolve()


def default_state_dir() -> Path:
    return _expand_path_to_path("~/.logforge")


def default_config_path() -> Path:
    return default_state_dir() / "config.yaml"


def default_entities_path() -> Path:
    return default_state_dir() / "entities.yaml"


def default_templates_dir() -> Path:
    return default_state_dir() / "templates"


def default_logs_path() -> Path:
    return default_state_dir() / "logforge.log"


class LoggingRotationConfig(BaseModel):
    max_size: str = "50MB"
    backup_count: int = 5


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: Path = Field(default_factory=default_logs_path)
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    rotation: LoggingRotationConfig = Field(default_factory=LoggingRotationConfig)

    @field_validator("file", mode="before")
    @classmethod
    def _expand_file(cls, value: str | Path) -> Path:
        expanded = expand_path(value or "")
        return Path(expanded or value)


class APIAuthConfig(BaseModel):
    enabled: bool = False
    key: Optional[str] = None


class APIConfig(BaseModel):
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8080
    auth: APIAuthConfig = Field(default_factory=APIAuthConfig)
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])


class EngineConfig(BaseModel):
    max_generators: Optional[int] = 10
    thread_pool_size: Optional[int] = None
    log_level: str = "INFO"


class EntityRegistryConfig(BaseModel):
    path: Path = Field(default_factory=default_entities_path)
    auto_save: bool = True
    save_interval: int = 60
    backup_enabled: bool = True
    backup_count: int = 3

    @field_validator("path", mode="before")
    @classmethod
    def _expand_path(cls, value: str | Path) -> Path:
        expanded = expand_path(value or "")
        return Path(expanded or value)


class TemplatesConfig(BaseModel):
    local_path: str = "~/.logforge/templates"
    default_path: str = "~/.logforge/templates/default"
    custom_path: str = "~/.logforge/templates/custom"
    precedence: str = "custom_first"
    community_api_url: str = "https://api.logforge.io/v1"
    auto_update_check: bool = True
    cache_ttl: int = 3600

    @field_validator("local_path", "default_path", "custom_path", mode="before")
    @classmethod
    def _expand_paths(cls, value: str) -> str:
        return str(expand_path(value or ""))


class TemplateSettings(BaseModel):
    local_path: Path = Field(default_factory=default_templates_dir)
    community_api_url: str = "https://api.logforge.io/v1"
    auto_update_check: bool = True
    cache_ttl: int = 3600

class OutputsRetryConfig(BaseModel):
    max_attempts: int = -1
    retry_interval: int = 5
    backoff_multiplier: float = 2.0
    max_backoff: int = 300


class OutputsConfig(BaseModel):
    retry: OutputsRetryConfig = Field(default_factory=OutputsRetryConfig)
    buffer_size: int = 10000
    definitions: list[dict[str, Any]] = Field(default_factory=list)


class GeneratorDefinition(BaseModel):
    name: str
    template: str
    enabled: bool = True
    frequency: Dict[str, Any] = Field(default_factory=dict)
    outputs: list[str] = Field(default_factory=list)


class LogForgeConfig(BaseModel):
    version: str = DEFAULT_CONFIG_VERSION
    engine: EngineConfig = Field(default_factory=EngineConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    entity_registry: EntityRegistryConfig = Field(default_factory=EntityRegistryConfig)
    templates: TemplatesConfig = Field(default_factory=TemplatesConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    outputs: OutputsConfig = Field(default_factory=OutputsConfig)
    generators: list[GeneratorDefinition] = Field(default_factory=list)

    @model_validator(mode="after")
    def _post_init(self) -> "LogForgeConfig":
        if self.api.auth.key and not self.api.auth.enabled:
            self.api.auth.enabled = True
        return self

    def dict_with_expanded_paths(self) -> Dict[str, Any]:
        data = self.model_dump(mode="python")
        _expand_paths_in_place(data)
        return data


def _expand_paths_in_place(payload: Any) -> None:
    if isinstance(payload, dict):
        for key, value in list(payload.items()):
            if isinstance(value, (dict, list)):
                _expand_paths_in_place(value)
            elif isinstance(value, (str, Path)) and key in {"path", "file", "local_path", "default_path", "custom_path"}:
                payload[key] = str(expand_path(value))
    elif isinstance(payload, list):
        for index, entry in enumerate(payload):
            if isinstance(entry, (dict, list)):
                _expand_paths_in_place(entry)


def default_config_dict() -> Dict[str, Any]:
    return {
        "version": DEFAULT_CONFIG_VERSION,
        "engine": {
            "max_generators": 10,
            "thread_pool_size": None,
            "log_level": "INFO",
        },
        "api": {
            "enabled": True,
            "host": "127.0.0.1",
            "port": 8080,
            "auth": {"enabled": False, "key": None},
            "cors_allow_origins": ["*"],
        },
        "entity_registry": {
            "path": "~/.logforge/entities.yaml",
            "auto_save": True,
            "save_interval": 60,
            "backup_enabled": True,
            "backup_count": 3,
        },
        "templates": {
            "local_path": "~/.logforge/templates",
            "default_path": "~/.logforge/templates/default",
            "custom_path": "~/.logforge/templates/custom",
            "precedence": "custom_first",
            "community_api_url": "https://api.logforge.io/v1",
            "auto_update_check": True,
            "cache_ttl": 3600,
        },
        "logging": {
            "level": "INFO",
            "file": "~/.logforge/logforge.log",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "rotation": {"max_size": "50MB", "backup_count": 5},
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
                    "path": "/var/log/logforge/{generator}.log",
                    "rotation": {
                        "type": "size",
                        "max_size": "100MB",
                        "max_age": "7d",
                        "compress": True,
                    },
                },
                {
                    "name": "console_json",
                    "type": "console",
                    "format": "json",
                },
            ],
        },
        "generators": [
            {
                "name": "windows_security",
                "template": "microsoft/windows/eventlog/security",
                "enabled": True,
                "frequency": {
                    "base_rate": 10,
                    "variation": [
                        {"days": [1, 2, 3, 4, 5], "time": "09:00-17:00", "multiplier": 2.0},
                        {"days": [6, 7], "multiplier": 0.5},
                    ],
                },
                "outputs": ["default_file", "console_json"],
            },
            {
                "name": "palo_alto_traffic",
                "template": "paloalto/firewall/traffic",
                "enabled": True,
                "frequency": {"base_rate": 50},
                "outputs": ["default_file"],
            },
        ],
    }


def default_config() -> LogForgeConfig:
    """Instantiate the default configuration model."""
    return LogForgeConfig()


def deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = dict(base)
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def set_in_dict(data: Dict[str, Any], path: Iterable[str], value: Any) -> None:
    current = data
    keys = list(path)
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def _coerce_env_value(raw: str) -> Any:
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _parse_env(env: Mapping[str, str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    prefix = f"{ENV_PREFIX}{ENV_SEPARATOR}"
    for key, raw in env.items():
        if not key.startswith(prefix):
            continue
        parts = [part for part in key[len(prefix) :].split(ENV_SEPARATOR) if part]
        if not parts:
            continue
        normalized = [part.lower() for part in parts]
        value = _coerce_env_value(raw)
        cursor: MutableMapping[str, Any] = result
        for segment in normalized[:-1]:
            if segment not in cursor or not isinstance(cursor[segment], MutableMapping):
                cursor[segment] = {}
            cursor = cursor[segment]  # type: ignore[assignment]
        cursor[normalized[-1]] = value
    return result


ENV_MAPPING = {
    "API_ENABLED": ("api", "enabled"),
    "API_HOST": ("api", "host"),
    "API_PORT": ("api", "port"),
    "API_KEY": ("api", "auth", "key"),
    "API_CORS_ORIGINS": ("api", "cors_allow_origins"),
    "ENGINE_MAX_GENERATORS": ("engine", "max_generators"),
    "ENGINE_THREAD_POOL_SIZE": ("engine", "thread_pool_size"),
    "ENGINE_LOG_LEVEL": ("engine", "log_level"),
    "LOG_LEVEL": ("logging", "level"),
    "LOG_FILE": ("logging", "file"),
    "ENTITIES_PATH": ("entity_registry", "path"),
    "TEMPLATES_PATH": ("templates", "local_path"),
    "TEMPLATES_DEFAULT_PATH": ("templates", "default_path"),
    "TEMPLATES_CUSTOM_PATH": ("templates", "custom_path"),
    "TEMPLATE_PRECEDENCE": ("templates", "precedence"),
    "COMMUNITY_API_URL": ("templates", "community_api_url"),
    "OUTPUT_BUFFER_SIZE": ("outputs", "buffer_size"),
}


def apply_env_overrides(config_data: Dict[str, Any], env: Mapping[str, str]) -> Dict[str, Any]:
    merged = dict(config_data)
    for suffix, path in ENV_MAPPING.items():
        env_key = f"{ENV_MAPPING_PREFIX}{suffix}"
        if env_key not in env:
            continue
        raw_value = env[env_key]
        if raw_value.lower() in {"true", "false"}:
            value: Any = raw_value.lower() == "true"
        else:
            try:
                value = int(raw_value)
            except ValueError:
                try:
                    value = float(raw_value)
                except ValueError:
                    if suffix == "API_CORS_ORIGINS":
                        value = [item.strip() for item in raw_value.split(",") if item.strip()]
                    else:
                        value = raw_value
        set_in_dict(merged, path, value)

    nested_overrides = _parse_env(env)
    if nested_overrides:
        merged = deep_merge(merged, nested_overrides)

    if merged.get("api", {}).get("auth", {}).get("key"):
        set_in_dict(merged, ("api", "auth", "enabled"), True)

    return merged


def load_yaml_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            raise ConfigError(f"Configuration at {path} must be a mapping")
        return data
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse configuration {path}: {exc}") from exc


class ConfigManager:
    """High-level configuration loader and saver."""

    def __init__(self, config_path: Optional[Path] = None):
        env_path = os.environ.get(f"{ENV_MAPPING_PREFIX}CONFIG")
        chosen_path: Optional[Path] = None
        if env_path:
            chosen_path = Path(expand_path(env_path) or env_path)
        if config_path:
            chosen_path = Path(expand_path(config_path) or config_path)
        default_path = default_config_path()
        self.config_path = chosen_path or default_path

    def load(
        self,
        cli_overrides: Optional[Dict[str, Any]] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> LogForgeConfig:
        merged = default_config_dict()
        file_config = load_yaml_file(self.config_path)
        merged = deep_merge(merged, file_config)
        env_mapping = dict(env or os.environ)
        merged = apply_env_overrides(merged, env_mapping)
        if cli_overrides:
            merged = deep_merge(merged, cli_overrides)

        try:
            return LogForgeConfig.model_validate(merged)
        except ValidationError as exc:
            raise ConfigError(str(exc)) from exc

    def save_default(
        self,
        overwrite: bool = False,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Path:
        config_dir = self.config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)
        if self.config_path.exists() and not overwrite:
            raise ConfigError(f"Configuration already exists at {self.config_path}")

        data = default_config_dict()
        if overrides:
            data = deep_merge(data, overrides)

        with self.config_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(data, handle, sort_keys=False)
        return self.config_path

    def ensure_supporting_files(self, base_dir: Optional[Path] = None) -> None:
        cfg = self.load()
        base = Path(base_dir).expanduser() if base_dir else Path(cfg.entity_registry.path).expanduser().parent
        base.mkdir(parents=True, exist_ok=True)

        entities_path = Path(cfg.entity_registry.path).expanduser()
        entities_path.parent.mkdir(parents=True, exist_ok=True)
        if not entities_path.exists():
            entities_path.write_text(
                "organization:\n  name: Example Organization\n  domain: example.com\nusers: []\ndevices: []\nservices: []\n",
                encoding="utf-8",
            )

        templates_default = Path(cfg.templates.default_path).expanduser()
        templates_custom = Path(cfg.templates.custom_path).expanduser()
        templates_default.mkdir(parents=True, exist_ok=True)
        templates_custom.mkdir(parents=True, exist_ok=True)

        log_file = Path(cfg.logging.file).expanduser()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if not log_file.exists():
            log_file.touch()

        for definition in cfg.outputs.definitions:
            if definition.get("type") != "file":
                continue
            path_template = definition.get("path")
            if not path_template:
                continue
            example_path = path_template.replace("{generator}", "example")
            expanded_path = expand_path(example_path) or example_path
            file_path = Path(expanded_path).expanduser()
            file_path.parent.mkdir(parents=True, exist_ok=True)


def load_config(
    config_path: Optional[Path] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    env: Optional[Mapping[str, str]] = None,
) -> LogForgeConfig:
    env_mapping = dict(env or os.environ)
    effective_path = config_path
    for key in ("LOGFORGE_CONFIG", "LOGFORGE_CONFIG_PATH"):
        candidate = env_mapping.get(key)
        if candidate:
            effective_path = Path(candidate)
            break

    manager = ConfigManager(config_path=effective_path)
    return manager.load(cli_overrides=dict(overrides or {}), env=env_mapping)


def write_default_config(target: Optional[Path] = None, force: bool = False) -> Path:
    manager = ConfigManager(config_path=target)
    return manager.save_default(overwrite=force)


def ensure_runtime_paths(base_dir: Optional[Path] = None) -> dict[str, Path]:
    root = Path(base_dir).expanduser() if base_dir else default_state_dir()
    templates_root = root / "templates"
    defaults = {
        "state": root,
        "templates_default": templates_root / "default",
        "templates_custom": templates_root / "custom",
    }
    for path in defaults.values():
        path.mkdir(parents=True, exist_ok=True)
    return defaults
