from __future__ import annotations

import json

from typer.testing import CliRunner

from logforge.cli.main import app

runner = CliRunner()


class FakeClient:
    def __init__(self) -> None:
        self.data = {
            "outputs": [
                {
                    "name": "default_file",
                    "type": "file",
                    "status": "healthy",
                    "configuration": {"path": "{generator}.log"},
                    "statistics": {
                        "events_sent": 10,
                        "errors": 0,
                        "buffered_events": 0,
                        "last_error": None,
                    },
                }
            ]
        }

    def get(self, path: str):
        if path == "/api/outputs":
            return self.data
        if path.startswith("/api/outputs/"):
            return self.data["outputs"][0]
        raise AssertionError(path)


def test_outputs_list_json(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr("logforge.cli.outputs._client", lambda ctx: fake)
    result = runner.invoke(app, ["--output", "json", "outputs", "list"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data[0]["name"] == "default_file"


def test_outputs_show(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr("logforge.cli.outputs._client", lambda ctx: fake)
    result = runner.invoke(app, ["outputs", "show", "default_file"])
    assert result.exit_code == 0
    assert "default_file" in result.stdout
