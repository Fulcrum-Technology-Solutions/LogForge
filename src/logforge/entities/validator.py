"""Entity validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from pydantic import ValidationError

from logforge.entities.models import EntityDocument


@dataclass
class EntityValidationError(Exception):
    message: str
    line: int | None = None

    def __str__(self) -> str:  # pragma: no cover - simple string repr
        if self.line is not None:
            return f"{self.message} (line {self.line})"
        return self.message


def validate_entities(data: dict[str, Any]) -> EntityDocument:
    try:
        document = EntityDocument.model_validate(data)
    except ValidationError as exc:
        first_error = exc.errors()[0]
        field = ".".join(str(part) for part in first_error["loc"])
        raise EntityValidationError(f"{field}: {first_error['msg']}")

    _assert_unique([user.username for user in document.users], "users.username")
    _assert_unique([user.email for user in document.users], "users.email")
    _assert_unique([device.hostname for device in document.devices], "devices.hostname")
    _assert_unique([service.name for service in document.services], "services.name")

    return document


def _assert_unique(values: Iterable[Any], field_name: str) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise EntityValidationError(f"Duplicate value '{value}' for {field_name}")
        seen.add(value)


__all__ = ["validate_entities", "EntityValidationError"]
