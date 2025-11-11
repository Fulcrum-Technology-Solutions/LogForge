from __future__ import annotations

from pathlib import Path

from logforge.entities.functions import RegistryFunctions
from logforge.entities.registry import EntityRegistry
from logforge.entities.storage import EntityStorage


def _registry(tmp_path: Path) -> EntityRegistry:
    storage = EntityStorage(tmp_path / "entities.yaml", backup_count=0)
    registry = EntityRegistry(storage, auto_save=False)
    registry.import_bundle(
        {
            "organization": {"name": "Acme", "domain": "acme.com"},
            "users": [{"username": "alice", "email": "alice@acme.com"}],
            "devices": [{"hostname": "ws1", "ip_address": "10.0.0.1", "owner": "alice"}],
            "services": [{"name": "api", "url": "https://api.acme.com"}],
        },
        replace=True,
    )
    return registry


def test_registry_functions_lookup(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    functions = RegistryFunctions(registry)

    assert functions.get_random_user()["username"] == "alice"
    assert functions.get_user("alice")["email"] == "alice@acme.com"
    assert functions.get_device("ws1")["owner"] == "alice"
    assert functions.get_random_service()["name"] == "api"
    assert functions.get_organization_field("domain") == "acme.com"
