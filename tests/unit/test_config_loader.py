from __future__ import annotations

import os
from pathlib import Path

import pytest

from logforge.core.config import ConfigError, load_config


def write_config(tmp_path: Path, content: str) -> Path:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(content)
    return cfg_path


def test_load_config_substitutes_env_vars(tmp_path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    config_file = write_config(
        home,
        """
api:
  host: ${API_HOST}
logging:
  file: ${LOGFORGE_HOME}/logforge.log
""",
    )

    monkeypatch.setenv("API_HOST", "0.0.0.0")

    config = load_config(config_file, logforge_home=home)

    assert config["api"]["host"] == "0.0.0.0"
    assert config["logging"]["file"] == f"{home}/logforge.log"


def test_load_config_expands_user_paths(tmp_path, monkeypatch) -> None:
    home = tmp_path / "lf"
    home.mkdir()
    config_file = write_config(
        home,
        """
logging:
  file: "~/logs/logforge.log"
""",
    )

    monkeypatch.setenv("HOME", str(tmp_path / "custom_home"))

    config = load_config(config_file, logforge_home=home)
    expected_path = os.path.expanduser("~/logs/logforge.log")
    assert config["logging"]["file"] == expected_path


def test_load_config_rejects_paths_outside_home(tmp_path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    cfg = write_config(outside, "engine: {}\n")

    with pytest.raises(ConfigError):
        load_config(cfg, logforge_home=home)


def test_missing_environment_variable_raises(tmp_path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    cfg = write_config(home, "api:\n  host: ${MISSING_ENV}\n")

    with pytest.raises(ConfigError):
        load_config(cfg, logforge_home=home)
