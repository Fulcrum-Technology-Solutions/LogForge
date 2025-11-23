from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from logforge.cli.main import app

runner = CliRunner()


def initialize(tmp_path: Path) -> None:
    runner.invoke(app, ["init", "--overwrite", "--home", str(tmp_path)])


def test_config_show(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOGFORGE_HOME", str(tmp_path))
    initialize(tmp_path)
    result = runner.invoke(app, ["config", "show", "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["api"]["port"] == 8080


def test_config_validate(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOGFORGE_HOME", str(tmp_path))
    initialize(tmp_path)
    result = runner.invoke(app, ["config", "validate"])
    assert result.exit_code == 0


def test_config_set_updates_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOGFORGE_HOME", str(tmp_path))
    initialize(tmp_path)
    result = runner.invoke(app, ["config", "set", "api.port", "9091"])
    assert result.exit_code == 0
    config_path = tmp_path / "config.yaml"
    assert config_path.exists()
    import yaml

    data = yaml.safe_load(config_path.read_text())
    assert data["api"]["port"] == 9091
