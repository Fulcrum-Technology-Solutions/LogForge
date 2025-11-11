from unittest.mock import patch

from click.testing import CliRunner

from logforge.cli.main import cli


def test_cli_init_creates_structure(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--path", str(tmp_path)])

    assert result.exit_code == 0, result.output
    config_path = tmp_path / "config.yaml"
    assert config_path.exists()
    assert (tmp_path / "templates" / "default").exists()
    assert (tmp_path / "templates" / "custom").exists()
    assert (tmp_path / "entities.yaml").exists()


def test_cli_config_show_json(tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["init", "--path", str(tmp_path)])
    config_path = tmp_path / "config.yaml"

    result = runner.invoke(
        cli,
        ["--config", str(config_path), "config", "show", "--output", "json"],
    )
    assert result.exit_code == 0, result.output
    assert '"api"' in result.output


def test_cli_status_json(tmp_path):
    runner = CliRunner()
    runner.invoke(cli, ["init", "--path", str(tmp_path)])
    config_path = tmp_path / "config.yaml"

    fake_response = {"uptime": 1, "version": "1.0.0", "generators": [], "system": {}}

    with patch("logforge.cli.main.APIClient") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.json_request.return_value = fake_response

        result = runner.invoke(
            cli,
            ["--config", str(config_path), "status", "--output", "json"],
        )

    assert result.exit_code == 0, result.output
    assert '"uptime": 1' in result.output
