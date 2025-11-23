from __future__ import annotations

import logging
import random
import threading
from typing import Dict, List, Optional

import yaml

from logforge.core.config import ConfigError, EntityRegistryConfig
from logforge.entities.models import Device, EntitiesModel, Organization, Service, User
from logforge.entities.storage import EntitiesStorage

LOGGER = logging.getLogger(__name__)


class EntityRegistry:
    def __init__(self, config: EntityRegistryConfig) -> None:
        self._config = config
        self._storage = EntitiesStorage(config)
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._auto_save_thread: Optional[threading.Thread] = None
        self._entities: Optional[EntitiesModel] = None

        self.reload()
        self._start_auto_save()

    @property
    def entities(self) -> EntitiesModel:
        if self._entities is None:
            raise RuntimeError("Entity registry not loaded.")
        return self._entities

    def reload(self) -> None:
        with self._lock:
            try:
                self._entities = self._storage.load()
            except ConfigError as exc:
                if self._config.backup_enabled:
                    LOGGER.warning(
                        "Primary entity registry load failed (%s). Attempting backup recovery.",
                        exc,
                    )
                    try:
                        self._entities = self._storage.load_latest_backup()
                        LOGGER.info("Entity registry recovered from backup.")
                        return
                    except ConfigError as backup_exc:
                        LOGGER.error("Entity registry backup recovery failed: %s", backup_exc)
                        raise backup_exc
                raise

    def save(self) -> None:
        with self._lock:
            if self._entities is None:
                raise RuntimeError("Cannot save registry before it has been loaded.")
            self._storage.save(self._entities)

    def shutdown(self) -> None:
        self._stop_event.set()
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            self._auto_save_thread.join(timeout=2)
        self._auto_save_thread = None

    def _start_auto_save(self) -> None:
        if not self._config.auto_save:
            return
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            return

        interval = max(self._config.save_interval, 1)

        def _loop() -> None:
            while not self._stop_event.wait(interval):
                try:
                    self.save()
                except Exception as exc:  # pragma: no cover - logged for operators
                    LOGGER.exception("Auto-save failed: %s", exc)

        self._auto_save_thread = threading.Thread(target=_loop, daemon=True)
        self._auto_save_thread.start()

    def get_organization(self) -> Organization:
        return self.entities.organization

    def get_organization_field(self, key: str) -> Optional[str]:
        return self.entities.organization.attributes.get(key)

    def get_organization_contact(self, key: str) -> Optional[str]:
        return self.entities.organization.contacts.get(key)

    def get_users(self) -> Dict[str, User]:
        return {user.username: user for user in self.entities.users}

    def get_devices(self) -> Dict[str, Device]:
        return {device.hostname: device for device in self.entities.devices}

    def get_services(self) -> Dict[str, Service]:
        return {service.name: service for service in self.entities.services}

    def get_user(self, username: str) -> Optional[User]:
        username_lower = username.lower()
        return next((user for user in self.entities.users if user.username.lower() == username_lower), None)

    def get_device(self, hostname: str) -> Optional[Device]:
        hostname_lower = hostname.lower()
        return next((device for device in self.entities.devices if device.hostname.lower() == hostname_lower), None)

    def get_service(self, name: str) -> Optional[Service]:
        name_lower = name.lower()
        return next((service for service in self.entities.services if service.name.lower() == name_lower), None)

    def get_random_user(self) -> User:
        return random.choice(self.entities.users)

    def get_random_device(self) -> Device:
        return random.choice(self.entities.devices)

    def get_random_service(self) -> Service:
        return random.choice(self.entities.services)

    def list_entities(self, entity_type: str) -> List[dict]:
        with self._lock:
            mapping = {
                "users": [user.model_dump() for user in self.entities.users],
                "devices": [device.model_dump() for device in self.entities.devices],
                "services": [service.model_dump() for service in self.entities.services],
            }
            if entity_type == "organization":
                return [self.entities.organization.model_dump()]
            if entity_type not in mapping:
                raise ValueError(f"Unsupported entity type '{entity_type}'")
            return mapping[entity_type]

    def get_entity(self, entity_type: str, identifier: str) -> dict:
        with self._lock:
            lookup = self._resolve_lookup(entity_type, identifier)
            if lookup is None:
                raise KeyError(f"{entity_type} '{identifier}' not found")
            return lookup.model_dump()

    def create_entity(self, entity_type: str, payload: dict) -> dict:
        def mutate(entities: EntitiesModel) -> None:
            if entity_type == "users":
                user = User.model_validate(payload)
                if self._find_index(entities.users, user.username) is not None:
                    raise ValueError(f"User '{user.username}' already exists.")
                entities.users.append(user)
            elif entity_type == "devices":
                device = Device.model_validate(payload)
                if self._find_index(entities.devices, device.hostname) is not None:
                    raise ValueError(f"Device '{device.hostname}' already exists.")
                entities.devices.append(device)
            elif entity_type == "services":
                service = Service.model_validate(payload)
                if self._find_index(entities.services, service.name) is not None:
                    raise ValueError(f"Service '{service.name}' already exists.")
                entities.services.append(service)
            else:
                raise ValueError(f"Unsupported entity type '{entity_type}'")

        entity = self._mutate(mutate)
        return self.get_entity(entity_type, payload.get("username") or payload.get("hostname") or payload.get("name"))

    def update_entity(self, entity_type: str, identifier: str, payload: dict) -> dict:
        def mutate(entities: EntitiesModel) -> None:
            if entity_type == "users":
                user = User.model_validate(payload)
                index = self._find_index(entities.users, identifier)
                if index is None:
                    raise KeyError(f"User '{identifier}' not found.")
                entities.users[index] = user
            elif entity_type == "devices":
                device = Device.model_validate(payload)
                index = self._find_index(entities.devices, identifier)
                if index is None:
                    raise KeyError(f"Device '{identifier}' not found.")
                entities.devices[index] = device
            elif entity_type == "services":
                service = Service.model_validate(payload)
                index = self._find_index(entities.services, identifier)
                if index is None:
                    raise KeyError(f"Service '{identifier}' not found.")
                entities.services[index] = service
            else:
                raise ValueError(f"Unsupported entity type '{entity_type}'")

        self._mutate(mutate)
        return self.get_entity(entity_type, identifier)

    def delete_entity(self, entity_type: str, identifier: str) -> None:
        def mutate(entities: EntitiesModel) -> None:
            if entity_type == "users":
                index = self._find_index(entities.users, identifier)
                if index is None:
                    raise KeyError(f"User '{identifier}' not found.")
                del entities.users[index]
            elif entity_type == "devices":
                index = self._find_index(entities.devices, identifier)
                if index is None:
                    raise KeyError(f"Device '{identifier}' not found.")
                del entities.devices[index]
            elif entity_type == "services":
                index = self._find_index(entities.services, identifier)
                if index is None:
                    raise KeyError(f"Service '{identifier}' not found.")
                del entities.services[index]
            else:
                raise ValueError(f"Unsupported entity type '{entity_type}'")

        self._mutate(mutate)

    def import_yaml(self, content: str) -> None:
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise ValueError("Entity import must be a YAML mapping.")
        model = EntitiesModel.model_validate(data)
        with self._lock:
            self._entities = model
            self._storage.save(self._entities)

    def export_yaml(self) -> str:
        with self._lock:
            if self._entities is None:
                raise RuntimeError("Entity registry not loaded.")
            payload = self._entities.model_dump(mode="json", by_alias=True)
            return yaml.safe_dump(payload, sort_keys=False)

    def validate_yaml(self, content: str) -> None:
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise ValueError("Entity definition must be a YAML mapping.")
        EntitiesModel.model_validate(data)

    def _mutate(self, mutator) -> EntitiesModel:
        with self._lock:
            if self._entities is None:
                raise RuntimeError("Entity registry not loaded.")
            mutator(self._entities)
            self._entities = EntitiesModel.model_validate(self._entities.model_dump())
            self._storage.save(self._entities)
            return self._entities

    def _find_index(self, collection, identifier: str) -> Optional[int]:
        identifier_lower = identifier.lower()
        for index, item in enumerate(collection):
            key = getattr(item, "username", None) or getattr(item, "hostname", None) or getattr(item, "name", None)
            if key and key.lower() == identifier_lower:
                return index
        return None

    def _resolve_lookup(self, entity_type: str, identifier: str):
        if entity_type == "users":
            return self.get_user(identifier)
        if entity_type == "devices":
            return self.get_device(identifier)
        if entity_type == "services":
            return self.get_service(identifier)
        if entity_type == "organization":
            org = self.entities.organization
            if org.name.lower() != identifier.lower():
                raise KeyError(f"Organization '{identifier}' not found.")
            return org
        raise ValueError(f"Unsupported entity type '{entity_type}'")

