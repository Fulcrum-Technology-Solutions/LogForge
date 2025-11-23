"""Health endpoint router."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from logforge.api.models import HealthResponse, StatusResponse

if TYPE_CHECKING:
    from logforge.api.server import APIDependencies


def create_health_router(deps: "APIDependencies", auth_dependency):
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse, tags=["health"])
    async def health(_: None = Depends(auth_dependency)) -> HealthResponse:
        return deps.get_health()

    @router.get("/status", response_model=StatusResponse, tags=["health"])
    async def status(_: None = Depends(auth_dependency)) -> StatusResponse:
        return deps.get_status()

    return router


__all__ = ["create_health_router"]
