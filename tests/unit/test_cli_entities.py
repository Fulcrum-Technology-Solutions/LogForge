from __future__ import annotations

import json

from typer.testing import CliRunner

from logforge.cli.main import app

runner = CliRunner()


class FakeClient:
    def __init__(self) -> None:
        self.created = None

    def get(self, path: str):
        if path == "/api/entities":
            return {"users": 1, "devices": 0, "services": 0}
        if path.startswith("/api/entities/"):
            return {"type": "users", "count": 1, "entities": [{"username": "jsmith"}]}
        raise AssertionError(path)

    def post(self, path: str, payload: dict):
        self.created = payload
        return payload


def test_entities_list(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr("logforge.cli.entities._client", lambda ctx: fake)
    result = runner.invoke(app, ["entities", "list", "--type", "users"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["count"] == 1


def test_entities_add(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr("logforge.cli.entities._client", lambda ctx: fake)
    payload = '{"username": "mary", "email": "mary@example.com", "full_name": "Mary"}'
    result = runner.invoke(app, ["entities", "add", "users", "--data", payload])
    assert result.exit_code == 0
    assert fake.created["username"] == "mary"
