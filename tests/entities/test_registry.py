from __future__ import annotations

import time
import yaml
import pytest

from logforge.core import config as core_config
from logforge.core.config import EntityRegistryConfig
from logforge.entities.registry import EntityRegistry


def write_entities(tmp_path, data):
    path = tmp_path / "entities.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def test_registry_loads_entities(monkeypatch, tmp_path):
    home = tmp_path / "opt" / "logforge"
    home.mkdir(parents=True)
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))

    data = core_config.default_entities_dict(
        organization_name="Acme Corp",
        domain="acme.test",
    )
    path = write_entities(home, data)

    config = EntityRegistryConfig(path=path, auto_save=False, backup_enabled=False, backup_count=1, save_interval=60)
    registry = EntityRegistry(config)

    assert registry.get_organization().name == "Acme Corp"
    random_user = registry.get_random_user()
    assert random_user.username in registry.get_users()
    assert registry.get_device("app-01") is not None
    registry.shutdown()


def test_registry_validates_duplicates(monkeypatch, tmp_path):
    home = tmp_path / "opt" / "logforge"
    home.mkdir(parents=True)
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))

    data = core_config.default_entities_dict()
    data["users"].append(data["users"][0])
    path = write_entities(home, data)

    config = EntityRegistryConfig(path=path, auto_save=False, backup_enabled=False, backup_count=1, save_interval=60)

    with pytest.raises(core_config.ConfigError):
        EntityRegistry(config)


def test_registry_backup_rotation(monkeypatch, tmp_path):
    home = tmp_path / "opt" / "logforge"
    home.mkdir(parents=True)
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))

    data = core_config.default_entities_dict()
    path = write_entities(home, data)

    config = EntityRegistryConfig(path=path, auto_save=False, backup_enabled=True, backup_count=2, save_interval=60)
    registry = EntityRegistry(config)

    registry.entities.users.append(
        registry.entities.users[0].model_copy(update={"username": "newuser", "email": "new@acme.com"})
    )
    registry.save()

    registry.entities.users.append(
        registry.entities.users[0].model_copy(update={"username": "another", "email": "another@acme.com"})
    )
    registry.save()

    backups = list(path.parent.glob("entities.yaml.*.bak"))
    registry.shutdown()
    assert len(backups) <= 2


def test_registry_auto_save_persists_changes(monkeypatch, tmp_path):
    home = tmp_path / "opt" / "logforge"
    home.mkdir(parents=True)
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))

    data = core_config.default_entities_dict()
    path = write_entities(home, data)

    config = EntityRegistryConfig(path=path, auto_save=True, backup_enabled=False, backup_count=1, save_interval=1)
    registry = EntityRegistry(config)

    registry.entities.users.append(
        registry.entities.users[0].model_copy(update={"username": "autosave", "email": "autosave@acme.com"})
    )

    time.sleep(1.5)
    registry.shutdown()

    saved = yaml.safe_load(path.read_text(encoding="utf-8"))
    usernames = {user["username"] for user in saved["users"]}
    assert "autosave" in usernames


def test_registry_recovers_from_corruption(monkeypatch, tmp_path):
    home = tmp_path / "opt" / "logforge"
    home.mkdir(parents=True)
    monkeypatch.setenv(core_config.LOGFORGE_HOME_ENV, str(home))

    data = core_config.default_entities_dict()
    path = write_entities(home, data)

    config = EntityRegistryConfig(path=path, auto_save=False, backup_enabled=True, backup_count=2, save_interval=60)
    registry = EntityRegistry(config)

    registry.save()  # ensure backup exists
    path.write_text("::corrupted::", encoding="utf-8")

    registry.reload()
    registry.shutdown()

    assert registry.get_organization().name == data["organization"]["name"]

