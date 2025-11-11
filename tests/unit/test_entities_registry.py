from __future__ import annotations

from pathlib import Path

import pytest

from logforge.core.config import LogForgeConfig
from logforge.entities.registry import EntityRegistry
from logforge.entities.storage import EntityStorage


def _create_registry(tmp_path: Path) -> EntityRegistry:
    storage = EntityStorage(tmp_path / "entities.yaml", backup_count=1)
    registry = EntityRegistry(storage)
    return registry


def test_add_and_get_user(tmp_path: Path) -> None:
    registry = _create_registry(tmp_path)
    registry.add_entity("users", {"username": "alice", "email": "alice@acme.com"})

    user = registry.get_entity("users", "alice")
    assert user["email"] == "alice@acme.com"


def test_update_device(tmp_path: Path) -> None:
    registry = _create_registry(tmp_path)
    registry.add_entity("devices", {"hostname": "ws1", "ip_address": "10.0.0.1"})
    updated = registry.update_entity("devices", "ws1", {"hostname": "ws1", "ip_address": "10.0.0.2"})

    assert updated["ip_address"] == "10.0.0.2"


def test_delete_service(tmp_path: Path) -> None:
    registry = _create_registry(tmp_path)
    registry.add_entity("services", {"name": "api", "url": "https://api.acme.com"})
    registry.delete_entity("services", "api")

    assert registry.get_entity("services", "api") is None


def test_import_bundle_replace(tmp_path: Path) -> None:
    registry = _create_registry(tmp_path)
    registry.add_entity("users", {"username": "old", "email": "old@acme.com"})
    bundle = {
        "organization": {"name": "Acme", "domain": "acme.com"},
        "users": [{"username": "new", "email": "new@acme.com"}],
        "devices": [],
        "services": [],
    }

    registry.import_bundle(bundle, replace=True)
    assert registry.get_entity("users", "old") is None
    assert registry.get_entity("users", "new")["email"] == "new@acme.com"
