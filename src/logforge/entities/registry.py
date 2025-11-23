"""In-memory entity registry with autosave support."""

from __future__ import annotations

import random
from typing import Any, List, Optional, Sequence, cast

from pydantic import BaseModel

from logforge.entities.models import (
    DeviceEntity,
    EntityDocument,
    Organization,
    ServiceEntity,
    UserEntity,
)
from logforge.entities.storage import EntityStorage
from logforge.entities.validator import EntityValidationError, validate_entities


class EntityRegistry:
    """Loads, validates, and serves entity data to templates and API."""

    def __init__(
        self,
        *,
        storage: Optional[EntityStorage] = None,
        autosave: bool = True,
    ) -> None:
        self.storage = storage or EntityStorage()
        raw = self.storage.load()
        self.document = validate_entities(raw) if raw else self._empty_document()
        if autosave:
            self.storage.start_autosave(lambda: self.document.model_dump())

    def summary(self) -> dict[str, Any]:
        return {
            "organization": {
                "name": self.document.organization.name,
                "domain": self.document.organization.domain,
            },
            "users": len(self.document.users),
            "devices": len(self.document.devices),
            "services": len(self.document.services),
        }

    def list_entities(self, entity_type: str) -> List[dict[str, Any]]:
        collection = getattr(self.document, entity_type)
        return [entity.model_dump() for entity in collection]

    def add_entity(self, entity_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        collection = getattr(self.document, entity_type)
        model_cls = {
            "users": UserEntity,
            "devices": DeviceEntity,
            "services": ServiceEntity,
        }.get(entity_type)
        if model_cls is None:
            raise EntityValidationError(f"Unsupported entity type '{entity_type}'")
        model = model_cls(**payload)
        collection.append(model)
        self.storage.save(self.document.model_dump())
        return cast(dict[str, Any], model.model_dump())

    def get_random_user(self) -> Optional[dict[str, Any]]:
        return self._get_random(self.document.users)

    def get_random_service(self) -> Optional[dict[str, Any]]:
        return self._get_random(self.document.services)

    def _get_random(self, items: Sequence[BaseModel]) -> Optional[dict[str, Any]]:
        if not items:
            return None
        choice = random.choice(items)
        return cast(dict[str, Any], choice.model_dump())

    @staticmethod
    def _empty_document() -> EntityDocument:
        return EntityDocument(
            organization=Organization(name="Example Corp", domain="example.com"),
            users=[],
            devices=[],
            services=[],
        )


__all__ = ["EntityRegistry"]
