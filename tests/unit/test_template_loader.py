from __future__ import annotations

from pathlib import Path

import yaml

from logforge.templates.loader import TemplateLoader


def write_template(root: Path, location: str, rel: str, metadata: dict) -> None:
    base = root / location / rel
    base.mkdir(parents=True, exist_ok=True)
    (base / "metadata.yaml").write_text(yaml.safe_dump(metadata, sort_keys=False))
    (base / "template.j2").write_text("{{ now() }}")


def test_loader_discovers_templates(tmp_path) -> None:
    templates_dir = tmp_path / "templates"
    metadata = {
        "id": "vendor/product/system/example",
        "name": "Example",
        "vendor": "vendor",
        "product": "product",
        "data_source": "system",
        "format": "json",
    }
    write_template(templates_dir, "default", "vendor/product/system/example", metadata)
    loader = TemplateLoader(templates_dir=templates_dir, cache_ttl=1)
    records = loader.list_templates()
    assert len(records) == 1
    assert records[0].metadata.name == "Example"


def test_loader_custom_precedence(tmp_path) -> None:
    templates_dir = tmp_path / "templates"
    base_meta = {
        "id": "vendor/product/system/example",
        "name": "Default",
        "vendor": "vendor",
        "product": "product",
        "data_source": "system",
        "format": "json",
    }
    write_template(templates_dir, "default", "vendor/product/system/example", base_meta)
    custom_meta = base_meta | {"name": "Custom"}
    write_template(templates_dir, "custom", "vendor/product/system/example", custom_meta)
    loader = TemplateLoader(templates_dir=templates_dir, cache_ttl=1)
    record = loader.get_template("vendor/product/system/example")
    assert record is not None
    assert record.location == "custom"
    assert record.metadata.name == "Custom"


def test_loader_cache_refresh(tmp_path) -> None:
    templates_dir = tmp_path / "templates"
    metadata = {
        "id": "vendor/product/system/example",
        "name": "Example",
        "vendor": "vendor",
        "product": "product",
        "data_source": "system",
        "format": "json",
    }
    write_template(templates_dir, "default", "vendor/product/system/example", metadata)
    loader = TemplateLoader(templates_dir=templates_dir, cache_ttl=0)
    (templates_dir / "default" / "vendor/product/system/example/metadata.yaml").write_text(
        yaml.safe_dump(metadata | {"name": "Updated"}, sort_keys=False)
    )
    record = loader.get_template("vendor/product/system/example")
    assert record.metadata.name == "Updated"
