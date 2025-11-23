from __future__ import annotations

import pytest
import yaml

from logforge.core.config import ConfigError, validate_config_dict
from logforge.core.default_config import (
    build_default_config_dict,
    ensure_default_directories,
    write_default_config,
)


def test_build_default_config_valid(tmp_path) -> None:
    config = build_default_config_dict(logforge_home=tmp_path)
    model = validate_config_dict(config)
    assert model.templates.local_path == str(tmp_path / "templates")


def test_write_default_config_creates_file(tmp_path) -> None:
    path = write_default_config(logforge_home=tmp_path)
    assert path.exists()
    loaded = yaml.safe_load(path.read_text())
    validate_config_dict(loaded)


def test_write_default_config_prevents_overwrite(tmp_path) -> None:
    write_default_config(logforge_home=tmp_path)
    with pytest.raises(ConfigError):
        write_default_config(logforge_home=tmp_path)


def test_ensure_default_directories(tmp_path) -> None:
    ensure_default_directories(tmp_path)
    assert (tmp_path / "templates" / "default").exists()
