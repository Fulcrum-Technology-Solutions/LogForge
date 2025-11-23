from __future__ import annotations

from pathlib import Path

import yaml

from logforge.templates.loader import TemplateLoader
from logforge.templates.renderer import TemplateRenderer


def create_template(root: Path, metadata: dict, body: str) -> None:
    base = root / "default" / metadata["id"]
    base.mkdir(parents=True, exist_ok=True)
    (base / "metadata.yaml").write_text(yaml.safe_dump(metadata, sort_keys=False))
    (base / "template.j2").write_text(body)


def test_renderer_renders_template(tmp_path) -> None:
    templates_dir = tmp_path / "templates"
    metadata = {
        "id": "vendor/product/system/example",
        "name": "Example",
        "vendor": "vendor",
        "product": "product",
        "data_source": "system",
        "format": "json",
    }
    create_template(
        templates_dir,
        metadata,
        "{{ metadata.name }}-{{ random_int(1, 3) }}",
    )
    loader = TemplateLoader(templates_dir=templates_dir, cache_ttl=1)
    renderer = TemplateRenderer(loader)
    output = renderer.render("vendor/product/system/example")
    assert output.startswith("Example-")
