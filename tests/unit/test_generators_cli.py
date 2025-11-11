from __future__ import annotations

from click.testing import CliRunner

from logforge.cli.main import cli


class DummyClient:
    def __init__(self, responses):
        self.responses = responses

    def get(self, path, params=None):
        return self.responses[path]

    def post(self, path, json_body=None):
        return self.responses[path]

    def request(self, method, path, params=None):
        return self.responses[path]

    def close(self):
        pass


def test_generators_list_command(monkeypatch):
    runner = CliRunner()
    dummy = DummyClient(
        {
            "/api/generators": [
                {"name": "demo", "state": "STOPPED", "template": "acme/simple", "events_generated": 0, "errors": 0}
            ],
        }
    )
    monkeypatch.setattr("logforge.cli.main.APIClient", lambda *a, **k: dummy)

    result = runner.invoke(cli, ["generators", "list"])
    assert result.exit_code == 0
    assert "demo" in result.output


def test_generators_start_command(monkeypatch):
    runner = CliRunner()
    dummy = DummyClient(
        {
            "/api/generators/demo/start": {"name": "demo", "state": "RUNNING"},
        }
    )
    monkeypatch.setattr("logforge.cli.main.APIClient", lambda *a, **k: dummy)

    result = runner.invoke(cli, ["generators", "start", "demo"])
    assert result.exit_code == 0
    assert "Generator demo started" in result.output
