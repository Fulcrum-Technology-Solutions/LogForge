from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from logforge.core.config import TemplateConfig
from logforge.templates.loader import TemplateLoader
from logforge.templates.metadata import MetadataLoader


def _setup_template(tmp_path: Path, template_id: str) -> tuple[TemplateConfig, TemplateLoader]:
    local_path = tmp_path / "templates"
    default_path = local_path / "default"
    custom_path = local_path / "custom"
    default_path.mkdir(parents=True)
    custom_path.mkdir(parents=True)

    parts = template_id.split("/")
    template_dir = default_path.joinpath(*parts)
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "template.j2").write_text("body", encoding="utf-8")

    metadata = {
        "id": template_id,
        "name": "Sample Template",
        "description": "Test template",
        "vendor": parts[0],
        "product": parts[1],
        "data_source": parts[2],
        "format": "json",
    }
    (template_dir / "metadata.yaml").write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")

    config = TemplateConfig(
        local_path=local_path,
        default_path=default_path,
        custom_path=custom_path,
        precedence="default_first",
    )
    loader = TemplateLoader(config)
    return config, loader


def _write_schema(schema_path: Path) -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "vendor": {"type": "string"},
            "product": {"type": "string"},
            "data_source": {"type": "string"},
            "format": {"type": "string"},
        },
        "required": ["id", "name", "vendor", "product", "data_source", "format"],
    }
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(json.dumps(schema), encoding="utf-8")


def test_metadata_loader_validates_schema(tmp_path):
    template_id = "vendor/product/source/name"
    config, loader = _setup_template(tmp_path, template_id)

    schema_path = tmp_path / "schemas" / "template.schema.json"
    _write_schema(schema_path)

    metadata_loader = MetadataLoader(config, loader, schema_path)
    metadata = metadata_loader.load_metadata(template_id)

    assert metadata.id == template_id
    assert metadata.vendor == "vendor"


def test_metadata_loader_rejects_invalid_schema(tmp_path):
    template_id = "vendor/product/source/name"
    config, loader = _setup_template(tmp_path, template_id)

    schema_path = tmp_path / "schemas" / "template.schema.json"
    _write_schema(schema_path)

    metadata_path = loader.metadata(template_id)
    faulty = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    faulty.pop("format")
    metadata_path.write_text(yaml.safe_dump(faulty, sort_keys=False), encoding="utf-8")

    metadata_loader = MetadataLoader(config, loader, schema_path)

    with pytest.raises(ValueError):
        metadata_loader.load_metadata(template_id)

