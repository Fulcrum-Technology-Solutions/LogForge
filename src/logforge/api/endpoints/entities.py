"""Entity API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, status

if TYPE_CHECKING:
    from logforge.api.server import APIDependencies

AuthDependency = Callable[..., Awaitable[None]]


def create_entities_router(deps: "APIDependencies", auth_dependency: AuthDependency) -> APIRouter:
    router = APIRouter(prefix="/entities", tags=["entities"])

    @router.get("")
    async def summary(_: None = Depends(auth_dependency)) -> dict:
        return deps.entities_summary()

    @router.get("/{entity_type}")
    async def list_entities(entity_type: str, _: None = Depends(auth_dependency)) -> dict:
        _ensure_type(entity_type)
        entities = deps.list_entities(entity_type)
        return {"type": entity_type, "count": len(entities), "entities": entities}

    @router.post("/{entity_type}", status_code=status.HTTP_201_CREATED)
    async def create_entity(
        entity_type: str,
        payload: dict,
        _: None = Depends(auth_dependency),
    ) -> dict:
        _ensure_type(entity_type)
        entity = deps.create_entity(entity_type, payload)
        return entity

    return router


def _ensure_type(entity_type: str) -> None:
    if entity_type not in {"users", "devices", "services"}:
        raise HTTPException(status_code=400, detail=f"Unsupported entity type '{entity_type}'")


__all__ = ["create_entities_router"]
