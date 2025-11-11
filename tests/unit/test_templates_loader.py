from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from logforge.core.config import TemplateSettings
from logforge.templates.loader import TemplateLoader


def _write_template(base: Path, template_id: str, name: str, version: str, content: str) -> None:
    path = base / template_id
    path.mkdir(parents=True, exist_ok=True)
    (path / "metadata.yaml").write_text(
        yaml.safe_dump({"id": template_id, "name": name, "version": version}), encoding="utf-8"
    )
    (path / "template.j2").write_text(content, encoding="utf-8")


def test_loader_precedence(tmp_path: Path) -> None:
    settings = TemplateSettings(local_path=tmp_path)
    loader = TemplateLoader(settings)

    _write_template(loader.paths.default_dir, "vendor/product/template", "Default Template", "1.0.0", "{{ 1 }}")
    _write_template(loader.paths.custom_dir, "vendor/product/template", "Custom Template", "-", "{{ 2 }}")

    templates = loader.list_templates()
    assert len(templates) == 1
    record = templates[0]
    assert record.location == "custom"
    assert record.overrides is not None

    custom_content = loader.load_template_source("vendor/product/template")
    assert custom_content == "{{ 2 }}"


def test_customize_and_revert(tmp_path: Path) -> None:
    settings = TemplateSettings(local_path=tmp_path)
    loader = TemplateLoader(settings)
    _write_template(loader.paths.default_dir, "vendor/product/simple", "Simple", "1.0.0", "{{ 1 }}")

    target = loader.customize("vendor/product/simple")
    assert target.exists()

    loader.revert("vendor/product/simple")
    assert not target.exists()


def test_missing_template_raises(tmp_path: Path) -> None:
    settings = TemplateSettings(local_path=tmp_path)
    loader = TemplateLoader(settings)
    with pytest.raises(FileNotFoundError):
        loader.get_template("does/not/exist")
