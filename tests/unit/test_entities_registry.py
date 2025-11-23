from __future__ import annotations

from typing import Any

import pytest

from logforge.entities.registry import EntityRegistry
from logforge.entities.storage import EntityStorage
from logforge.entities.validator import EntityValidationError, validate_entities


def sample_data() -> dict[str, Any]:
    return {
        "organization": {"name": "Acme", "domain": "acme.com"},
        "users": [
            {"username": "jsmith", "email": "jsmith@acme.com", "full_name": "John Smith"},
        ],
        "devices": [],
        "services": [],
    }


def test_validate_entities_detects_duplicates() -> None:
    data = sample_data()
    data["users"].append(
        {"username": "jsmith", "email": "john2@acme.com", "full_name": "Dup User"}
    )
    with pytest.raises(EntityValidationError):
        validate_entities(data)


def test_entity_registry_summary(tmp_path) -> None:
    storage = EntityStorage(path=tmp_path / "entities.yaml")
    storage.save(sample_data())
    registry = EntityRegistry(storage=storage, autosave=False)
    summary = registry.summary()
    assert summary["users"] == 1
    assert registry.get_random_user()["username"] == "jsmith"
