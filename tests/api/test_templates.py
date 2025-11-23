from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from logforge.api.context import APIContext
from logforge.api.server import create_app
from logforge.community.client import CommunityClient
from logforge.core import config as core_config
from logforge.core.config import LogForgeConfig
from logforge.templates.engine import TemplateEngine
from logforge.templates.loader import TemplateLoader
from logforge.templates.manager import TemplateManager
from logforge.templates.metadata import MetadataLoader
from logforge.templates.renderer import TemplateRenderer


class StubCommunityClient(CommunityClient):
    def __init__(self) -> None:
        super().__init__("https://community.example.com")
        self._package: bytes = b""
        self._results = [
            {"id": "community/vendor/product/template", "vendor": "Community", "product": "Product"}
        ]

    def set_package(self, package: bytes) -> None:
        self._package = package

    def search_templates(self, query=None):
        return self._results

    def download_template(self, template_id: str, url: str | None = None) -> bytes:
        if not self._package:
            raise RuntimeError("No package prepared for download.")
        return self._package


def _create_template_tree(base: Path, template_id: str, version: str = "1.0.0") -> Path:
    parts = template_id.split("/")
    template_dir = base.joinpath(*parts)
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "template.j2").write_text("event={{ generator }}", encoding="utf-8")
    metadata = {
        "id": template_id,
        "name": "Sample Template",
        "vendor": parts[0],
        "product": parts[1],
        "data_source": parts[2],
        "description": "Sample template used for automated tests.",
        "format": "JSON",
        "version": version,
    }
    (template_dir / "metadata.yaml").write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
    return template_dir


def _zip_directory(directory: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in directory.rglob("*"):
            archive.write(item, arcname=item.relative_to(directory.parent))
    return buffer.getvalue()


@pytest.fixture()
def api_client(tmp_path, monkeypatch) -> TestClient:
    home = tmp_path / "opt" / "logforge"
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))
    default_root = home / "templates" / "default"
    custom_root = home / "templates" / "custom"
    local_root = home / "templates"
    sample_id = "vendor/product/datasource/name"
    _create_template_tree(default_root, sample_id)

    config_dict = core_config.default_config_dict()
    config_dict["templates"]["local_path"] = str(local_root)
    config_dict["templates"]["default_path"] = str(default_root)
    config_dict["templates"]["custom_path"] = str(custom_root)
    config_dict["templates"]["precedence"] = "custom_first"
    config_dict["outputs"]["definitions"] = []

    config = LogForgeConfig.parse_obj(config_dict)
    template_loader = TemplateLoader(config.templates)
    metadata_loader = MetadataLoader(config.templates, template_loader)
    renderer = TemplateRenderer(config.templates.local_path)
    template_engine = TemplateEngine(template_loader, metadata_loader, renderer)
    template_manager = TemplateManager(config.templates, template_loader, metadata_loader)
    community_client = StubCommunityClient()

    context = APIContext(
        config=config,
        template_engine=template_engine,
        template_manager=template_manager,
        community_client=community_client,
    )

    app = create_app(context)
    client = TestClient(app)
    client.app.state.context.community_client = community_client  # type: ignore[attr-defined]
    return client


def test_list_templates(api_client: TestClient):
    response = api_client.get("/api/templates")
    assert response.status_code == 200
    data = response.json()
    assert data["templates"][0]["id"] == "vendor/product/datasource/name"


def test_get_template_detail(api_client: TestClient):
    response = api_client.get("/api/templates/vendor/product/datasource/name")
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["name"] == "Sample Template"


def test_template_customization_flow(api_client: TestClient, tmp_path: Path):
    response = api_client.post("/api/templates/vendor/product/datasource/name/customize")
    assert response.status_code == 200
    custom_path = Path(response.json()["path"])
    assert custom_path.exists()

    (custom_path / "template.j2").write_text("event={{ generator }}-custom", encoding="utf-8")

    diff_resp = api_client.get("/api/templates/vendor/product/datasource/name/diff")
    assert diff_resp.status_code == 200
    assert "-event={{ generator }}" in diff_resp.json()["diff"]

    merge_resp = api_client.post("/api/templates/vendor/product/datasource/name/merge")
    assert merge_resp.status_code == 204
    assert "custom" not in (custom_path / "template.j2").read_text(encoding="utf-8")

    revert_resp = api_client.delete("/api/templates/vendor/product/datasource/name/custom")
    assert revert_resp.status_code == 204
    assert not custom_path.exists()


def test_template_install_from_package(api_client: TestClient, tmp_path: Path):
    new_template_id = "vendor/product/datasource/new_template"
    package_dir = tmp_path / "pkg"
    _create_template_tree(package_dir, new_template_id)
    package_bytes = _zip_directory(package_dir / "vendor")
    payload = {
        "template_id": new_template_id,
        "package": base64.b64encode(package_bytes).decode("utf-8"),
    }
    install_resp = api_client.post("/api/templates/install", json=payload)
    assert install_resp.status_code == 204

    detail_resp = api_client.get(f"/api/templates/{new_template_id}")
    assert detail_resp.status_code == 200


def test_template_validate(api_client: TestClient, tmp_path: Path):
    template_dir = tmp_path / "validate"
    _create_template_tree(template_dir, "vendor/product/datasource/validate")
    archive = _zip_directory(template_dir / "vendor")
    payload = {"archive": base64.b64encode(archive).decode("utf-8")}
    response = api_client.post("/api/templates/validate", json=payload)
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_template_search_endpoint(api_client: TestClient):
    response = api_client.get("/api/templates/search")
    assert response.status_code == 200
    data = response.json()
    assert data["templates"][0]["id"] == "community/vendor/product/template"


def test_template_install_community(api_client: TestClient, tmp_path: Path):
    community_client: StubCommunityClient = api_client.app.state.context.community_client  # type: ignore[attr-defined]
    package_dir = tmp_path / "community"
    _create_template_tree(package_dir, "community/vendor/product/template")
    community_client.set_package(_zip_directory(package_dir / "community"))

    response = api_client.post(
        "/api/templates/install",
        json={"template_id": "community/vendor/product/template"},
    )
    assert response.status_code == 204

