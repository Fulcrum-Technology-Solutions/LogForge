from __future__ import annotations

import io
import zipfile

import pytest

from logforge.templates.loader import TemplateLoader
from logforge.templates.updater import TemplateUpdateChecker, TemplateUpdateError


def _write_template(root, location: str = "default", version: str = "1.0.0") -> None:
    template_dir = root / location / "vendor" / "product" / "example"
    template_dir.mkdir(parents=True)
    metadata = "\n".join(
        [
            "id: vendor/product/example",
            "name: Example",
            "vendor: vendor",
            "product: product",
            "data_source: system",
            "format: json",
            f"version: {version}",
            "",
        ]
    )
    (template_dir / "metadata.yaml").write_text(metadata)
    (template_dir / "template.j2").write_text("{{ metadata.name }}")


def _make_archive(metadata_text: str, template_body: str = "{{ metadata.name }}") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("metadata.yaml", metadata_text)
        zf.writestr("template.j2", template_body)
    return buffer.getvalue()


class StubCommunityClient:
    def __init__(self, *, version: str = "1.1.0", archive: bytes | None = None) -> None:
        self.version = version
        self._archive = archive

    def get_template_details(self, template_id: str) -> dict:
        return {"metadata": {"id": template_id, "version": self.version}}

    def download_template(self, template_id: str) -> bytes:
        if self._archive is None:
            raise AssertionError("Archive not configured for download operation.")
        return self._archive


def test_update_checker_detects_newer_version(tmp_path):
    templates_root = tmp_path / "templates"
    _write_template(templates_root, "default", version="1.0.0")
    loader = TemplateLoader(templates_dir=templates_root)
    checker = TemplateUpdateChecker(
        loader=loader,
        client=StubCommunityClient(version="1.2.0"),
    )
    updates = checker.check_updates()
    assert len(updates) == 1
    assert updates[0].latest_version == "1.2.0"


def test_update_checker_apply_update_writes_new_files(tmp_path):
    templates_root = tmp_path / "templates"
    _write_template(templates_root, "default", version="1.0.0")
    loader = TemplateLoader(templates_dir=templates_root)
    metadata_v2 = "\n".join(
        [
            "id: vendor/product/example",
            "name: Example",
            "vendor: vendor",
            "product: product",
            "data_source: system",
            "format: json",
            "version: 2.0.0",
            "",
        ]
    )
    archive = _make_archive(metadata_v2, "{{ metadata.name }} v2")
    checker = TemplateUpdateChecker(
        loader=loader,
        client=StubCommunityClient(version="2.0.0", archive=archive),
    )
    candidate = checker.check_updates()[0]
    installed_path = checker.apply_update(candidate)
    metadata = (installed_path / "metadata.yaml").read_text()
    template_body = (installed_path / "template.j2").read_text()
    assert "version: 2.0.0" in metadata
    assert template_body == "{{ metadata.name }} v2"


def test_update_checker_rejects_custom_templates(tmp_path):
    templates_root = tmp_path / "templates"
    _write_template(templates_root, "custom", version="1.0.0")
    loader = TemplateLoader(templates_dir=templates_root)
    checker = TemplateUpdateChecker(loader=loader, client=StubCommunityClient())
    with pytest.raises(TemplateUpdateError):
        checker.check_updates(template_ids=["vendor/product/example"])

