from __future__ import annotations

import pytest
import yaml

from logforge.core.config import ConfigError, validate_config_dict
from logforge.core.default_config import (
    DefaultConfigOptions,
    build_default_config_dict,
    ensure_default_directories,
    write_default_config,
    write_default_entities,
)


def test_build_default_config_valid(tmp_path) -> None:
    options = DefaultConfigOptions(base_rate=25, api_port=9090)
    config = build_default_config_dict(logforge_home=tmp_path, options=options)
    model = validate_config_dict(config)
    assert model.templates.local_path == str(tmp_path / "templates")
    assert model.api.port == 9090
    assert model.generators[0].frequency.base_rate == 25


def test_write_default_config_creates_file(tmp_path) -> None:
    options = DefaultConfigOptions(organization_name="Acme", organization_domain="acme.com")
    path = write_default_config(logforge_home=tmp_path, options=options)
    assert path.exists()
    loaded = yaml.safe_load(path.read_text())
    validate_config_dict(loaded)
    entities = yaml.safe_load((tmp_path / "entities.yaml").read_text())
    assert entities["organization"]["name"] == "Acme"


def test_write_default_config_prevents_overwrite(tmp_path) -> None:
    write_default_config(logforge_home=tmp_path)
    with pytest.raises(ConfigError):
        write_default_config(logforge_home=tmp_path)


def test_ensure_default_directories(tmp_path) -> None:
    ensure_default_directories(tmp_path)
    assert (tmp_path / "templates" / "default").exists()


def test_write_default_entities_overwrite(tmp_path) -> None:
    options = DefaultConfigOptions(organization_name="New Corp")
    write_default_entities(tmp_path, options, overwrite=True)
    entities = yaml.safe_load((tmp_path / "entities.yaml").read_text())
    assert entities["organization"]["name"] == "New Corp"
