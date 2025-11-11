from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml

from logforge.core.config import TemplateSettings
from logforge.templates.models import TemplateMetadata, TemplateRecord


@dataclass
class TemplatePaths:
    base: Path
    default_dir: Path
    custom_dir: Path


class TemplateLoader:
    def __init__(self, settings: TemplateSettings) -> None:
        self.settings = settings
        self.paths = TemplatePaths(
            base=Path(settings.local_path),
            default_dir=Path(settings.local_path) / "default",
            custom_dir=Path(settings.local_path) / "custom",
        )
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        self.paths.default_dir.mkdir(parents=True, exist_ok=True)
        self.paths.custom_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[TemplateRecord]:
        default_templates = self._scan_directory(self.paths.default_dir, location="default")
        custom_templates = self._scan_directory(self.paths.custom_dir, location="custom")

        merged: Dict[str, TemplateRecord] = {}
        for record in default_templates:
            merged[record.id] = record

        for record in custom_templates:
            base = merged.get(record.id)
            if base:
                record.overrides = f"Overrides default v{base.version}" if base.version else "Overrides default"
            merged[record.id] = record

        return sorted(merged.values(), key=lambda r: r.id)

    def get_template(self, template_id: str) -> TemplateRecord:
        custom_path = self._template_path(self.paths.custom_dir, template_id)
        if custom_path:
            record = self._build_record(custom_path, "custom")
            default_path = self._template_path(self.paths.default_dir, template_id)
            if default_path:
                base = self._build_record(default_path, "default")
                record.overrides = f"Overrides default v{base.version}" if base.version else "Overrides default"
            return record

        default_path = self._template_path(self.paths.default_dir, template_id)
        if default_path:
            return self._build_record(default_path, "default")
        raise FileNotFoundError(f"Template '{template_id}' not found")

    def metadata_for(self, template_id: str) -> TemplateMetadata:
        return self.get_template(template_id).metadata

    def load_template_source(self, template_id: str) -> str:
        record = self.get_template(template_id)
        template_path = record.path / "template.j2"
        if not template_path.exists():
            raise FileNotFoundError(f"Template source missing for '{template_id}'")
        return template_path.read_text(encoding="utf-8")

    def load_metadata(self, path: Path) -> TemplateMetadata:
        metadata_path = path / "metadata.yaml"
        if not metadata_path.exists():
            raise FileNotFoundError(f"metadata.yaml missing under {path}")
        with metadata_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        return TemplateMetadata.model_validate(payload)

    def export_bundle(self, template_id: str) -> Dict[str, str]:
        record = self.get_template(template_id)
        bundle = {}
        for item in record.path.rglob("*"):
            if item.is_file():
                rel = item.relative_to(record.path)
                bundle[str(rel)] = item.read_text(encoding="utf-8")
        return bundle

    def customize(self, template_id: str) -> Path:
        record = self.get_template(template_id)
        if record.location == "custom":
            return record.path

        target = self.paths.custom_dir / Path(template_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            return target

        for item in record.path.rglob("*"):
            rel = item.relative_to(record.path)
            dest = target / rel
            if item.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
        return target

    def revert(self, template_id: str) -> None:
        custom_path = self._template_path(self.paths.custom_dir, template_id)
        if not custom_path:
            raise FileNotFoundError(f"No custom template '{template_id}' found")
        for item in sorted(custom_path.rglob("*"), reverse=True):
            if item.is_file():
                item.unlink()
            else:
                os.rmdir(item)
        os.rmdir(custom_path)

    def _scan_directory(self, base_dir: Path, *, location: str) -> List[TemplateRecord]:
        records: List[TemplateRecord] = []
        if not base_dir.exists():
            return records
        for metadata_path in base_dir.glob("**/metadata.yaml"):
            path = metadata_path.parent
            try:
                record = self._build_record(path, location)
            except Exception:
                continue
            records.append(record)
        return records

    def _build_record(self, path: Path, location: str) -> TemplateRecord:
        metadata = self.load_metadata(path)
        return TemplateRecord(
            id=metadata.id,
            name=metadata.name,
            version=metadata.version,
            location=location,
            path=path,
            metadata=metadata,
            local=True,
        )

    def _template_path(self, base_dir: Path, template_id: str) -> Optional[Path]:
        candidate = base_dir / Path(template_id)
        if candidate.exists() and (candidate / "metadata.yaml").exists():
            return candidate
        return None
