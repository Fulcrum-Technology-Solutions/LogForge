from __future__ import annotations

from click.testing import CliRunner

from logforge.cli.main import cli


class DummyClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, path, params=None):
        self.calls.append(("GET", path, params))
        return self.responses[path]

    def post(self, path, json_body=None):
        self.calls.append(("POST", path, json_body))
        return self.responses[path]

    def request(self, method, path, params=None):
        self.calls.append((method, path, params))
        return self.responses[path]

    def close(self):
        pass


def test_templates_list_command(monkeypatch):
    runner = CliRunner()

    dummy = DummyClient(
        {
            "/api/templates": [
                {"id": "acme/simple", "name": "Simple", "location": "default", "version": "1.0.0", "overrides": None}
            ]
        }
    )

    def api_client_factory(*args, **kwargs):
        return dummy

    monkeypatch.setattr("logforge.cli.main.APIClient", lambda *a, **k: dummy)

    result = runner.invoke(cli, ["templates", "list"])
    assert result.exit_code == 0
    assert "acme/simple" in result.output


def test_templates_install_command(monkeypatch):
    runner = CliRunner()
    dummy = DummyClient(
        {
            "/api/templates/install": {"id": "acme/simple"},
        }
    )
    monkeypatch.setattr("logforge.cli.main.APIClient", lambda *a, **k: dummy)

    result = runner.invoke(cli, ["templates", "install", "acme/simple"])
    assert result.exit_code == 0
    assert "Installed template acme/simple" in result.output


def test_templates_search_command(monkeypatch):
    runner = CliRunner()
    dummy = DummyClient(
        {
            "/api/templates/search": [
                {"id": "acme/simple", "name": "Simple", "vendor": "acme", "version": "1.0.0"}
            ],
        }
    )
    monkeypatch.setattr("logforge.cli.main.APIClient", lambda *a, **k: dummy)

    result = runner.invoke(cli, ["templates", "search", "simple"])
    assert result.exit_code == 0
    assert "acme/simple" in result.output
