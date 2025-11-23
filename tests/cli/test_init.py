from __future__ import annotations

from pathlib import Path

import importlib.util

import pytest
import yaml

try:
    from typer.testing import CliRunner
except ImportError:  # pragma: no cover
    CliRunner = None

if importlib.util.find_spec("typer") is None:  # pragma: no cover
    pytest.skip("typer is required for CLI tests", allow_module_level=True)

from logforge.cli.main import app
from logforge.core import config as core_config


pytestmark = pytest.mark.skipif(CliRunner is None, reason="typer testing utilities unavailable")

runner = CliRunner() if CliRunner else None


def test_init_creates_default_artifacts(monkeypatch, tmp_path):
    home = tmp_path / "logforge-home"
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))

    result = runner.invoke(app, ["init", "--force"])

    assert result.exit_code == 0, result.stdout
    assert (home / "config.yaml").exists()
    assert (home / "entities.yaml").exists()
    assert (home / "templates" / "default").is_dir()
    assert (home / "templates" / "custom").is_dir()


def test_interactive_init_applies_overrides(monkeypatch, tmp_path):
    home = tmp_path / "logforge-home"
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))

    inputs = "\n".join(
        [
            "Acme Corporation",  # organization name
            "acme.test",  # domain
            str(tmp_path / "logs"),  # log directory
            "25",  # event rate
            "9090",  # api port
            "n",  # template install
        ]
    )

    result = runner.invoke(app, ["init", "--force", "--interactive"], input=inputs)

    assert result.exit_code == 0, result.stdout

    config_path = home / "config.yaml"
    entities_path = home / "entities.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    entities = yaml.safe_load(entities_path.read_text(encoding="utf-8"))

    expected_log_path = Path(tmp_path / "logs" / "{generator}.log")
    assert config["outputs"]["definitions"][0]["options"]["path"] == str(expected_log_path)
    assert config["api"]["port"] == 9090
    assert config["generators"][0]["frequency"]["base_rate"] == 25
    assert entities["organization"]["name"] == "Acme Corporation"
    assert entities["organization"]["domain"] == "acme.test"
    assert entities["users"][0]["email"] == "admin@acme.test"

