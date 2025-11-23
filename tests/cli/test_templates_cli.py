from __future__ import annotations

import base64
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
@patch("logforge.cli.templates.requests.get")
def test_templates_list(mock_templates_get, mock_health_get):
    assert runner is not None
    assert app is not None

    mock_health_response = MagicMock()
    mock_health_response.json.return_value = {"healthy": True}
    mock_health_response.raise_for_status.return_value = None
    mock_health_get.return_value = mock_health_response

    mock_templates_response = MagicMock()
    mock_templates_response.json.return_value = {
        "templates": [
            {
                "id": "vendor/product/ds/name",
                "locations": ["default"],
                "version": "1.0.0",
                "format": "json",
            }
        ]
    }
    mock_templates_response.raise_for_status.return_value = None
    mock_templates_get.return_value = mock_templates_response

    result = runner.invoke(app, ["--output", "json", "templates", "list"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["templates"][0]["id"] == "vendor/product/ds/name"


@patch("logforge.cli.common.requests.get")
@patch("logforge.cli.templates.requests.request")
def test_templates_search(mock_request, mock_health):
    assert runner is not None
    assert app is not None

    mock_health_response = MagicMock()
    mock_health_response.json.return_value = {"healthy": True}
    mock_health_response.raise_for_status.return_value = None
    mock_health.return_value = mock_health_response

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "templates": [{"id": "community/vendor/product/template"}],
    }
    mock_response.raise_for_status.return_value = None
    mock_request.return_value = mock_response

    result = runner.invoke(app, ["--output", "json", "templates", "search", "vendor"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["templates"][0]["id"] == "community/vendor/product/template"


@patch("logforge.cli.common.requests.get")
@patch("logforge.cli.templates.requests.request")
def test_templates_install_with_file(mock_request, mock_health, tmp_path):
    assert runner is not None
    assert app is not None

    package_path = tmp_path / "package.zip"
    package_path.write_bytes(b"package-bytes")

    mock_health_response = MagicMock()
    mock_health_response.json.return_value = {"healthy": True}
    mock_health_response.raise_for_status.return_value = None
    mock_health.return_value = mock_health_response

    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {"locations": []}
    mock_get_response.raise_for_status.return_value = None

    mock_post_response = MagicMock()
    mock_post_response.status_code = 204
    mock_post_response.content = b""
    mock_post_response.raise_for_status.return_value = None
    mock_request.side_effect = [mock_get_response, mock_post_response]

    result = runner.invoke(app, ["templates", "install", "template-id", "--file", str(package_path)])
    assert result.exit_code == 0

    post_call = mock_request.call_args_list[-1]
    payload = post_call.kwargs["json"]
    assert payload["template_id"] == "template-id"
    assert base64.b64decode(payload["package"]) == b"package-bytes"


@patch("logforge.cli.templates._zip_directory", return_value=b"zip-bytes")
@patch("logforge.cli.common.requests.get")
@patch("logforge.cli.templates.requests.request")
def test_templates_validate(mock_request, mock_health, mock_zip, tmp_path):
    assert runner is not None
    assert app is not None

    template_dir = tmp_path / "template"
    template_dir.mkdir()

    mock_health_response = MagicMock()
    mock_health_response.json.return_value = {"healthy": True}
    mock_health_response.raise_for_status.return_value = None
    mock_health.return_value = mock_health_response

    mock_api_response = MagicMock()
    mock_api_response.json.return_value = {"valid": True}
    mock_api_response.raise_for_status.return_value = None
    mock_request.return_value = mock_api_response

    result = runner.invoke(app, ["--output", "json", "templates", "validate", str(template_dir)])
    assert result.exit_code == 0

    _, kwargs = mock_request.call_args
    payload = kwargs["json"]
    assert base64.b64decode(payload["archive"]) == b"zip-bytes"

