from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Request, status

from logforge.entities.registry import EntityRegistry
from logforge.entities.validator import EntityValidationError

router = APIRouter(prefix="/api/entities", tags=["entities"])


def get_registry(request: Request) -> EntityRegistry:
    return request.app.state.entity_registry


def ensure_entity_type(entity_type: str) -> str:
    allowed = {"users", "devices", "services"}
    if entity_type not in allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown entity type")
    return entity_type


@router.get("", response_model=Dict[str, object])
def summary(registry: EntityRegistry = Depends(get_registry)):
    return registry.summary()


@router.get("/export", response_model=Dict[str, object])
def export_entities(registry: EntityRegistry = Depends(get_registry)):
    return registry.export_bundle()


@router.post("/import", response_model=Dict[str, object])
def import_entities(
    payload: Dict = Body(...),
    replace: bool = False,
    registry: EntityRegistry = Depends(get_registry),
):
    try:
        bundle = registry.import_bundle(payload, replace=replace)
    except EntityValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return bundle


@router.get("/{entity_type}/{identifier}", response_model=Dict)
def get_entity(
    entity_type: str = Path(...),
    identifier: str = Path(...),
    registry: EntityRegistry = Depends(get_registry),
):
    entity_type = ensure_entity_type(entity_type)
    entity = registry.get_entity(entity_type, identifier)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return entity


@router.post("/{entity_type}", response_model=Dict[str, object], status_code=status.HTTP_201_CREATED)
def create_entity(
    entity_type: str = Path(...),
    payload: Dict = Body(...),
    registry: EntityRegistry = Depends(get_registry),
):
    entity_type = ensure_entity_type(entity_type)
    try:
        return registry.add_entity(entity_type, payload)
    except EntityValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{entity_type}/{identifier}", response_model=Dict[str, object])
def update_entity(
    entity_type: str = Path(...),
    identifier: str = Path(...),
    payload: Dict = Body(...),
    registry: EntityRegistry = Depends(get_registry),
):
    entity_type = ensure_entity_type(entity_type)
    try:
        return registry.update_entity(entity_type, identifier, payload)
    except EntityValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{entity_type}", response_model=List[Dict])
def list_entities(entity_type: str = Path(...), registry: EntityRegistry = Depends(get_registry)):
    entity_type = ensure_entity_type(entity_type)
    return registry.list_entities(entity_type)


@router.delete("/{entity_type}/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity(
    entity_type: str = Path(...),
    identifier: str = Path(...),
    registry: EntityRegistry = Depends(get_registry),
):
    entity_type = ensure_entity_type(entity_type)
    try:
        registry.delete_entity(entity_type, identifier)
    except EntityValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return None


