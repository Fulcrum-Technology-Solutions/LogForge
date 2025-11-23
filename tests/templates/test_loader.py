from __future__ import annotations

import pytest

from logforge.core.config import TemplateConfig
from logforge.templates.loader import TemplateLoader


def _write_template(base: Path, path: str) -> None:
    parts = path.split("/")
    template_dir = base.joinpath(*parts)
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "template.j2").write_text("content", encoding="utf-8")
    (template_dir / "metadata.yaml").write_text(f"id: {'/'.join(parts)}\n", encoding="utf-8")


def test_loader_custom_first(tmp_path):
    local = tmp_path / "templates"
    default = local / "default"
    custom = local / "custom"

    _write_template(default, "vendor/product/source/name")
    (default / "vendor/product/source/name/template.j2").write_text("default", encoding="utf-8")
    _write_template(custom, "vendor/product/source/name")
    (custom / "vendor/product/source/name/template.j2").write_text("custom", encoding="utf-8")

    config = TemplateConfig(
        local_path=local,
        default_path=default,
        custom_path=custom,
        precedence="custom_first",
    )

    loader = TemplateLoader(config)
    resolved = loader.resolve("vendor/product/source/name")
    assert resolved.read_text(encoding="utf-8") == "custom"


def test_loader_default_first(tmp_path):
    local = tmp_path / "templates"
    default = local / "default"
    custom = local / "custom"
    _write_template(default, "vendor/product/source/name")
    (default / "vendor/product/source/name/template.j2").write_text("default", encoding="utf-8")
    _write_template(custom, "vendor/product/source/name")
    (custom / "vendor/product/source/name/template.j2").write_text("custom", encoding="utf-8")

    config = TemplateConfig(
        local_path=local,
        default_path=default,
        custom_path=custom,
        precedence="default_first",
    )

    loader = TemplateLoader(config)
    resolved = loader.resolve("vendor/product/source/name")
    assert resolved.read_text(encoding="utf-8") == "default"


def test_loader_explicit_requires_prefix(tmp_path):
    local = tmp_path / "templates"
    default = local / "default"
    custom = local / "custom"
    _write_template(default, "vendor/product/source/name")
    _write_template(custom, "vendor/product/source/name")

    config = TemplateConfig(
        local_path=local,
        default_path=default,
        custom_path=custom,
        precedence="explicit",
    )
    loader = TemplateLoader(config)

    with pytest.raises(ValueError):
        loader.resolve("vendor/product/source/name")

    resolved = loader.resolve("custom:vendor/product/source/name")
    assert resolved.is_file()

    resolved_default = loader.resolve("default:vendor/product/source/name")
    assert resolved_default.is_file()

