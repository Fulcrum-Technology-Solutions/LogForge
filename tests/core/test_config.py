from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from logforge.core import config as core_config


def test_resolve_logforge_home_uses_env(monkeypatch, tmp_path):
    desired_home = tmp_path / "logforge-home"
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(desired_home))

    result = core_config.resolve_logforge_home()

    assert result == desired_home


def test_resolve_logforge_home_rejects_relative(monkeypatch):
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, "relative/path")

    with pytest.raises(core_config.ConfigError):
        core_config.resolve_logforge_home()


def test_load_config_resolves_paths_inside_home(monkeypatch, tmp_path):
    home = tmp_path / "opt" / "logforge"
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))

    home.mkdir(parents=True, exist_ok=True)
    config_path = core_config.write_default_config()

    loaded = core_config.load_config(config_path)

    assert loaded.entity_registry.path == (home / "entities.yaml")
    assert loaded.templates.local_path == (home / "templates")
    assert loaded.templates.default_path == (home / "templates" / "default")
    assert loaded.templates.custom_path == (home / "templates" / "custom")
    assert loaded.logging.file == (home / "logforge.log")
    assert loaded.generators[0].frequency.base_rate == 10


def test_load_config_rejects_paths_outside_home(monkeypatch, tmp_path):
    home = tmp_path / "opt" / "logforge"
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))
    home.mkdir(parents=True, exist_ok=True)

    config_data = core_config.default_config_dict()
    config_data["entity_registry"]["path"] = "/tmp/external/entities.yaml"

    config_file = home / "config.yaml"
    config_file.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")

    with pytest.raises(core_config.ConfigError):
        core_config.load_config(config_file)


def test_write_default_config_with_overrides(monkeypatch, tmp_path):
    home = tmp_path / "opt" / "logforge"
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))
    home.mkdir(parents=True, exist_ok=True)

    log_dir = tmp_path / "logs"
    config_data = core_config.default_config_dict(
        log_output_dir=log_dir,
        default_event_rate=42,
        api_port=9090,
    )
    path = core_config.write_default_config(config_data=config_data)

    loaded = core_config.load_config(path)
    assert loaded.api.port == 9090
    assert loaded.generators[0].frequency.base_rate == 42
    assert loaded.outputs.definitions[0].options["path"] == str(log_dir / "{generator}.log")


def test_write_default_entities_respects_existing(monkeypatch, tmp_path):
    home = tmp_path / "opt" / "logforge"
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))
    home.mkdir(parents=True, exist_ok=True)

    destination = core_config.write_default_entities()
    assert destination == home / "entities.yaml"
    assert destination.exists()

    with pytest.raises(core_config.ConfigError):
        core_config.write_default_entities()


def test_default_entities_dict_customization(monkeypatch, tmp_path):
    home = tmp_path / "opt" / "logforge"
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))
    home.mkdir(parents=True, exist_ok=True)

    destination = core_config.write_default_entities(
        organization_name="Acme Corp",
        domain="acme.test",
    )
    data = yaml.safe_load(destination.read_text(encoding="utf-8"))
    assert data["organization"]["name"] == "Acme Corp"
    assert data["organization"]["domain"] == "acme.test"
    assert data["organization"]["contacts"]["admin"] == "admin@acme.test"
    assert data["users"][0]["email"] == "admin@acme.test"
