"""Output handler API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, status

from logforge.api.models import OutputListResponse, OutputSummary

if TYPE_CHECKING:
    from logforge.api.server import APIDependencies

AuthDependency = Callable[..., Awaitable[None]]


def create_outputs_router(
    deps: "APIDependencies",
    auth_dependency: AuthDependency | None,
) -> APIRouter:
    router = APIRouter(prefix="/outputs", tags=["outputs"])

    dependency = Depends(auth_dependency) if auth_dependency else None

    @router.get("", response_model=OutputListResponse)
    async def list_outputs(_: None = dependency) -> OutputListResponse:
        outputs = [OutputSummary(**item) for item in deps.list_outputs()]
        return OutputListResponse(outputs=outputs)

    @router.get("/{name}", response_model=OutputSummary)
    async def get_output(name: str, _: None = dependency) -> OutputSummary:
        data = deps.get_output(name)
        if data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output not found")
        return OutputSummary(**data)

    return router


__all__ = ["create_outputs_router"]
