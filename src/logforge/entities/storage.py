"""Entity storage module handling YAML persistence and backups."""

from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from typing import Any, Callable, Optional

import yaml

from logforge.core.home import resolve_logforge_home


class EntityStorage:
    """Handles disk persistence for the entity registry."""

    def __init__(
        self,
        *,
        path: Optional[Path] = None,
        backup_count: int = 3,
        autosave_interval: int = 60,
    ) -> None:
        home = resolve_logforge_home()
        self.path = path or home / "entities.yaml"
        self.backup_count = backup_count
        self.autosave_interval = autosave_interval
        self._autosave_thread: Optional[Thread] = None
        self._autosave_stop = Event()
        self._pending_getter: Optional[Callable[[], dict[str, Any]]] = None

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return yaml.safe_load(self.path.read_text()) or {}

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self._rotate_backups()
        tmp_path = self.path.with_suffix(".tmp")
        tmp_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        tmp_path.replace(self.path)

    def _rotate_backups(self) -> None:
        if self.backup_count <= 0:
            return
        for index in range(self.backup_count, 0, -1):
            src = self.path.with_suffix(f".bak{index - 1}") if index > 1 else self.path
            dst = self.path.with_suffix(f".bak{index}")
            if src.exists():
                src.replace(dst)

    def start_autosave(self, getter: Callable[[], dict[str, Any]]) -> None:
        self._pending_getter = getter
        if self._autosave_thread and self._autosave_thread.is_alive():
            return
        self._autosave_stop.clear()
        self._autosave_thread = Thread(
            target=self._autosave_loop,
            name="entity-autosave",
            daemon=True,
        )
        self._autosave_thread.start()

    def stop_autosave(self) -> None:
        self._autosave_stop.set()
        if self._autosave_thread:
            self._autosave_thread.join(timeout=5)

    def _autosave_loop(self) -> None:
        while not self._autosave_stop.wait(self.autosave_interval):
            if self._pending_getter is None:
                continue
            data = self._pending_getter()
            if data:
                self.save(data)


__all__ = ["EntityStorage"]
