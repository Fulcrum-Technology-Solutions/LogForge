from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from logforge.cli.main import cli
from logforge.core.config import write_default_config


def _bootstrap_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "config.yaml"
    write_default_config(config_path, force=True)
    return config_path


def test_cli_init_creates_structure(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--path", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "config.yaml").exists()
    assert (tmp_path / "entities.yaml").exists()
    assert (tmp_path / "templates" / "default").exists()
    assert (tmp_path / "templates" / "custom").exists()


def test_cli_config_show_outputs_json(tmp_path: Path) -> None:
    config_path = _bootstrap_config(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["--config", str(config_path), "config", "show", "--output", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["version"] == "1.0"
    assert payload["api"]["host"] == "127.0.0.1"


def test_cli_config_validate(tmp_path: Path) -> None:
    config_path = _bootstrap_config(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["--config", str(config_path), "config", "validate"])

    assert result.exit_code == 0
    assert "Configuration is valid." in result.output


def test_cli_status_json(tmp_path: Path) -> None:
    _bootstrap_config(tmp_path)
    runner = CliRunner()
    fake_response = {"uptime": 1, "version": "1.0.0", "generators": [], "system": {}}

    with patch("logforge.cli.main.APIClient") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.get.return_value = fake_response

        result = runner.invoke(cli, ["status", "--output", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["uptime"] == 1


def test_cli_health_handles_connection_error(tmp_path: Path) -> None:
    _bootstrap_config(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["--api-url", "http://127.0.0.1:65535", "health"])

    assert result.exit_code != 0
    assert "Failed to reach API" in result.output
