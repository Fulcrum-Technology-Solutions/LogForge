from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from logforge.api.server import create_app
from logforge.core.config import LogForgeConfig, GeneratorDefinition


def _configure(tmp_path: Path) -> LogForgeConfig:
    config = LogForgeConfig()
    config.templates.local_path = tmp_path / "templates"
    config.entity_registry.path = tmp_path / "entities.yaml"
    config.entity_registry.auto_save = False
    config.entity_registry.backup_count = 0
    config.generators = [
        GeneratorDefinition(
            name="demo",
            template="acme/simple",
            outputs=[],
            frequency={"base_rate": 1},
        )
    ]
    return config


def _write_entities(config: LogForgeConfig) -> None:
    config.entity_registry.path.write_text(
        yaml.safe_dump(
            {
                "organization": {"name": "Acme", "domain": "acme.com"},
                "users": [{"username": "alice", "email": "alice@acme.com"}],
                "devices": [],
                "services": [],
            }
        ),
        encoding="utf-8",
    )


def _write_template(config: LogForgeConfig) -> None:
    template_dir = config.templates.local_path / "default" / "acme/simple"
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "metadata.yaml").write_text(
        yaml.safe_dump({"id": "acme/simple", "name": "Simple"}), encoding="utf-8"
    )
    (template_dir / "template.j2").write_text("{{ registry.get_random_user().username }}", encoding="utf-8")


def _client(tmp_path: Path) -> TestClient:
    config = _configure(tmp_path)
    config.templates.local_path.mkdir(parents=True, exist_ok=True)
    _write_entities(config)
    _write_template(config)
    app = create_app(config)
    return TestClient(app)


def test_generators_start_stop(tmp_path: Path) -> None:
    client = _client(tmp_path)

    resp = client.get("/api/generators")
    assert resp.status_code == 200

    resp = client.post("/api/generators/demo/start")
    assert resp.status_code == 200

    resp = client.post("/api/generators/demo/stop")
    assert resp.status_code == 200
