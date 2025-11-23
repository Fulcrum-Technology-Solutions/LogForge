"""Default configuration generator for logforge init."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from logforge.core.config import CONFIG_FILENAME, ConfigError, validate_config_dict
from logforge.core.home import resolve_logforge_home


def build_default_config_dict(logforge_home: Path | None = None) -> Mapping[str, Any]:
    """Create an in-memory configuration dictionary with sensible defaults."""

    home = resolve_logforge_home(override=logforge_home)
    templates_dir = home / "templates"
    default_templates = templates_dir / "default"
    custom_templates = templates_dir / "custom"
    outputs_dir = Path("/var/log/logforge")
    entities_path = home / "entities.yaml"

    config = {
        "version": "1.0",
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
        },
        "entity_registry": {
            "path": str(entities_path),
            "auto_save": True,
            "save_interval": 60,
            "backup_enabled": True,
            "backup_count": 3,
        },
        "templates": {
            "local_path": str(templates_dir),
            "default_path": str(default_templates),
            "custom_path": str(custom_templates),
            "precedence": "custom_first",
            "community_api_url": "https://api.logforge.io/v1",
            "auto_update_check": True,
            "cache_ttl": 3600,
            "auto_backup_on_customize": True,
            "diff_tool": "auto",
        },
        "logging": {
            "level": "INFO",
            "file": str(home / "logforge.log"),
            "rotation": {
                "type": "size",
                "max_size": "50MB",
                "backup_count": 5,
                "compress": True,
            },
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "outputs": {
            "buffer_size": 10000,
            "retry": {
                "max_attempts": -1,
                "retry_interval": 5,
                "backoff_multiplier": 2.0,
                "max_backoff": 300,
            },
            "definitions": [
                {
                    "name": "default_file",
                    "type": "file",
                    "path": str(outputs_dir / "{generator}.log"),
                    "rotation": {
                        "type": "size",
                        "max_size": "100MB",
                        "backup_count": 5,
                        "compress": True,
                    },
                },
                {"name": "console_json", "type": "console", "format": "json"},
            ],
        },
        "generators": [
            {
                "name": "windows_security",
                "template": "microsoft/windows/eventlog/security",
                "enabled": True,
                "outputs": ["default_file", "console_json"],
                "frequency": {"base_rate": 10},
            }
        ],
    }

    validate_config_dict(config)
    return config


def write_default_config(
    *,
    logforge_home: Path | None = None,
    destination: Path | None = None,
    overwrite: bool = False,
) -> Path:
    """Persist default configuration to disk."""

    home = resolve_logforge_home(override=logforge_home)
    dest = destination or home / CONFIG_FILENAME
    dest_parent = dest.parent
    dest_parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not overwrite:
        raise ConfigError(f"Configuration file already exists: {dest}")

    ensure_default_directories(home)

    config_dict = build_default_config_dict(home)

    with dest.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config_dict, handle, sort_keys=False)

    return dest


def ensure_default_directories(home: Path | None = None) -> None:
    """Create the directory structure required for a fresh LogForge install."""

    resolved_home = resolve_logforge_home(override=home)
    for path in (
        resolved_home,
        resolved_home / "templates",
        resolved_home / "templates" / "default",
        resolved_home / "templates" / "custom",
    ):
        path.mkdir(parents=True, exist_ok=True)


__all__ = ["build_default_config_dict", "write_default_config", "ensure_default_directories"]
