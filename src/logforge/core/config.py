from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field

ENV_PREFIX = "LOGFORGE"
ENV_SEPARATOR = "__"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_state_dir() -> Path:
    return expand_path(Path("~/.logforge"))


def default_config_path() -> Path:
    return default_state_dir() / "config.yaml"


def default_entities_path() -> Path:
    return default_state_dir() / "entities.yaml"


def default_templates_dir() -> Path:
    return default_state_dir() / "templates"


def default_logs_path() -> Path:
    return default_state_dir() / "logforge.log"


def expand_path(path: str | Path) -> Path:
    expanded = os.path.expanduser(os.path.expandvars(str(path)))
    return Path(expanded).resolve(strict=False)


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


def _deep_merge(target: MutableMapping[str, Any], source: Mapping[str, Any]) -> MutableMapping[str, Any]:
    for key, value in source.items():
        if isinstance(value, Mapping) and isinstance(target.get(key), Mapping):
            _deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def _set_nested(data: MutableMapping[str, Any], path: Iterable[str], value: Any) -> None:
    cursor = data
    segments = list(path)
    for segment in segments[:-1]:
        if segment not in cursor or not isinstance(cursor[segment], MutableMapping):
            cursor[segment] = {}
        cursor = cursor[segment]
    cursor[segments[-1]] = value


def _parse_env(env: Mapping[str, str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    prefix = f"{ENV_PREFIX}{ENV_SEPARATOR}"
    for key, raw in env.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix) :].split(ENV_SEPARATOR)
        normalized = [part.lower() for part in parts if part]
        if not normalized:
            continue
        value = _coerce_env_value(raw)
        _set_nested(result, normalized, value)
    return result


class ApiAuthSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    key: Optional[str] = None


class ApiSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8080
    auth: ApiAuthSettings = Field(default_factory=ApiAuthSettings)


class EngineSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_generators: Optional[int] = 10
    thread_pool_size: Optional[int] = None
    log_level: str = "INFO"


class LoggingRotationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_size: str = "50MB"
    backup_count: int = 5


class LoggingSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: str = "INFO"
    file: Path = Field(default_factory=default_logs_path)
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    rotation: LoggingRotationSettings = Field(default_factory=LoggingRotationSettings)


class EntityRegistrySettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: Path = Field(default_factory=default_entities_path)
    auto_save: bool = True
    save_interval: int = 60
    backup_enabled: bool = True
    backup_count: int = 3


class TemplateSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_path: Path = Field(default_factory=default_templates_dir)
    community_api_url: str = "https://api.logforge.io/v1"
    auto_update_check: bool = True
    cache_ttl: int = 3600


class OutputRetrySettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_attempts: int = -1
    retry_interval: int = 5
    backoff_multiplier: float = 2.0
    max_backoff: int = 300


class OutputSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retry: OutputRetrySettings = Field(default_factory=OutputRetrySettings)
    buffer_size: int = 10000
    definitions: list[dict[str, Any]] = Field(default_factory=list)


class GeneratorDefinition(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    template: str
    enabled: bool = True
    frequency: Dict[str, Any] = Field(default_factory=dict)
    outputs: list[str] = Field(default_factory=list)


class LogForgeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "1.0"
    engine: EngineSettings = Field(default_factory=EngineSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    entity_registry: EntityRegistrySettings = Field(default_factory=EntityRegistrySettings)
    templates: TemplateSettings = Field(default_factory=TemplateSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    outputs: OutputSettings = Field(default_factory=OutputSettings)
    generators: list[GeneratorDefinition] = Field(default_factory=list)

    def dict_with_expanded_paths(self) -> Dict[str, Any]:
        data = self.model_dump(mode="python")
        _expand_paths_in_place(data)
        return data


def _expand_paths_in_place(payload: Any) -> None:
    if isinstance(payload, dict):
        for key, value in list(payload.items()):
            if isinstance(value, (dict, list)):
                _expand_paths_in_place(value)
            elif isinstance(value, (str, Path)) and key in {"path", "file", "local_path"}:
                payload[key] = str(expand_path(value))
    elif isinstance(payload, list):
        for index, entry in enumerate(payload):
            if isinstance(entry, (dict, list)):
                _expand_paths_in_place(entry)


def default_config() -> LogForgeConfig:
    return LogForgeConfig()


def load_config(
    config_path: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
    overrides: Optional[Mapping[str, Any]] = None,
) -> LogForgeConfig:
    env = env or os.environ
    if config_path is None:
        env_override = env.get(f"{ENV_PREFIX}_CONFIG") or env.get(f"{ENV_PREFIX}_CONFIG_PATH")
        config_path = expand_path(env_override) if env_override else default_config_path()
    else:
        config_path = expand_path(config_path)

    combined: Dict[str, Any] = default_config().model_dump(mode="python")

    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            file_data = yaml.safe_load(handle) or {}
        if not isinstance(file_data, dict):
            raise ValueError(f"Invalid configuration format: {config_path}")
        _deep_merge(combined, file_data)

    env_overrides = _parse_env(env)
    if env_overrides:
        _deep_merge(combined, env_overrides)

    if overrides:
        _deep_merge(combined, overrides)

    config = LogForgeConfig.model_validate(combined)
    return config


def write_default_config(target: Optional[Path] = None, force: bool = False) -> Path:
    path = expand_path(target or default_config_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"Config already exists at {path}")
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(default_config().model_dump(mode="json"), handle, sort_keys=False)
    return path


def ensure_runtime_paths() -> dict[str, Path]:
    base = default_state_dir()
    templates = default_templates_dir()
    directories = [base, templates / "default", templates / "custom"]
    created: dict[str, Path] = {}
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        created[directory.name] = directory
    return created
