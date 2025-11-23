"""Template rendering engine built on Jinja2."""

from __future__ import annotations

from typing import Any, Dict, Optional

from faker import Faker
from jinja2 import Environment, FileSystemLoader

from logforge.entities import functions as registry_functions
from logforge.templates.filters import register_filters
from logforge.templates.loader import TemplateLoader


class TemplateRenderer:
    """Render templates discovered by TemplateLoader with Faker + registry context."""

    def __init__(self, loader: TemplateLoader) -> None:
        self.loader = loader
        self.env = Environment(
            loader=FileSystemLoader(str(loader.templates_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        register_filters(self.env)
        self.env.globals["fake"] = Faker()
        self.env.globals["registry"] = registry_functions

    def render(self, template_id: str, context: Optional[Dict[str, Any]] = None) -> str:
        record = self.loader.get_template(template_id)
        if record is None:
            raise ValueError(f"Template '{template_id}' not found.")
        template_name = record.template_path.relative_to(self.loader.templates_dir).as_posix()
        template = self.env.get_template(template_name)
        base_context: Dict[str, Any] = {
            "metadata": record.metadata.model_dump(),
        }
        if context:
            base_context.update(context)
        return template.render(**base_context)


__all__ = ["TemplateRenderer"]
