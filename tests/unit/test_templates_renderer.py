from __future__ import annotations

from pathlib import Path

import yaml

from logforge.core.config import TemplateSettings
from logforge.entities.registry import EntityRegistry
from logforge.entities.storage import EntityStorage
from logforge.templates.loader import TemplateLoader
from logforge.templates.manager import TemplateManager


def _write_template(base: Path, template_id: str, content: str) -> None:
    path = base / template_id
    path.mkdir(parents=True, exist_ok=True)
    (path / "metadata.yaml").write_text(
        yaml.safe_dump({"id": template_id, "name": template_id, "version": "1.0.0"}), encoding="utf-8"
    )
    (path / "template.j2").write_text(content, encoding="utf-8")


def test_template_renderer_renders_with_registry(tmp_path: Path) -> None:
    settings = TemplateSettings(local_path=tmp_path)
    loader = TemplateLoader(settings)
    _write_template(loader.paths.default_dir, "acme/simple", "{{ registry.get_random_user().username }}")

    storage = EntityStorage(tmp_path / "entities.yaml", backup_count=0)
    storage.save(
        {
            "organization": {"name": "Acme", "domain": "acme.com"},
            "users": [{"username": "alice", "email": "alice@acme.com"}],
            "devices": [],
            "services": [],
        }
    )
    registry = EntityRegistry(storage, auto_save=False)
    manager = TemplateManager(config=_build_config(tmp_path), registry=registry)

    output = manager.render("acme/simple")
    assert "alice" in output


def _build_config(tmp_path: Path):
    from logforge.core.config import LogForgeConfig

    config = LogForgeConfig()
    config.templates.local_path = tmp_path
    config.entity_registry.path = tmp_path / "entities.yaml"
    config.entity_registry.auto_save = False
    config.entity_registry.backup_count = 0
    return config
