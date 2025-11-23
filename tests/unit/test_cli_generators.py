from __future__ import annotations

import json

from typer.testing import CliRunner

from logforge.cli.main import app

runner = CliRunner()


class FakeClient:
    def __init__(self) -> None:
        self.last_post = None

    def get(self, path: str):
        if path == "/api/generators":
            return [
                {
                    "name": "alpha",
                    "state": "RUNNING",
                    "template": "vendor/product/example",
                    "outputs": ["default"],
                    "statistics": {
                        "events_generated": 10,
                        "errors": 0,
                        "uptime": 5,
                        "last_event": None,
                    },
                    "frequency": {"base_rate": 5},
                }
            ]
        if path.startswith("/api/generators/"):
            return {
                "name": path.split("/")[-1],
                "state": "RUNNING",
                "template": "vendor/product/example",
                "outputs": ["default"],
                "statistics": {
                    "events_generated": 10,
                    "errors": 0,
                    "uptime": 5,
                    "last_event": None,
                },
                "frequency": {"base_rate": 5},
            }
        raise AssertionError(path)

    def post(self, path: str, payload: dict):
        self.last_post = (path, payload)
        return self.get(f"/api/generators/{path.split('/')[-2]}")


def test_generators_list_json(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr("logforge.cli.generators._client", lambda ctx: fake)
    result = runner.invoke(app, ["--output", "json", "generators", "list"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data[0]["name"] == "alpha"


def test_generators_start(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr("logforge.cli.generators._client", lambda ctx: fake)
    result = runner.invoke(app, ["generators", "start", "alpha"])
    assert result.exit_code == 0
    assert fake.last_post[0].endswith("/alpha/start")
