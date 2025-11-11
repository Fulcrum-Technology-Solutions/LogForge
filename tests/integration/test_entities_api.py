from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from logforge.api.server import create_app
from logforge.core.config import LogForgeConfig


def _app(tmp_path: Path) -> TestClient:
    config = LogForgeConfig()
    config.entity_registry.path = tmp_path / "entities.yaml"
    config.entity_registry.auto_save = False
    config.entity_registry.backup_count = 0
    app = create_app(config)
    return TestClient(app)


def test_entities_crud(tmp_path: Path) -> None:
    client = _app(tmp_path)

    resp = client.get("/api/entities")
    assert resp.status_code == 200

    payload = {"username": "alice", "email": "alice@acme.com"}
    resp = client.post("/api/entities/users", json=payload)
    assert resp.status_code == 201

    resp = client.get("/api/entities/users/alice")
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@acme.com"

    resp = client.put("/api/entities/users/alice", json={"username": "alice", "email": "new@acme.com"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "new@acme.com"

    resp = client.delete("/api/entities/users/alice")
    assert resp.status_code == 204


def test_entities_import_export(tmp_path: Path) -> None:
    client = _app(tmp_path)
    bundle = {
        "organization": {"name": "Acme", "domain": "acme.com"},
        "users": [{"username": "alice", "email": "alice@acme.com"}],
        "devices": [],
        "services": [],
    }
    resp = client.post("/api/entities/import", json=bundle)
    assert resp.status_code == 200

    resp = client.get("/api/entities/export")
    assert resp.status_code == 200
    data = resp.json()
    assert data["users"][0]["username"] == "alice"
