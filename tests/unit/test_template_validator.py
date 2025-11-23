from __future__ import annotations

import pytest

from logforge.templates.loader import TemplateLoader
from logforge.templates.validator import TemplateValidationError, TemplateValidator


def create_template(templates_dir, template_id: str, body: str = "{{ metadata.name }}"):
    path = templates_dir / "default" / template_id
    path.mkdir(parents=True, exist_ok=True)
    metadata_text = "\n".join(
        [
            f"id: {template_id}",
            "name: Example",
            "vendor: vendor",
            "product: product",
            "data_source: system",
            "format: json",
            "",
        ]
    )
    (path / "metadata.yaml").write_text(metadata_text)
    (path / "template.j2").write_text(body)
    return path


def test_validator_accepts_valid_template(tmp_path):
    templates_dir = tmp_path / "templates"
    create_template(templates_dir, "vendor/product/example")
    loader = TemplateLoader(templates_dir=templates_dir, cache_ttl=1)
    validator = TemplateValidator(loader)
    result = validator.validate("vendor/product/example")
    assert result.template_id == "vendor/product/example"


def test_validator_detects_missing_template(tmp_path):
    templates_dir = tmp_path / "templates"
    path = create_template(templates_dir, "vendor/product/example")
    (path / "template.j2").unlink()
    loader = TemplateLoader(templates_dir=templates_dir, cache_ttl=1)
    validator = TemplateValidator(loader)
    with pytest.raises(TemplateValidationError):
        validator.validate("vendor/product/example")


def test_validator_blocks_unsafe_constructs(tmp_path):
    templates_dir = tmp_path / "templates"
    create_template(templates_dir, "vendor/product/example", "{{ __import__('os').system('ls') }}")
    loader = TemplateLoader(templates_dir=templates_dir, cache_ttl=1)
    validator = TemplateValidator(loader)
    with pytest.raises(TemplateValidationError) as exc:
        validator.validate("vendor/product/example")
    assert "unsafe" in str(exc.value).lower()
