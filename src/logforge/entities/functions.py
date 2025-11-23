from __future__ import annotations

from typing import Optional, Protocol

from logforge.entities.registry import EntityRegistry


class ModelLike(Protocol):
    def dict(self) -> dict:
        ...


def _to_dict(model: Optional[ModelLike]) -> Optional[dict]:
    return model.dict() if model else None


class RegistryFunctions:
    def __init__(self, registry: EntityRegistry) -> None:
        self._registry = registry

    def get_random_user(self) -> dict:
        return self._registry.get_random_user().dict()

    def get_random_device(self) -> dict:
        return self._registry.get_random_device().dict()

    def get_random_service(self) -> dict:
        return self._registry.get_random_service().dict()

    def get_user(self, username: str) -> Optional[dict]:
        return _to_dict(self._registry.get_user(username))

    def get_device(self, hostname: str) -> Optional[dict]:
        return _to_dict(self._registry.get_device(hostname))

    def get_service(self, name: str) -> Optional[dict]:
        return _to_dict(self._registry.get_service(name))

    def get_organization(self) -> dict:
        return self._registry.get_organization().dict()

    def get_organization_field(self, key: str) -> Optional[str]:
        return self._registry.get_organization_field(key)

    def get_organization_contact(self, key: str) -> Optional[str]:
        return self._registry.get_organization_contact(key)

