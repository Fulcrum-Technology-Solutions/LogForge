from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

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
@patch("logforge.cli.entities.requests.request")
def test_entities_list(mock_request, mock_health):
    assert runner is not None
    assert app is not None

    mock_health_response = MagicMock()
    mock_health_response.json.return_value = {"healthy": True}
    mock_health_response.raise_for_status.return_value = None
    mock_health.return_value = mock_health_response

    mock_response = MagicMock()
    mock_response.json.return_value = {"organization": {"name": "Acme"}, "users": 1, "devices": 0, "services": 0}
    mock_response.raise_for_status.return_value = None
    mock_request.return_value = mock_response

    result = runner.invoke(app, ["--output", "json", "entities", "list"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["organization"]["name"] == "Acme"


@patch("logforge.cli.entities.typer.prompt")
@patch("logforge.cli.common.requests.get")
@patch("logforge.cli.entities.requests.request")
def test_entities_add_user(mock_request, mock_health, mock_prompt):
    assert runner is not None
    assert app is not None

    mock_health_response = MagicMock()
    mock_health_response.json.return_value = {"healthy": True}
    mock_health_response.raise_for_status.return_value = None
    mock_health.return_value = mock_health_response

    responses = iter(
        [
            "newuser",  # username
            "newuser@example.com",  # email
            "New User",  # full name
            "",  # department
            "",  # role
        ]
    )

    def _prompt_side_effect(*args, **kwargs):
        try:
            return next(responses)
        except StopIteration:
            return ""

    mock_prompt.side_effect = _prompt_side_effect

    mock_api_response = MagicMock()
    mock_api_response.json.return_value = {
        "type": "users",
        "entity": {"username": "newuser", "email": "newuser@example.com"},
    }
    mock_api_response.raise_for_status.return_value = None
    mock_request.return_value = mock_api_response

    result = runner.invoke(app, ["--output", "json", "entities", "add", "users"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["entity"]["username"] == "newuser"

