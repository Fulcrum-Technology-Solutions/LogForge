from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

try:
    from typer.testing import CliRunner
except ImportError:  # pragma: no cover
    CliRunner = None

import pytest

if CliRunner is None:
    pytestmark = pytest.mark.skip(reason="typer testing utilities unavailable")
    app = None  # type: ignore
    runner = None
else:
    from logforge.cli.main import app

    pytestmark = []  # type: ignore
    runner = CliRunner()


@patch("logforge.cli.common.requests.get")
@patch("logforge.cli.generators.requests.request")
def test_generators_list(mock_request, mock_health):
    assert runner is not None
    assert app is not None
    mock_response = MagicMock()
    mock_response.json.return_value = {"generators": []}
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_request.return_value = mock_response

    mock_health_response = MagicMock()
    mock_health_response.json.return_value = {"healthy": True}
    mock_health_response.raise_for_status.return_value = None
    mock_health.return_value = mock_health_response

    result = runner.invoke(app, ["--output", "json", "generators", "list"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"generators": []}

