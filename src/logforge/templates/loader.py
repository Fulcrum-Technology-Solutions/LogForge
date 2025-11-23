"""Filesystem template loader with precedence rules."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from logforge.core.home import resolve_logforge_home
from logforge.templates.models import TemplateMetadata


@dataclass
class TemplateRecord:
    template_id: str
    metadata: TemplateMetadata
    template_path: Path
    metadata_path: Path
    location: str  # "default" or "custom"
    relative_dir: Path


class TemplateLoader:
    """Loads template metadata from default/custom directories with precedence rules."""

    def __init__(
        self,
        *,
        templates_dir: Optional[Path] = None,
        precedence: str = "custom_first",
        cache_ttl: int = 3600,
    ) -> None:
        self.home = resolve_logforge_home()
        self.templates_dir = templates_dir or self.home / "templates"
        self.default_dir = self.templates_dir / "default"
        self.custom_dir = self.templates_dir / "custom"
        self.precedence = precedence
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, TemplateRecord] = {}
        self._last_scan = 0.0
        self.refresh()

    def refresh(self) -> None:
        """Scan the filesystem for templates."""

        self._cache = {}
        self._scan_directory(self.default_dir, "default")
        self._scan_directory(self.custom_dir, "custom")
        self._last_scan = time.time()

    def _scan_directory(self, base_path: Path, location: str) -> None:
        if not base_path.exists():
            return
        for metadata_path in base_path.rglob("metadata.yaml"):
            try:
                metadata = self._load_metadata(metadata_path)
                template_path = metadata_path.with_name("template.j2")
                if not template_path.exists():
                    continue
                record_dir = metadata_path.parent
                record = TemplateRecord(
                    template_id=metadata.id,
                    metadata=metadata,
                    template_path=template_path,
                    metadata_path=metadata_path,
                    location=location,
                    relative_dir=record_dir.relative_to(self.templates_dir),
                )
                self._cache = self._merge_record(self._cache, record)
            except Exception:
                continue

    def _merge_record(
        self,
        cache: Dict[str, TemplateRecord],
        record: TemplateRecord,
    ) -> Dict[str, TemplateRecord]:
        existing = cache.get(record.template_id)
        if existing is None:
            cache[record.template_id] = record
            return cache

        if self.precedence == "custom_first" and record.location == "custom":
            cache[record.template_id] = record
        elif self.precedence == "default_first" and record.location == "default":
            cache[record.template_id] = record
        elif self.precedence == "explicit":
            cache[f"{record.location}:{record.template_id}"] = record
        return cache

    def list_templates(self) -> List[TemplateRecord]:
        """Return list of templates respecting cache TTL."""

        self._ensure_cache()
        return sorted(self._cache.values(), key=lambda rec: rec.template_id)

    def get_template(self, template_id: str) -> Optional[TemplateRecord]:
        """Return the record for a template id."""

        self._ensure_cache()
        return self._cache.get(template_id)

    def _ensure_cache(self) -> None:
        if (time.time() - self._last_scan) > self.cache_ttl:
            self.refresh()

    def _load_metadata(self, path: Path) -> TemplateMetadata:
        data = yaml.safe_load(path.read_text()) or {}
        if "id" not in data:
            rel = path.relative_to(self.templates_dir)
            data["id"] = "/".join(rel.parts[:-1])
        return TemplateMetadata.model_validate(data)


__all__ = ["TemplateLoader", "TemplateRecord"]
