from __future__ import annotations

import io
import json
import zipfile

from typer.testing import CliRunner

from logforge.cli.main import app

runner = CliRunner()

METADATA_TEXT = "\n".join(
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
    (default_dir / "metadata.yaml").write_text(METADATA_TEXT)
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
    metadata_file = template_dir / "metadata.yaml"
    metadata_file.write_text(METADATA_TEXT)
    (template_dir / "template.j2").write_text("{{ metadata.name }}")
    monkeypatch.setenv("LOGFORGE_HOME", str(home))
    result = runner.invoke(app, ["templates", "validate", "--path", str(metadata_file)])
    assert result.exit_code == 0


def test_templates_diff(monkeypatch, tmp_path):
    home = tmp_path / "home"
    default_dir = home / "templates" / "default" / "vendor" / "product" / "example"
    custom_dir = home / "templates" / "custom" / "vendor" / "product" / "example"
    default_dir.mkdir(parents=True)
    custom_dir.mkdir(parents=True)
    (default_dir / "metadata.yaml").write_text(METADATA_TEXT)
    (custom_dir / "metadata.yaml").write_text(METADATA_TEXT.replace("Example", "Custom Example", 1))
    (default_dir / "template.j2").write_text("hello")
    (custom_dir / "template.j2").write_text("hello world")
    monkeypatch.setenv("LOGFORGE_HOME", str(home))
    result = runner.invoke(app, ["templates", "diff", "vendor/product/example"])
    assert result.exit_code == 0
    assert "--- default/metadata.yaml" in result.stdout
    assert "+hello world" in result.stdout


def test_templates_merge_default_strategy(monkeypatch, tmp_path):
    home = tmp_path / "home"
    default_dir = home / "templates" / "default" / "vendor" / "product" / "example"
    custom_dir = home / "templates" / "custom" / "vendor" / "product" / "example"
    default_dir.mkdir(parents=True)
    custom_dir.mkdir(parents=True)
    (default_dir / "metadata.yaml").write_text(METADATA_TEXT)
    custom_metadata = METADATA_TEXT.replace("Example", "Custom Example", 1)
    (custom_dir / "metadata.yaml").write_text(custom_metadata)
    (default_dir / "template.j2").write_text("hello")
    (custom_dir / "template.j2").write_text("goodbye")
    monkeypatch.setenv("LOGFORGE_HOME", str(home))
    result = runner.invoke(app, ["templates", "merge", "vendor/product/example"])
    assert result.exit_code == 0
    assert (custom_dir / "metadata.yaml").read_text() == METADATA_TEXT
    assert (custom_dir / "template.j2").read_text() == "hello"
    assert (custom_dir / "template.j2.bak").exists()


def test_templates_merge_custom_strategy_keeps_changes(monkeypatch, tmp_path):
    home = tmp_path / "home"
    default_dir = home / "templates" / "default" / "vendor" / "product" / "example"
    custom_dir = home / "templates" / "custom" / "vendor" / "product" / "example"
    default_dir.mkdir(parents=True)
    custom_dir.mkdir(parents=True)
    (default_dir / "metadata.yaml").write_text(METADATA_TEXT)
    custom_metadata = METADATA_TEXT.replace("Example", "Custom Example", 1)
    (custom_dir / "metadata.yaml").write_text(custom_metadata)
    monkeypatch.setenv("LOGFORGE_HOME", str(home))
    result = runner.invoke(
        app,
        ["templates", "merge", "vendor/product/example", "--strategy", "custom"],
    )
    assert result.exit_code == 0
    assert (custom_dir / "metadata.yaml").read_text() == custom_metadata
    assert not (custom_dir / "metadata.yaml.bak").exists()


class DummyCommunityClient:
    def __init__(self, *, results=None, archive: bytes | None = None) -> None:
        self.results = results or []
        self.archive = archive

    def search_templates(self, query: str, limit: int = 20):
        return self.results

    def download_template(self, template_id: str) -> bytes:
        if self.archive is None:
            raise AssertionError("No archive set")
        return self.archive


def _make_archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("metadata.yaml", "id: vendor/product/example\nname: Example\n")
        zf.writestr("template.j2", "{{ metadata.name }}")
    return buffer.getvalue()


def test_templates_search_command(monkeypatch):
    fake = DummyCommunityClient(results=[{"id": "vendor/product/example", "name": "Example"}])
    monkeypatch.setattr("logforge.cli.templates._community_client", lambda *args, **kwargs: fake)
    result = runner.invoke(app, ["--output", "json", "templates", "search", "windows"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data[0]["id"] == "vendor/product/example"


def test_templates_install_command(monkeypatch, tmp_path):
    fake = DummyCommunityClient(archive=_make_archive())
    monkeypatch.setattr("logforge.cli.templates._community_client", lambda *args, **kwargs: fake)
    result = runner.invoke(
        app,
        [
            "templates",
            "install",
            "vendor/product/example",
            "--destination",
            str(tmp_path),
            "--force",
        ],
    )
    assert result.exit_code == 0
    target_dir = tmp_path / "vendor/product/example"
    assert (target_dir / "metadata.yaml").exists()
    assert (target_dir / "template.j2").exists()
