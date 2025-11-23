"""Community template API endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, status

from logforge.api.models import (
    CommunityTemplateInstallRequest,
    CommunityTemplateInstallResponse,
    CommunityTemplateSearchResponse,
    CommunityTemplateSummary,
)
from logforge.community.client import CommunityClient, CommunityClientConfig
from logforge.community.install import TemplateInstallError, install_template_archive

AuthDependency = Callable[..., Awaitable[None]]


def _community_client() -> CommunityClient:
    return CommunityClient(CommunityClientConfig())


def create_community_router(auth_dependency: AuthDependency | None) -> APIRouter:
    router = APIRouter(prefix="/community", tags=["community"])

    dependency = Depends(auth_dependency) if auth_dependency else None

    @router.get("/templates/search", response_model=CommunityTemplateSearchResponse)
    async def search_templates(
        query: str,
        limit: int = 20,
        _: None = dependency,
    ) -> CommunityTemplateSearchResponse:
        client = _community_client()
        results = client.search_templates(query, limit=limit)
        summaries = [CommunityTemplateSummary(**item) for item in results]
        return CommunityTemplateSearchResponse(results=summaries)

    @router.post("/templates/install", response_model=CommunityTemplateInstallResponse)
    async def install_template(
        payload: CommunityTemplateInstallRequest,
        _: None = dependency,
    ) -> CommunityTemplateInstallResponse:
        client = _community_client()
        try:
            archive = client.download_template(payload.template_id)
            installed_path = install_template_archive(
                payload.template_id,
                archive,
                destination=Path(payload.destination) if payload.destination else None,
                force=payload.force,
            )
        except TemplateInstallError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        return CommunityTemplateInstallResponse(
            template_id=payload.template_id,
            path=str(installed_path),
        )

    return router


__all__ = ["create_community_router"]
