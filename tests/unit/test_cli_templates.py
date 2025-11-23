from __future__ import annotations

import json

from typer.testing import CliRunner

from logforge.cli.main import app

runner = CliRunner()


class FakeClient:
    def get(self, path: str):
        if path == "/api/templates":
            return {
                "templates": [
                    {
                        "id": "vendor/product/example",
                        "name": "Example",
                        "vendor": "vendor",
                        "product": "product",
                        "data_source": "system",
                        "version": "1.0.0",
                        "location": "default",
                    }
                ]
            }
        if path == "/api/templates/vendor/product/example":
            return {
                "summary": {
                    "id": "vendor/product/example",
                    "name": "Example",
                    "vendor": "vendor",
                    "product": "product",
                    "data_source": "system",
                    "version": "1.0.0",
                    "location": "default",
                },
                "metadata": {
                    "id": "vendor/product/example",
                    "name": "Example",
                    "vendor": "vendor",
                    "product": "product",
                    "data_source": "system",
                    "format": "json",
                },
            }
        raise AssertionError(path)


def test_templates_list(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr("logforge.cli.templates._client", lambda ctx: fake)
    result = runner.invoke(app, ["--output", "json", "templates", "list"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["templates"][0]["id"] == "vendor/product/example"


def test_templates_info(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr("logforge.cli.templates._client", lambda ctx: fake)
    result = runner.invoke(app, ["--output", "json", "templates", "info", "vendor/product/example"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["summary"]["id"] == "vendor/product/example"


def test_templates_customize_and_revert(tmp_path, monkeypatch):
    home = tmp_path / "home"
    default_dir = home / "templates" / "default" / "vendor" / "product" / "example"
    default_dir.mkdir(parents=True)
    metadata = "\n".join(
        [
            "id: vendor/product/example",
            "name: Example",
            "vendor: vendor",
            "product: product",
            "data_source: system",
            "format: json",
            "",
        ]
    )
    (default_dir / "metadata.yaml").write_text(metadata)
    (default_dir / "template.j2").write_text("hello")
    monkeypatch.setenv("LOGFORGE_HOME", str(home))

    customize = runner.invoke(app, ["templates", "customize", "vendor/product/example"])
    assert customize.exit_code == 0
    custom_dir = home / "templates" / "custom" / "vendor" / "product" / "example"
    assert custom_dir.exists()

    revert = runner.invoke(app, ["templates", "revert", "vendor/product/example"])
    assert revert.exit_code == 0
    assert not custom_dir.exists()


def test_templates_validate_by_path(tmp_path, monkeypatch):
    home = tmp_path / "home"
    template_dir = home / "templates" / "default" / "vendor" / "product" / "example"
    template_dir.mkdir(parents=True)
    metadata_text = "\n".join(
        [
            "id: vendor/product/example",
            "name: Example",
            "vendor: vendor",
            "product: product",
            "data_source: system",
            "format: json",
            "",
        ]
    )
    metadata_file = template_dir / "metadata.yaml"
    metadata_file.write_text(metadata_text)
    (template_dir / "template.j2").write_text("{{ metadata.name }}")
    monkeypatch.setenv("LOGFORGE_HOME", str(home))
    result = runner.invoke(app, ["templates", "validate", "--path", str(metadata_file)])
    assert result.exit_code == 0
