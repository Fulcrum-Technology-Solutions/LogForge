from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from faker import Faker
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

from logforge.entities.functions import RegistryFunctions
from logforge.templates.filters import format_datetime, now, random_choice, random_int
from logforge.templates.loader import TemplateLoader


class TemplateRenderer:
    def __init__(self, loader: TemplateLoader, registry_functions: RegistryFunctions) -> None:
        self.loader = loader
        self.registry = registry_functions
        self.fake = Faker()
        search_paths = [
            str(loader.paths.custom_dir),
            str(loader.paths.default_dir),
        ]
        self.env = Environment(
            loader=FileSystemLoader(search_paths),
            undefined=StrictUndefined,
            autoescape=False,
        )
        self._register_filters()

    def _register_filters(self) -> None:
        self.env.globals["now"] = now
        self.env.filters["format_datetime"] = format_datetime
        self.env.globals["random_int"] = random_int
        self.env.globals["random_choice"] = random_choice
        self.env.globals["fake"] = self.fake

    def render(self, template_id: str, *, extra_context: Optional[Dict[str, Any]] = None) -> str:
        record = self.loader.get_template(template_id)
        template_rel_path = Path(template_id) / "template.j2"
        try:
            template = self.env.get_template(str(template_rel_path))
        except TemplateNotFound as exc:
            raise FileNotFoundError(f"Template source missing for '{template_id}'") from exc

        context = {
            "registry": self.registry,
            "fake": self.fake,
        }
        if extra_context:
            context.update(extra_context)
        return template.render(**context)
