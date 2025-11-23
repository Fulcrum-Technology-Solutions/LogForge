from __future__ import annotations

import base64
import io
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from logforge.api.auth import get_context, require_api_key
from logforge.api.context import APIContext
from logforge.api.models import (
    TemplateCollection,
    TemplateDetail,
    TemplateDiffResponse,
    TemplateInstallRequest,
    TemplateSummary,
    TemplateValidateRequest,
)
from logforge.templates.engine import TemplateEngine
from logforge.templates.manager import TemplateManager

router = APIRouter()


def _get_template_engine(context: APIContext) -> TemplateEngine:
    engine = getattr(context, "template_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Template engine unavailable.",
        )
    return engine


def _get_template_manager(context: APIContext) -> TemplateManager:
    manager = getattr(context, "template_manager", None)
    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Template manager unavailable.",
        )
    return manager


def _get_community_client(context: APIContext):
    client = getattr(context, "community_client", None)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Community client unavailable.",
        )
    return client


@router.get("/templates", dependencies=[Depends(require_api_key)], response_model=TemplateCollection)
async def list_templates(
    context: APIContext = Depends(get_context),
    query: Optional[str] = Query(default=None, description="Filter templates by substring."),
) -> TemplateCollection:
    _get_template_engine(context)  # ensure engine available
    manager = _get_template_manager(context)
    payload = manager.search(query)
    summaries = [
        TemplateSummary(
            id=item["id"],
            locations=item.get("locations", []),
            name=item.get("name"),
            vendor=item.get("vendor"),
            product=item.get("product"),
            data_source=item.get("data_source"),
            version=item.get("version"),
            format=item.get("format"),
        )
        for item in payload
    ]
    return TemplateCollection(templates=summaries)


@router.get(
    "/templates/search",
    dependencies=[Depends(require_api_key)],
)
async def search_templates(
    query: Optional[str] = Query(default=None, description="Search query."),
    context: APIContext = Depends(get_context),
) -> dict:
    client = _get_community_client(context)
    results = client.search_templates(query=query)
    return {"templates": results}


@router.post(
    "/templates/install",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
async def install_template(
    request: TemplateInstallRequest,
    context: APIContext = Depends(get_context),
) -> None:
    manager = _get_template_manager(context)
    client = _get_community_client(context)
    if request.package:
        package_bytes = base64.b64decode(request.package)
    elif request.template_id:
        package_bytes = client.download_template(request.template_id, url=request.url)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="template_id or package required.")
    manager.install_package(package_bytes)


@router.post(
    "/templates/{template_id:path}/customize",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_api_key)],
)
async def customize_template(
    template_id: str,
    context: APIContext = Depends(get_context),
) -> dict:
    manager = _get_template_manager(context)
    try:
        path = manager.customize(template_id)
    except (FileNotFoundError, FileExistsError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"path": str(path)}


@router.delete(
    "/templates/{template_id:path}/custom",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
async def revert_template(template_id: str, context: APIContext = Depends(get_context)) -> None:
    manager = _get_template_manager(context)
    try:
        manager.revert(template_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/templates/{template_id:path}/diff",
    dependencies=[Depends(require_api_key)],
    response_model=TemplateDiffResponse,
)
async def diff_template(template_id: str, context: APIContext = Depends(get_context)) -> TemplateDiffResponse:
    manager = _get_template_manager(context)
    try:
        diff = manager.diff(template_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TemplateDiffResponse(diff=diff)


@router.post(
    "/templates/{template_id:path}/merge",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
async def merge_template(template_id: str, context: APIContext = Depends(get_context)) -> None:
    manager = _get_template_manager(context)
    try:
        manager.merge(template_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/templates/{template_id:path}",
    dependencies=[Depends(require_api_key)],
    response_model=TemplateDetail,
)
async def get_template(template_id: str, context: APIContext = Depends(get_context)) -> TemplateDetail:
    engine = _get_template_engine(context)
    try:
        detail = engine.get_template_detail(template_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TemplateDetail(
        id=detail["id"],
        metadata=detail["metadata"],
        locations=detail.get("locations", []),
    )


@router.post(
    "/templates/validate",
    dependencies=[Depends(require_api_key)],
)
async def validate_template(
    request: TemplateValidateRequest,
    context: APIContext = Depends(get_context),
) -> dict:
    manager = _get_template_manager(context)
    data = base64.b64decode(request.archive)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            archive.extractall(tmp_path)
        candidate = tmp_path
        metadata_files = list(candidate.rglob("metadata.yaml"))
        if metadata_files:
            candidate = metadata_files[0].parent
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="metadata.yaml not found in archive.",
            )
        metadata = manager.validate_directory(candidate)
    return {"valid": True, "metadata": metadata}

