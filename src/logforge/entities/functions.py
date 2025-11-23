"""Template helper functions backed by EntityRegistry."""

from __future__ import annotations

from typing import Optional

from logforge.entities.registry import EntityRegistry

_registry: Optional[EntityRegistry] = None


def _set_registry(registry: EntityRegistry) -> None:
    """Set the global registry instance (used by service initialization)."""
    global _registry
    _registry = registry


def _get_registry() -> EntityRegistry:
    """Get the global registry instance, creating default if needed."""
    global _registry
    if _registry is None:
        _registry = EntityRegistry()
    return _registry


def get_random_user() -> Optional[dict]:
    return _get_registry().get_random_user()


def get_random_service() -> Optional[dict]:
    return _get_registry().get_random_service()


def get_organization() -> dict:
    return _get_registry().document.organization.model_dump()


__all__ = ["get_random_user", "get_random_service", "get_organization", "_set_registry"]
