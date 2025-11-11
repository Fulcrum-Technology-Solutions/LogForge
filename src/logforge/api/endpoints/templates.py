from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status

from logforge.templates.manager import TemplateManager
from logforge.templates.validator import TemplateValidationError

router = APIRouter(prefix="/api/templates", tags=["templates"])


def get_manager(request: Request) -> TemplateManager:
    return request.app.state.template_manager


@router.get("", response_model=List[Dict[str, object]])
def list_templates(
    manager: TemplateManager = Depends(get_manager),
) -> List[Dict[str, object]]:
    return manager.list_templates()


@router.get("/search", response_model=List[Dict[str, object]])
def search_templates(
    q: Optional[str] = Query(default=None),
    vendor: Optional[str] = Query(default=None),
    manager: TemplateManager = Depends(get_manager),
) -> List[Dict[str, object]]:
    return manager.search_remote(query=q, vendor=vendor)


@router.get("/{template_id:path}", response_model=Dict[str, object])
def template_info(template_id: str, manager: TemplateManager = Depends(get_manager)) -> Dict[str, object]:
    try:
        return manager.template_info(template_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{template_id:path}/validate", response_model=Dict[str, object])
def validate_template(template_id: str, manager: TemplateManager = Depends(get_manager)) -> Dict[str, object]:
    try:
        return manager.validate(template_id)
    except TemplateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/validate", response_model=Dict[str, object])
def validate_path(payload: Dict[str, str] = Body(...), manager: TemplateManager = Depends(get_manager)) -> Dict[str, object]:
    path_str = payload.get("path")
    if not path_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="path field required")
    try:
        return manager.validate_path(Path(path_str))
    except (TemplateValidationError, FileNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/install", response_model=Dict[str, object])
def install_template(
    payload: Dict[str, str] = Body(...),
    manager: TemplateManager = Depends(get_manager),
) -> Dict[str, object]:
    template_id = payload.get("template_id")
    if not template_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="template_id required")
    try:
        return manager.install_from_remote(template_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{template_id:path}/customize", response_model=Dict[str, object])
def customize_template(template_id: str, manager: TemplateManager = Depends(get_manager)) -> Dict[str, object]:
    try:
        manager.customize(template_id)
        return manager.template_info(template_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{template_id:path}/diff", response_model=Dict[str, str])
def diff_template(template_id: str, manager: TemplateManager = Depends(get_manager)) -> Dict[str, str]:
    try:
        diff_text = manager.diff(template_id)
        return {"template_id": template_id, "diff": diff_text}
    except TemplateValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{template_id:path}/custom", status_code=status.HTTP_204_NO_CONTENT)
def revert_template(template_id: str, manager: TemplateManager = Depends(get_manager)) -> None:
    try:
        manager.revert(template_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
