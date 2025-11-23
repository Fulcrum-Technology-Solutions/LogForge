from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from logforge.api.auth import get_context, require_api_key
from logforge.api.context import APIContext
from logforge.api.models import (
    EntityImportRequest,
    EntityPayload,
    EntityResponse,
    EntityValidationRequest,
)
from logforge.entities.registry import EntityRegistry

router = APIRouter()


class EntitiesSummary(BaseModel):
    organization: dict
    users: int
    devices: int
    services: int


class EntityCollection(BaseModel):
    type: str
    count: int
    entities: list[dict]


def _get_registry(context: APIContext) -> EntityRegistry:
    if context.entity_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Entity registry not available.",
        )
    return context.entity_registry


def _normalize_type(entity_type: str) -> str:
    entity_type = entity_type.lower()
    if entity_type not in {"users", "devices", "services", "organization"}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown entity type: {entity_type}",
        )
    return entity_type


@router.get("/entities", response_model=EntitiesSummary, dependencies=[Depends(require_api_key)])
async def get_entities_summary(context: APIContext = Depends(get_context)) -> EntitiesSummary:
    registry = _get_registry(context)
    organization = registry.get_organization().model_dump()
    return EntitiesSummary(
        organization=organization,
        users=len(registry.entities.users),
        devices=len(registry.entities.devices),
        services=len(registry.entities.services),
    )


@router.post(
    "/entities/import",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
async def import_entities(
    request: EntityImportRequest,
    context: APIContext = Depends(get_context),
) -> None:
    registry = _get_registry(context)
    try:
        registry.import_yaml(request.content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/entities/export",
    dependencies=[Depends(require_api_key)],
)
async def export_entities(context: APIContext = Depends(get_context)) -> dict:
    registry = _get_registry(context)
    return {"content": registry.export_yaml()}


@router.post(
    "/entities/validate",
    dependencies=[Depends(require_api_key)],
)
async def validate_entities(
    request: EntityValidationRequest,
    context: APIContext = Depends(get_context),
) -> dict:
    registry = _get_registry(context)
    try:
        registry.validate_yaml(request.content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"valid": True}


@router.get(
    "/entities/{entity_type}",
    response_model=EntityCollection,
    dependencies=[Depends(require_api_key)],
)
async def get_entities_by_type(
    entity_type: str,
    context: APIContext = Depends(get_context),
) -> EntityCollection:
    registry = _get_registry(context)
    entity_type = _normalize_type(entity_type)

    entities = registry.list_entities(entity_type)

    return EntityCollection(type=entity_type, count=len(entities), entities=entities)


@router.get(
    "/entities/{entity_type}/{identifier}",
    response_model=EntityResponse,
    dependencies=[Depends(require_api_key)],
)
async def get_entity_detail(
    entity_type: str,
    identifier: str,
    context: APIContext = Depends(get_context),
) -> EntityResponse:
    registry = _get_registry(context)
    entity_type = _normalize_type(entity_type)
    try:
        entity = registry.get_entity(entity_type, identifier)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return EntityResponse(type=entity_type, entity=entity)


@router.post(
    "/entities/{entity_type}",
    response_model=EntityResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
async def create_entity(
    entity_type: str,
    payload: EntityPayload,
    context: APIContext = Depends(get_context),
) -> EntityResponse:
    registry = _get_registry(context)
    entity_type = _normalize_type(entity_type)
    try:
        entity = registry.create_entity(entity_type, payload.entity)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return EntityResponse(type=entity_type, entity=entity)


@router.put(
    "/entities/{entity_type}/{identifier}",
    response_model=EntityResponse,
    dependencies=[Depends(require_api_key)],
)
async def update_entity(
    entity_type: str,
    identifier: str,
    payload: EntityPayload,
    context: APIContext = Depends(get_context),
) -> EntityResponse:
    registry = _get_registry(context)
    entity_type = _normalize_type(entity_type)
    try:
        entity = registry.update_entity(entity_type, identifier, payload.entity)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return EntityResponse(type=entity_type, entity=entity)


@router.delete(
    "/entities/{entity_type}/{identifier}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
async def delete_entity(
    entity_type: str,
    identifier: str,
    context: APIContext = Depends(get_context),
) -> None:
    registry = _get_registry(context)
    entity_type = _normalize_type(entity_type)
    try:
        registry.delete_entity(entity_type, identifier)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc



