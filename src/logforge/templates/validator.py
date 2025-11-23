"""Template validation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from logforge.templates.filters import register_filters
from logforge.templates.loader import TemplateLoader, TemplateRecord
from logforge.templates.models import TemplateMetadata


@dataclass
class TemplateValidationResult:
    template_id: str
    metadata: TemplateMetadata
    template_path: Path


class TemplateValidationError(Exception):
    """Raised when template validation fails."""


class TemplateValidator:
    def __init__(self, loader: TemplateLoader) -> None:
        self.loader = loader
        self.env = Environment(loader=FileSystemLoader(str(loader.templates_dir)))
        register_filters(self.env)

    def validate(self, template_id: str) -> TemplateValidationResult:
        record = self.loader.get_template(template_id)
        if record is None:
            raise TemplateValidationError(f"Template '{template_id}' not found.")
        self._validate_record(record)
        return TemplateValidationResult(
            template_id=record.template_id,
            metadata=record.metadata,
            template_path=record.template_path,
        )

    def validate_path(self, metadata_path: Path) -> TemplateValidationResult:
        metadata = TemplateMetadata.model_validate(yaml.safe_load(metadata_path.read_text()) or {})
        template_path = metadata_path.with_name("template.j2")
        try:
            relative_dir = metadata_path.parent.relative_to(self.loader.templates_dir)
        except ValueError:
            relative_dir = metadata_path.parent
        record = TemplateRecord(
            template_id=metadata.id,
            metadata=metadata,
            template_path=template_path,
            metadata_path=metadata_path,
            location="custom",
            relative_dir=relative_dir,
        )
        self._validate_record(record)
        return TemplateValidationResult(
            template_id=record.template_id,
            metadata=record.metadata,
            template_path=record.template_path,
        )

    def _validate_record(self, record: TemplateRecord) -> None:
        if not record.template_path.exists():
            raise TemplateValidationError(f"Template file missing: {record.template_path}")
        try:
            template_path = record.template_path.relative_to(self.loader.templates_dir)
        except ValueError:
            template_path = record.template_path
        template_name = template_path.as_posix()
        try:
            source, _, _ = self.env.loader.get_source(self.env, template_name)
            self.env.parse(source)
        except TemplateNotFound as exc:
            raise TemplateValidationError(f"Template not found: {template_name}") from exc
        except Exception as exc:  # pragma: no cover - jinja error surfaces line info
            raise TemplateValidationError(f"Jinja2 validation failed: {exc}") from exc


__all__ = ["TemplateValidator", "TemplateValidationResult", "TemplateValidationError"]
