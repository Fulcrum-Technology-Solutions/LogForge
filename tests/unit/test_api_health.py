from fastapi.testclient import TestClient

from logforge.api.server import create_app
from logforge.core.config import ConfigManager


def _get_config(tmp_path):
    manager = ConfigManager(config_path=tmp_path / "config.yaml")
    return manager.load()


def test_health_endpoint(tmp_path):
    config = _get_config(tmp_path)
    app = create_app(config)
    client = TestClient(app)

    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "generators" in body


def test_status_endpoint(tmp_path):
    config = _get_config(tmp_path)
    app = create_app(config)
    client = TestClient(app)

    response = client.get("/api/status")
    assert response.status_code == 200
    body = response.json()
    assert "uptime" in body
    assert "system" in body


def test_status_requires_api_key(tmp_path):
    config_path = tmp_path / "config.yaml"
    manager = ConfigManager(config_path=config_path)
    manager.save_default(
        overwrite=True,
        overrides={"api": {"auth": {"enabled": True, "key": "secret-key"}}},
    )
    config = manager.load()
    app = create_app(config)
    client = TestClient(app)

    unauthorized = client.get("/api/status")
    assert unauthorized.status_code == 401

    authorized = client.get("/api/status", headers={"Authorization": "Bearer secret-key"})
    assert authorized.status_code == 200
