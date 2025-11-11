from __future__ import annotations

import contextlib
import os
import threading
from pathlib import Path
from typing import Dict

import yaml

try:
    import fcntl  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    fcntl = None


class EntityStorage:
    def __init__(self, path: Path, backup_count: int = 3) -> None:
        self.path = path
        self.backup_count = backup_count
        self._thread_lock = threading.RLock()
        self._lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path.touch(exist_ok=True)

    def load(self) -> Dict:
        with self._thread_lock, self._file_lock(shared=True):
            if not self.path.exists():
                return {}
            with self.path.open("r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}

    def save(self, data: Dict) -> None:
        payload = yaml.safe_dump(data, sort_keys=False)
        with self._thread_lock, self._file_lock(shared=False):
            self._rotate_backups()
            temp_path = self.path.with_suffix(".tmp")
            with temp_path.open("w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(temp_path, self.path)

    def _rotate_backups(self) -> None:
        if self.backup_count <= 0 or not self.path.exists():
            return
        for index in range(self.backup_count - 1, 0, -1):
            older = self.path.with_suffix(f".{index}.bak")
            newer = self.path.with_suffix(f".{index + 1}.bak")
            if older.exists():
                os.replace(older, newer)
        first_backup = self.path.with_suffix(".1.bak")
        os.replace(self.path, first_backup)

    @contextlib.contextmanager
    def _file_lock(self, shared: bool):
        if fcntl is None:  # pragma: no cover - non-posix fallback
            yield
            return
        mode = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
        with self._lock_path.open("w", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), mode)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)