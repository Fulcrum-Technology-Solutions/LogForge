from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
import yaml

from logforge.core import config as core_config
from logforge.core.config import LogForgeConfig
from logforge.core.engine import GenerationEngine
from logforge.entities.registry import EntityRegistry
from logforge.outputs.factory import OutputFactory
from logforge.templates.engine import TemplateEngine
from logforge.templates.loader import TemplateLoader
from logforge.templates.metadata import MetadataLoader
from logforge.templates.renderer import TemplateRenderer
from logforge.entities.functions import RegistryFunctions
from logforge.utils.metrics import MetricsRegistry


def _create_template(home: Path, template_id: str) -> None:
    parts = template_id.split("/")
    template_dir = home / "templates" / "default" / Path(*parts)
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "template.j2").write_text('{"event": "static"}', encoding="utf-8")
    metadata = {
        "id": template_id,
        "name": "Static Template",
        "vendor": parts[0],
        "product": parts[1],
        "data_source": parts[2],
        "description": "Static event for end-to-end test.",
        "format": "JSON",
        "version": "1.0.0",
    }
    (template_dir / "metadata.yaml").write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")


@pytest.mark.asyncio
async def test_end_to_end_generation(tmp_path, monkeypatch):
    home = tmp_path / "opt" / "logforge"
    home.mkdir(parents=True)
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))

    template_id = "vendor/product/datasource/name"
    _create_template(home, template_id)

    entities_dict = core_config.default_entities_dict(
        organization_name="Acme Corp",
        domain="acme.example.com",
    )
    entities_path = home / "entities.yaml"
    entities_path.write_text(yaml.safe_dump(entities_dict, sort_keys=False), encoding="utf-8")

    config_dict = core_config.default_config_dict()
    config_dict["templates"]["local_path"] = str(home / "templates")
    config_dict["templates"]["default_path"] = str(home / "templates" / "default")
    config_dict["templates"]["custom_path"] = str(home / "templates" / "custom")
    config_dict["outputs"]["definitions"] = [
        {
            "name": "file_output",
            "type": "file",
            "options": {
                "path": str(home / "outputs" / "{generator}.log"),
            },
        }
    ]
    config_dict["generators"] = [
        {
            "name": "testgen",
            "template": template_id,
            "enabled": True,
            "frequency": {"base_rate": 5, "variation": []},
            "outputs": ["file_output"],
        }
    ]

    config = LogForgeConfig.parse_obj(config_dict)
    registry_config = config.entity_registry
    registry = EntityRegistry(registry_config)

    template_loader = TemplateLoader(config.templates)
    metadata_loader = MetadataLoader(config.templates, template_loader)
    renderer = TemplateRenderer(config.templates.local_path, RegistryFunctions(registry))
    template_engine = TemplateEngine(template_loader, metadata_loader, renderer)

    metrics = MetricsRegistry()
    outputs = OutputFactory(config.outputs).create_all(metrics)

    engine = GenerationEngine(template_engine, metrics=metrics, outputs=outputs)
    await engine.register_generator(config.generators[0])
    await engine.start_generator("testgen")
    await asyncio.sleep(1.0)
    await engine.stop_generator("testgen")

    output_file = home / "outputs" / "testgen.log"
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8").strip()
    assert "static" in content

