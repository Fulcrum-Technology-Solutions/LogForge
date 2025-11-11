from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from logforge.api.server import create_app
from logforge.core.config import LogForgeConfig


def _write_template(base: Path, template_id: str, content: str) -> None:
    path = base / template_id
    path.mkdir(parents=True, exist_ok=True)
    (path / "metadata.yaml").write_text(
        yaml.safe_dump({"id": template_id, "name": template_id, "version": "1.0.0"}), encoding="utf-8"
    )
    (path / "template.j2").write_text(content, encoding="utf-8")


def _app(tmp_path: Path) -> TestClient:
    config = LogForgeConfig()
    config.templates.local_path = tmp_path / "templates"
    config.entity_registry.path = tmp_path / "entities.yaml"
    config.entity_registry.auto_save = False
    config.entity_registry.backup_count = 0

    (config.entity_registry.path).write_text(
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

    loader_dir = Path(config.templates.local_path)
    _write_template(loader_dir / "default", "acme/simple", "{{ registry.get_random_user().username }}")

    app = create_app(config)
    return TestClient(app)


def test_templates_list_and_validate(tmp_path: Path) -> None:
    client = _app(tmp_path)

    resp = client.get("/api/templates")
    assert resp.status_code == 200
    assert resp.json()[0]["id"] == "acme/simple"

    resp = client.post("/api/templates/acme/simple/validate")
    assert resp.status_code == 200
    assert resp.json()["id"] == "acme/simple"
