"""Templates API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, status

from logforge.api.models import TemplateDetailResponse, TemplateListResponse, TemplateSummary

if TYPE_CHECKING:
    from logforge.api.server import APIDependencies

AuthDependency = Callable[..., Awaitable[None]]


def create_templates_router(
    deps: "APIDependencies",
    auth_dependency: AuthDependency | None,
) -> APIRouter:
    router = APIRouter(prefix="/templates", tags=["templates"])

    @router.get("", response_model=TemplateListResponse)
    async def list_templates() -> TemplateListResponse:
        summaries = [TemplateSummary(**item) for item in deps.list_templates()]
        return TemplateListResponse(templates=summaries)

    @router.get("/{template_id:path}", response_model=TemplateDetailResponse)
    async def get_template(
        template_id: str,
    ) -> TemplateDetailResponse:
        data = deps.get_template(template_id)
        if data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return TemplateDetailResponse(**data)

    if auth_dependency is not None:
        router.dependencies.append(Depends(auth_dependency))

    return router


__all__ = ["create_templates_router"]
