from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from jinja2 import Environment, FileSystemLoader, meta
from pydantic import ValidationError

from logforge.entities.functions import RegistryFunctions
from logforge.templates.loader import TemplateLoader
from logforge.templates.models import TemplateMetadata


class TemplateValidationError(Exception):
    pass


class TemplateValidator:
    def __init__(self, loader: TemplateLoader, registry_functions: RegistryFunctions) -> None:
        self.loader = loader
        self.registry = registry_functions

    def validate_template(self, template_id: str) -> TemplateMetadata:
        record = self.loader.get_template(template_id)
        self._validate_metadata(record.metadata)
        self._validate_template_source(record.path, template_id)
        return record.metadata

    def validate_path(self, path: Path) -> TemplateMetadata:
        metadata = self.loader.load_metadata(path)
        self._validate_metadata(metadata)
        self._validate_template_source(path, metadata.id)
        return metadata

    def _validate_metadata(self, metadata: TemplateMetadata) -> None:
        try:
            TemplateMetadata.model_validate(metadata.model_dump())
        except ValidationError as exc:
            raise TemplateValidationError(str(exc)) from exc

    def _validate_template_source(self, template_dir: Path, template_id: str) -> None:
        template_path = template_dir / "template.j2"
        if not template_path.exists():
            raise TemplateValidationError("template.j2 missing")

        env = Environment(loader=FileSystemLoader(str(template_dir.parent.parent)))
        source = template_path.read_text(encoding="utf-8")
        ast = env.parse(source)
        undefined = meta.find_undeclared_variables(ast)

        allowed_globals = {"registry", "fake", "now", "random_int", "random_choice"}
        missing = {name for name in undefined if name not in allowed_globals}
        if missing:
            raise TemplateValidationError(f"Unknown variables in template: {', '.join(sorted(missing))}")

        # attempt render with minimal context to catch runtime errors
        from logforge.templates.renderer import TemplateRenderer

        renderer = TemplateRenderer(self.loader, self.registry)
        try:
            renderer.render(template_id, extra_context={"dry_run": True})
        except Exception as exc:  # pragma: no cover - runtime errors
            raise TemplateValidationError(f"Template rendering failed: {exc}") from exc
