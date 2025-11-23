from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field, ValidationError

from logforge.core.config import TemplateConfig

class TemplateMetadata(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    vendor: str
    product: str
    data_source: str = Field(alias="data_source")
    version: Optional[str] = None
    format: str
    author: Optional[str] = None
    updated: Optional[str] = None
    base_template: Optional[str] = None
    tags: Optional[list[str]] = None
    variables: Optional[list[Dict[str, Any]]] = None


class MetadataLoader:
    def __init__(
        self,
        config: TemplateConfig,
        loader,
        schema_path: Optional[Path] = None,
    ) -> None:
        self._config = config
        self._loader = loader
        self._schema = self._load_schema(schema_path)
        self._validator = Draft202012Validator(self._schema)

    def load_metadata(self, template_id: str) -> TemplateMetadata:
        metadata_path = self._loader.metadata(template_id)
        raw = self._read_yaml(metadata_path)
        self._validate_schema(raw, metadata_path)
        try:
            return TemplateMetadata.model_validate(raw)
        except ValidationError as exc:
            raise ValueError(f"Metadata validation failed for {template_id}: {exc}") from exc

    def load_metadata_path(self, metadata_path: Path) -> TemplateMetadata:
        raw = self._read_yaml(metadata_path)
        self._validate_schema(raw, metadata_path)
        try:
            return TemplateMetadata.model_validate(raw)
        except ValidationError as exc:
            raise ValueError(f"Metadata validation failed for {metadata_path}: {exc}") from exc

    def _load_schema(self, schema_path: Optional[Path]) -> Dict[str, Any]:
        if schema_path is None:
            schema_path = Path("schemas/template.schema.json")
        schema_path = schema_path.expanduser().resolve()
        if not schema_path.is_file():
            raise FileNotFoundError(f"Template schema not found at {schema_path}")
        with schema_path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        schema["additionalProperties"] = True
        return schema

    def _read_yaml(self, path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"Metadata file must be a mapping: {path}")
        return data

    def _validate_schema(self, data: Dict[str, Any], path: Path) -> None:
        errors = sorted(self._validator.iter_errors(data), key=lambda e: e.path)
        if errors:
            message = "; ".join(f"{'.'.join(map(str, err.path))}: {err.message}" for err in errors)
            raise ValueError(f"Metadata schema validation failed for {path}: {message}")

