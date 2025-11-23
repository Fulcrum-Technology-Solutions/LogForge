from __future__ import annotations

import pytest
import yaml
from fastapi.testclient import TestClient

from logforge.api.context import APIContext
from logforge.api.server import create_app
from logforge.core import config as core_config
from logforge.core.config import EntityRegistryConfig
from logforge.entities.registry import EntityRegistry


@pytest.fixture()
def context_with_registry(tmp_path, monkeypatch) -> APIContext:
    home = tmp_path / "opt" / "logforge"
    home.mkdir(parents=True)
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))

    entities_path = home / "entities.yaml"
    entities_data = core_config.default_entities_dict(
        organization_name="Acme Corp",
        domain="acme.example.com",
    )
    entities_path.write_text(
        yaml.safe_dump(entities_data, sort_keys=False),
        encoding="utf-8",
    )

    config = core_config.LogForgeConfig.parse_obj(core_config.default_config_dict())
    registry_config = EntityRegistryConfig(
        path=entities_path,
        auto_save=False,
        backup_enabled=False,
        backup_count=1,
        save_interval=60,
    )
    config.entity_registry = registry_config
    registry = EntityRegistry(registry_config)
    return APIContext(config=config, entity_registry=registry)


def test_entities_summary_endpoint(context_with_registry):
    app = create_app(context_with_registry)
    client = TestClient(app)

    response = client.get("/api/entities")

    assert response.status_code == 200
    payload = response.json()
    assert payload["users"] == len(context_with_registry.entity_registry.entities.users)
    assert (
        payload["organization"]["domain"]
        == context_with_registry.entity_registry.entities.organization.domain
    )


def test_entities_detail_endpoint_requires_valid_type(context_with_registry):
    app = create_app(context_with_registry)
    client = TestClient(app)

    response = client.get("/api/entities/users")
    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "users"
    assert payload["count"] == len(context_with_registry.entity_registry.entities.users)

    missing = client.get("/api/entities/unknown")
    assert missing.status_code == 404


def test_entity_crud_flow(context_with_registry):
    app = create_app(context_with_registry)
    client = TestClient(app)

    create_resp = client.post(
        "/api/entities/users",
        json={
            "entity": {
                "username": "newuser",
                "email": "newuser@example.com",
                "full_name": "New User",
                "department": "Engineering",
                "role": "Analyst",
            }
        },
    )
    assert create_resp.status_code == 201

    detail_resp = client.get("/api/entities/users/newuser")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["entity"]["email"] == "newuser@example.com"

    update_resp = client.put(
        "/api/entities/users/newuser",
        json={
            "entity": {
                "username": "newuser",
                "email": "newuser@example.com",
                "full_name": "Updated User",
                "department": "Security",
                "role": "Lead",
            }
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["entity"]["full_name"] == "Updated User"

    delete_resp = client.delete("/api/entities/users/newuser")
    assert delete_resp.status_code == 204
    missing = client.get("/api/entities/users/newuser")
    assert missing.status_code == 404


def test_entity_import_export_validate(context_with_registry):
    app = create_app(context_with_registry)
    client = TestClient(app)

    export_resp = client.get("/api/entities/export")
    assert export_resp.status_code == 200
    content = export_resp.json()["content"]
    assert "organization" in content

    validate_resp = client.post("/api/entities/validate", json={"content": content})
    assert validate_resp.status_code == 200
    assert validate_resp.json()["valid"] is True

    modified = yaml.safe_load(content)
    modified["users"].append(
        {
            "username": "imported",
            "email": "imported@example.com",
            "full_name": "Imported User",
        }
    )
    import_payload = yaml.safe_dump(modified, sort_keys=False)

    import_resp = client.post("/api/entities/import", json={"content": import_payload})
    assert import_resp.status_code == 204
    detail_resp = client.get("/api/entities/users/imported")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["entity"]["username"] == "imported"

