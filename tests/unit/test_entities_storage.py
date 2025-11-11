from __future__ import annotations

from pathlib import Path

from logforge.entities.storage import EntityStorage


def test_entity_storage_backup_rotation(tmp_path: Path) -> None:
    path = tmp_path / "entities.yaml"
    storage = EntityStorage(path, backup_count=2)

    storage.save({"version": 1})
    storage.save({"version": 2})

    backup = path.with_suffix(".1.bak")
    assert backup.exists()

    data = storage.load()
    assert data["version"] == 2
