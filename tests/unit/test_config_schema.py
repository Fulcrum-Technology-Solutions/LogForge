from __future__ import annotations

from copy import deepcopy

import pytest

from logforge.core.config import ConfigError, validate_config_dict

BASE_CONFIG = {
    "version": "1.0",
    "engine": {"max_generators": 10, "thread_pool_size": None, "log_level": "INFO"},
    "api": {
        "enabled": True,
        "host": "127.0.0.1",
        "port": 8080,
        "auth": {"enabled": False, "key": None},
    },
    "entity_registry": {
        "path": "/var/lib/logforge/entities.yaml",
        "auto_save": True,
        "save_interval": 60,
        "backup_enabled": True,
        "backup_count": 3,
    },
    "templates": {
        "local_path": "/var/lib/logforge/templates",
        "default_path": "/var/lib/logforge/templates/default",
        "custom_path": "/var/lib/logforge/templates/custom",
        "precedence": "custom_first",
        "community_api_url": "https://api.logforge.io/v1",
        "auto_update_check": True,
        "cache_ttl": 3600,
        "auto_backup_on_customize": True,
        "diff_tool": "auto",
    },
    "logging": {
        "level": "INFO",
        "file": "/var/log/logforge/logforge.log",
        "rotation": {"type": "size", "max_size": "50MB", "backup_count": 5, "compress": True},
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
                "path": "/var/log/logforge/{generator}.log",
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


def test_validate_config_success() -> None:
    config = validate_config_dict(deepcopy(BASE_CONFIG))
    assert config.api.port == 8080
    assert config.outputs.definitions[0].name == "default_file"


def test_validate_rejects_invalid_port() -> None:
    bad = deepcopy(BASE_CONFIG)
    bad["api"]["port"] = 70000
    with pytest.raises(ConfigError):
        validate_config_dict(bad)


def test_validate_requires_generator() -> None:
    bad = deepcopy(BASE_CONFIG)
    bad["generators"] = []
    with pytest.raises(ConfigError):
        validate_config_dict(bad)


def test_validate_output_missing_path() -> None:
    bad = deepcopy(BASE_CONFIG)
    bad["outputs"]["definitions"][0].pop("path")
    with pytest.raises(ConfigError):
        validate_config_dict(bad)


def test_frequency_variation_invalid_day() -> None:
    bad = deepcopy(BASE_CONFIG)
    bad["generators"][0]["frequency"]["variation"] = [{"days": [0], "multiplier": 2.0}]
    with pytest.raises(ConfigError):
        validate_config_dict(bad)
