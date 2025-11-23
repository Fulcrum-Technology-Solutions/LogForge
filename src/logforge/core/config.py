"""Configuration loading utilities."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Mapping, cast

import yaml

from logforge.core.home import resolve_logforge_home

ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")
CONFIG_FILENAME = "config.yaml"

ConfigDict = dict[str, Any]


class ConfigError(RuntimeError):
    """Raised when configuration loading fails."""


def load_config(
    config_path: Path | None = None,
    *,
    logforge_home: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> ConfigDict:
    """Load and process the LogForge configuration file.

    Args:
        config_path: Explicit path to config.yaml. Defaults to LOGFORGE_HOME/config.yaml.
        logforge_home: Root directory for LogForge state. Defaults to ~/.logforge (subject to
            further refinement in the LOGFORGE_HOME resolution task).
        env: Optional environment mapping for substitution (defaults to os.environ).
    """

    home = resolve_logforge_home(override=logforge_home, env=env)
    config_file = _resolve_config_path(config_path, home)

    raw_data = _read_yaml(config_file)
    if raw_data is None:
        raw_data = {}
    if not isinstance(raw_data, dict):
        raise ConfigError("Configuration root must be a mapping.")

    replacements = {"LOGFORGE_HOME": str(home)}
    if env:
        replacements.update(env)
    else:
        replacements.update(os.environ)

    processed = cast(ConfigDict, _walk_and_replace(raw_data, replacements))
    return processed


def _resolve_config_path(config_path: Path | None, home: Path) -> Path:
    candidate = Path(config_path).expanduser() if config_path else home / CONFIG_FILENAME
    candidate = candidate if candidate.is_absolute() else home / candidate
    _ensure_within_home(candidate, home)
    if not candidate.exists():
        raise ConfigError(f"Configuration file not found: {candidate}")
    return candidate


def _ensure_within_home(target: Path, home: Path) -> None:
    try:
        target.resolve().relative_to(home.resolve())
    except ValueError as exc:
        raise ConfigError(
            f"Configuration file must reside under LOGFORGE_HOME ({home}). Got: {target}"
        ) from exc


def _read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed parsing YAML at {path}: {exc}") from exc


def _walk_and_replace(value: Any, replacements: Mapping[str, str]) -> Any:
    if isinstance(value, dict):
        return {k: _walk_and_replace(v, replacements) for k, v in value.items()}
    if isinstance(value, list):
        return [_walk_and_replace(item, replacements) for item in value]
    if isinstance(value, str):
        substituted = _substitute_env_vars(value, replacements)
        return os.path.expanduser(substituted)
    return value


def _substitute_env_vars(template: str, replacements: Mapping[str, str]) -> str:
    def _repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in replacements:
            raise ConfigError(f"Environment variable '{key}' referenced in config but not set.")
        return replacements[key]

    return ENV_VAR_PATTERN.sub(_repl, template)


__all__ = ["ConfigError", "load_config", "CONFIG_FILENAME"]
