from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Dict, List

import yaml

from logforge.core.config import ConfigError, EntityRegistryConfig, resolve_logforge_home
from logforge.entities.models import EntitiesModel


class EntitiesStorage:
    def __init__(self, config: EntityRegistryConfig) -> None:
        self._config = config
        home = resolve_logforge_home()
        self._path = config.path if config.path.is_absolute() else (home / config.path)
        self._path = self._path.resolve()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> EntitiesModel:
        data = self._read_yaml(self._path)
        return self._validate_data(data, self._path)

    def load_latest_backup(self) -> EntitiesModel:
        for backup in self._list_backups():
            try:
                data = self._read_yaml(backup)
                return self._validate_data(data, backup)
            except ConfigError:
                continue
        raise ConfigError("No valid entity registry backup available.")

    def save(self, entities: EntitiesModel) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists() and self._config.backup_enabled:
            self._rotate_backups()

        payload = entities.model_dump(mode="json", by_alias=True)
        with self._path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False)

    def _read_yaml(self, path: Path) -> Dict[str, object]:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ConfigError(f"Entity registry file not found: {path}") from exc
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ConfigError("Entity registry file must contain a mapping at the top level.")
        return data

    def _validate_data(self, data: Dict[str, object], path: Path) -> EntitiesModel:
        try:
            return EntitiesModel.model_validate(data)
        except Exception as exc:
            raise ConfigError(f"Entity registry validation failed for {path}: {exc}") from exc

    def _list_backups(self) -> List[Path]:
        pattern = f"{self._path.name}.*.bak"
        return sorted(self._path.parent.glob(pattern), reverse=True)

    def _rotate_backups(self) -> None:
        backup_count = self._config.backup_count
        if backup_count <= 0:
            return

        timestamp = time.strftime("%Y%m%d%H%M%S")
        backup_name = f"{self._path.name}.{timestamp}.bak"
        backup_path = self._path.with_name(backup_name)
        shutil.copy2(self._path, backup_path)

        backups = self._list_backups()
        for extra in backups[backup_count:]:
            extra.unlink(missing_ok=True)

