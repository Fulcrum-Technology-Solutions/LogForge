"""Default configuration generator for logforge init."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from logforge.core.config import CONFIG_FILENAME, ConfigError, validate_config_dict
from logforge.core.home import resolve_logforge_home


@dataclass
class DefaultConfigOptions:
    organization_name: str = "Example Corporation"
    organization_domain: str = "example.com"
    log_output_dir: Path = field(default_factory=lambda: Path("/var/log/logforge"))
    api_port: int = 8080
    base_rate: int = 10
    install_templates: bool = True


def build_default_config_dict(
    logforge_home: Path | None = None,
    options: DefaultConfigOptions | None = None,
) -> Mapping[str, Any]:
    """Create an in-memory configuration dictionary with sensible defaults."""

    opts = options or DefaultConfigOptions()
    home = resolve_logforge_home(override=logforge_home)
    templates_dir = home / "templates"
    default_templates = templates_dir / "default"
    custom_templates = templates_dir / "custom"
    outputs_dir = opts.log_output_dir
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
            "port": opts.api_port,
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
                "frequency": {"base_rate": opts.base_rate},
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
    options: DefaultConfigOptions | None = None,
) -> Path:
    """Persist default configuration to disk."""

    home = resolve_logforge_home(override=logforge_home)
    dest = destination or home / CONFIG_FILENAME
    dest_parent = dest.parent
    dest_parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not overwrite:
        raise ConfigError(f"Configuration file already exists: {dest}")

    ensure_default_directories(home)

    config_dict = build_default_config_dict(home, options)

    with dest.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config_dict, handle, sort_keys=False)

    write_default_entities(home, options, overwrite=overwrite)

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


def write_default_entities(
    home: Path | None = None,
    options: DefaultConfigOptions | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    """Create a starter entities.yaml file."""

    opts = options or DefaultConfigOptions()
    resolved_home = resolve_logforge_home(override=home)
    path = resolved_home / "entities.yaml"
    if path.exists() and not overwrite:
        return path

    entities = {
        "organization": {
            "name": opts.organization_name,
            "domain": opts.organization_domain,
            "contacts": {
                "admin": f"admin@{opts.organization_domain}",
                "security": f"security@{opts.organization_domain}",
            },
        },
        "users": [],
        "devices": [],
        "services": [],
    }

    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(entities, handle, sort_keys=False)

    return path


__all__ = [
    "DefaultConfigOptions",
    "build_default_config_dict",
    "write_default_config",
    "ensure_default_directories",
    "write_default_entities",
]
