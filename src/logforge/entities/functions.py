"""Template helper functions backed by EntityRegistry."""

from __future__ import annotations

from typing import Optional

from logforge.entities.registry import EntityRegistry

_registry = EntityRegistry()


def get_random_user() -> Optional[dict]:
    return _registry.get_random_user()


def get_random_service() -> Optional[dict]:
    return _registry.get_random_service()


def get_organization() -> dict:
    return _registry.document.organization.model_dump()


__all__ = ["get_random_user", "get_random_service", "get_organization"]
