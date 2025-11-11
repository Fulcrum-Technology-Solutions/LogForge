from __future__ import annotations

from typing import Dict, Optional

from logforge.entities.registry import EntityRegistry


class RegistryFunctions:
    def __init__(self, registry: EntityRegistry) -> None:
        self._registry = registry

    def get_random_user(self) -> Optional[Dict]:
        return self._registry.get_random("users")

    def get_random_device(self) -> Optional[Dict]:
        return self._registry.get_random("devices")

    def get_random_service(self) -> Optional[Dict]:
        return self._registry.get_random("services")

    def get_organization(self) -> Dict:
        return self._registry.summary()["organization"]

    def get_user(self, username: str) -> Optional[Dict]:
        return self._registry.get_entity("users", username)

    def get_device(self, hostname: str) -> Optional[Dict]:
        return self._registry.get_entity("devices", hostname)

    def get_service(self, name: str) -> Optional[Dict]:
        return self._registry.get_entity("services", name)

    def get_organization_field(self, field: str) -> Optional[str]:
        org = self.get_organization()
        return org.get(field)
