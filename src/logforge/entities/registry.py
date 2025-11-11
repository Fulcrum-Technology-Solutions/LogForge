from __future__ import annotations

import random
import threading
from typing import Dict, Iterable, List, Optional

from logforge.core.config import LogForgeConfig
from logforge.entities import validator
from logforge.entities.models import EntityBundle
from logforge.entities.storage import EntityStorage
from logforge.utils.logging import get_logger

logger = get_logger(__name__)

EntityType = str


class EntityRegistry:
    def __init__(self, storage: EntityStorage, auto_save: bool = True) -> None:
        self._storage = storage
        self._data: EntityBundle = EntityBundle(
            organization={
                "name": "Example Corp",
                "domain": "example.com",
            },
        )  # placeholder, will be replaced on load
        self._lock = threading.RLock()
        self._auto_save = auto_save
        self.load()

    @classmethod
    def from_config(cls, config: LogForgeConfig) -> "EntityRegistry":
        settings = config.entity_registry
        storage = EntityStorage(settings.path, backup_count=settings.backup_count)
        return cls(storage, auto_save=settings.auto_save)

    def load(self) -> None:
        raw_data = self._storage.load()
        if not raw_data:
            logger.info("Entity registry empty; skipping load")
            self._data = EntityBundle(
                organization={"name": "Example Corp", "domain": "example.com"},
                users=[],
                devices=[],
                services=[],
            )
            return
        bundle = validator.validate_bundle(raw_data)
        self._data = bundle
        logger.info(
            "Loaded entity registry: %d users, %d devices, %d services",
            len(bundle.users),
            len(bundle.devices),
            len(bundle.services),
        )

    def save(self) -> None:
        with self._lock:
            self._storage.save(self._data.model_dump(mode="json"))

    def summary(self) -> Dict[str, object]:
        with self._lock:
            return {
                "organization": self._data.organization.model_dump(mode="json"),
                "users": len(self._data.users),
                "devices": len(self._data.devices),
                "services": len(self._data.services),
            }

    def list_entities(self, entity_type: EntityType) -> List[Dict]:
        with self._lock:
            data = getattr(self._data, entity_type)
            return [item.model_dump(mode="json") for item in data]

    def get_entity(self, entity_type: EntityType, identifier: str) -> Optional[Dict]:
        key = _entity_identifier_key(entity_type)
        with self._lock:
            for item in getattr(self._data, entity_type):
                if getattr(item, key) == identifier:
                    return item.model_dump(mode="json")
        return None

    def add_entity(self, entity_type: EntityType, payload: Dict) -> Dict:
        validated = validator.validate_entity_payload(entity_type, payload)
        key = _entity_identifier_key(entity_type)
        with self._lock:
            items = getattr(self._data, entity_type)
            if any(getattr(item, key) == validated[key] for item in items):
                raise validator.EntityValidationError(f"{entity_type[:-1].capitalize()} '{validated[key]}' already exists")
            model_cls = _entity_model(entity_type)
            instance = model_cls.model_validate(validated)
            items.append(instance)
            if self._auto_save:
                self.save()
            return instance.model_dump(mode="json")

    def update_entity(self, entity_type: EntityType, identifier: str, payload: Dict) -> Dict:
        validated = validator.validate_entity_payload(entity_type, payload)
        key = _entity_identifier_key(entity_type)
        with self._lock:
            items = getattr(self._data, entity_type)
            for index, item in enumerate(items):
                if getattr(item, key) == identifier:
                    model_cls = _entity_model(entity_type)
                    instance = model_cls.model_validate({**item.model_dump(), **validated})
                    items[index] = instance
                    if self._auto_save:
                        self.save()
                    return instance.model_dump(mode="json")
        raise validator.EntityValidationError(f"{entity_type[:-1].capitalize()} '{identifier}' not found")

    def delete_entity(self, entity_type: EntityType, identifier: str) -> None:
        key = _entity_identifier_key(entity_type)
        with self._lock:
            items = getattr(self._data, entity_type)
            remaining = [item for item in items if getattr(item, key) != identifier]
            if len(remaining) == len(items):
                raise validator.EntityValidationError(f"{entity_type[:-1].capitalize()} '{identifier}' not found")
            setattr(self._data, entity_type, remaining)
            if self._auto_save:
                self.save()

    def import_bundle(self, data: Dict, *, replace: bool = False) -> Dict:
        bundle = validator.validate_bundle(validator.prune_unknown_types(data))
        with self._lock:
            if replace:
                self._data = bundle
            else:
                self._merge_bundle(bundle)
            if self._auto_save:
                self.save()
            return self._data.model_dump(mode="json")

    def export_bundle(self) -> Dict:
        with self._lock:
            return self._data.model_dump(mode="json")

    def get_random(self, entity_type: EntityType) -> Optional[Dict]:
        with self._lock:
            items = getattr(self._data, entity_type)
            if not items:
                return None
            return random.choice(items).model_dump(mode="json")

    def _merge_bundle(self, bundle: EntityBundle) -> None:
        existing_users = {user.username: user for user in self._data.users}
        existing_devices = {device.hostname: device for device in self._data.devices}
        existing_services = {service.name: service for service in self._data.services}

        for user in bundle.users:
            existing_users[user.username] = user
        for device in bundle.devices:
            existing_devices[device.hostname] = device
        for service in bundle.services:
            existing_services[service.name] = service

        self._data = EntityBundle(
            organization=bundle.organization,
            users=list(existing_users.values()),
            devices=list(existing_devices.values()),
            services=list(existing_services.values()),
        )


def _entity_identifier_key(entity_type: EntityType) -> str:
    if entity_type == "users":
        return "username"
    if entity_type == "devices":
        return "hostname"
    if entity_type == "services":
        return "name"
    raise ValueError(f"Unsupported entity type: {entity_type}")


def _entity_model(entity_type: EntityType):
    from logforge.entities.models import User, Device, Service

    return {"users": User, "devices": Device, "services": Service}[entity_type]
