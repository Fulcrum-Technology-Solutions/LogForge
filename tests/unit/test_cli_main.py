from typer.testing import CliRunner

from logforge import __version__
from logforge.cli.main import app

runner = CliRunner()


def test_cli_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"LogForge CLI {__version__}" in result.stdout


def test_cli_help_lists_subcommands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "templates" in result.stdout
    assert "generators" in result.stdout
