from __future__ import annotations

from pathlib import Path

import yaml

from logforge.core.config import default_config, load_config, write_default_config


def test_default_config_expands_paths() -> None:
    data = default_config().dict_with_expanded_paths()
    assert Path(data["logging"]["file"]).is_absolute()
    assert Path(data["entity_registry"]["path"]).is_absolute()


def test_load_config_merges_file_and_env(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    file_payload = {
        "api": {"port": 9000},
        "engine": {"log_level": "WARNING"},
        "outputs": {"buffer_size": 500},
    }
    config_path.write_text(yaml.safe_dump(file_payload, sort_keys=False), encoding="utf-8")
    env = {
        "LOGFORGE_CONFIG_PATH": str(config_path),
        "LOGFORGE__API__PORT": "8100",
        "LOGFORGE__ENGINE__LOG_LEVEL": "DEBUG",
    }

    config = load_config(env=env)

    assert config.api.port == 8100  # env override beats file
    assert config.engine.log_level == "DEBUG"
    assert config.outputs.buffer_size == 500  # from file


def test_write_default_config_roundtrip(tmp_path) -> None:
    target = tmp_path / "config.yaml"
    write_default_config(target, force=True)

    reloaded = load_config(config_path=target)
    assert reloaded.version == "1.0"
    assert reloaded.logging.file.name == "logforge.log"
