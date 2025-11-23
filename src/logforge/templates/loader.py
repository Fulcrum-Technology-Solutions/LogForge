from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from logforge.core.config import TemplateConfig

LOGGER = logging.getLogger(__name__)


class TemplateLoader:
    def __init__(self, config: TemplateConfig) -> None:
        self._config = config
        self._local_path = self._resolve_path(config.local_path)
        self._default_path = self._resolve_path(config.default_path)
        self._custom_path = self._resolve_path(config.custom_path)

    def _resolve_path(self, path: Path) -> Path:
        return path.expanduser().resolve()

    def resolve(self, template_id: str) -> Path:
        base_paths, relative = self._resolve_template_path(template_id)
        for base in base_paths:
            candidate = base / relative / "template.j2"
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(f"Template '{template_id}' not found in configured paths.")

    def metadata(self, template_id: str) -> Path:
        resolved_template = self.resolve(template_id)
        metadata_path = resolved_template.with_name("metadata.yaml")
        if not metadata_path.is_file():
            raise FileNotFoundError(f"Metadata for template '{template_id}' not found.")
        return metadata_path

    def list_templates(self) -> Dict[str, Dict[str, Path]]:
        templates: Dict[str, Dict[str, Path]] = {}
        for base in self._build_search_order(unique=False):
            location = "custom" if base == self._custom_path else "default"
            for entry in self._iter_templates(base, location):
                template_id = entry["id"]
                templates.setdefault(template_id, {})
                templates[template_id][location] = entry["template"]
        return templates

    def _resolve_template_path(self, template_id: str) -> tuple[Iterable[Path], Path]:
        precedence = self._config.precedence
        prefix = None
        identifier = template_id

        if precedence == "explicit":
            if ":" not in template_id:
                raise ValueError(
                    "Template precedence set to 'explicit'; template ids must include namespace prefix "
                    "('custom:' or 'default:')."
                )
            prefix, identifier = template_id.split(":", 1)
            prefix = prefix.lower()
            if prefix not in {"default", "custom"}:
                raise ValueError(f"Unsupported template namespace '{prefix}'. Expected 'default' or 'custom'.")

        parts = identifier.split("/")
        if len(parts) < 4:
            raise ValueError(f"Invalid template id '{identifier}'. Expected vendor/product/data_source/name.")

        relative = Path(*parts)

        if prefix == "default":
            search_order = [self._default_path]
        elif prefix == "custom":
            search_order = [self._custom_path]
        else:
            search_order = list(self._build_search_order())

        return search_order, relative

    def _build_search_order(self, unique: bool = True) -> Iterable[Path]:
        precedence = self._config.precedence
        if precedence == "custom_first":
            order = [self._custom_path, self._default_path]
        elif precedence == "default_first":
            order = [self._default_path, self._custom_path]
        elif precedence == "explicit":
            order = [self._custom_path, self._default_path]
        else:
            raise ValueError(f"Unknown precedence value: {precedence}")

        if unique:
            seen = set()
            for path in order:
                if path not in seen:
                    seen.add(path)
                    yield path
        else:
            for path in order:
                yield path

    def _iter_templates(self, base_path: Path, location: str) -> Iterable[Dict[str, Path]]:
        if not base_path.exists():
            return []

        results: List[Dict[str, Path]] = []
        for metadata_path in base_path.glob("**/metadata.yaml"):
            try:
                template_id = self._template_id_from_metadata(metadata_path, base_path)
            except Exception:
                LOGGER.debug("Skipping metadata at %s due to missing id.", metadata_path)
                continue
            template_path = metadata_path.with_name("template.j2")
            if not template_path.is_file():
                continue
            results.append({"id": template_id, "template": template_path, "metadata": metadata_path, "location": location})
        return results

    @staticmethod
    def _template_id_from_metadata(metadata_path: Path, base_path: Path) -> str:
        with metadata_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("id:"):
                    return line.split(":", 1)[1].strip()
        relative = metadata_path.relative_to(base_path)
        parts = relative.parts[:-1]
        return "/".join(parts)

