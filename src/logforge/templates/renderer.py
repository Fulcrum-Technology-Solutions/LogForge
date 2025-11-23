from __future__ import annotations

import datetime
import random
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from faker import Faker
from jinja2 import Environment, FileSystemLoader, select_autoescape

from logforge.entities.functions import RegistryFunctions


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _format_datetime(value: datetime.datetime, fmt: str) -> str:
    return value.strftime(fmt)


def _random_int(start: int, end: int) -> int:
    return random.randint(start, end)


def _random_choice(options: list[Any]) -> Any:
    return random.choice(options)


class TemplateRenderer:
    def __init__(self, template_root: Path, registry_functions: Optional[RegistryFunctions] = None) -> None:
        self._template_root = template_root.resolve()
        self._fake = Faker()
        self._env = Environment(
            loader=FileSystemLoader(str(self._template_root)),
            autoescape=select_autoescape(disabled_extensions=("j2",)),
        )
        self._register_filters()

        self._context: Dict[str, Any] = {
            "fake": self._fake,
            "now": _now,
            "random_int": _random_int,
            "random_choice": _random_choice,
        }

        if registry_functions:
            self._context["registry"] = registry_functions

    def _register_filters(self) -> None:
        self._env.filters["format_datetime"] = _format_datetime

    def render(self, template_path: Path, context: Optional[Dict[str, Any]] = None) -> str:
        if template_path.is_absolute():
            relative = template_path.resolve().relative_to(self._template_root)
        else:
            relative = template_path

        template = self._env.get_template(str(relative))
        render_context = dict(self._context)
        if context:
            render_context.update(context)
        return template.render(render_context)

