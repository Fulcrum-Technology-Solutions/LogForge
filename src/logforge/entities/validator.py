from __future__ import annotations

from typing import Dict, Iterable, Tuple

from pydantic import ValidationError

from logforge.entities.models import EntityBundle

ALLOWED_TYPES = {"users", "devices", "services"}


class EntityValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


def _assert_unique(items: Iterable[str], item_type: str) -> None:
    seen = set()
    duplicates = set()
    for value in items:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        raise EntityValidationError(f"Duplicate {item_type} detected: {', '.join(sorted(duplicates))}")


def validate_bundle(data: Dict) -> EntityBundle:
    try:
        bundle = EntityBundle.model_validate(data)
    except ValidationError as exc:
        raise EntityValidationError(str(exc)) from exc

    _assert_unique((user.username for user in bundle.users), "usernames")
    _assert_unique((device.hostname for device in bundle.devices), "hostnames")
    _assert_unique((service.name for service in bundle.services), "service names")

    owners = {user.username for user in bundle.users}
    for device in bundle.devices:
        if device.owner and device.owner not in owners:
            raise EntityValidationError(f"Device owner '{device.owner}' does not match any user")

    return bundle


def prune_unknown_types(data: Dict) -> Dict:
    return {key: value for key, value in data.items() if key in {"organization", *ALLOWED_TYPES}}


def validate_entity_payload(entity_type: str, payload: Dict) -> Dict:
    bundle_dict = {"organization": {"name": "Temp", "domain": "example.com"}, entity_type: [payload]}
    bundle = validate_bundle(bundle_dict)
    return bundle.model_dump()[entity_type][0]
