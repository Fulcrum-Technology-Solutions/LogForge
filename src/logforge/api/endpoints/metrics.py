"""Metrics endpoint router."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Response

if TYPE_CHECKING:
    from logforge.api.server import APIDependencies


def create_metrics_router(deps: "APIDependencies", auth_dependency):
    router = APIRouter()

    @router.get("/metrics", tags=["metrics"], response_class=Response)
    async def metrics(_: None = Depends(auth_dependency)) -> Response:
        data = deps.get_metrics()
        return Response(content=data, media_type="text/plain; version=0.0.4")

    return router


__all__ = ["create_metrics_router"]
