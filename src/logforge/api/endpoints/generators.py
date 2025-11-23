"""Generator management endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, status

from logforge.api.models import GeneratorStatus

if TYPE_CHECKING:
    from logforge.api.server import APIDependencies

AuthDependency = Callable[..., Awaitable[None]]


def create_generators_router(
    deps: "APIDependencies",
    auth_dependency: AuthDependency | None,
) -> APIRouter:
    router = APIRouter(prefix="/generators", tags=["generators"])

    dependency = Depends(auth_dependency) if auth_dependency else None

    @router.get("", response_model=list[GeneratorStatus])
    async def list_generators(_: None = dependency) -> list[GeneratorStatus]:
        return [GeneratorStatus(**data) for data in deps.list_generators()]

    @router.get("/{name}", response_model=GeneratorStatus)
    async def get_generator(name: str, _: None = dependency) -> GeneratorStatus:
        data = deps.get_generator(name)
        if data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generator not found")
        return GeneratorStatus(**data)

    @router.post("/{name}/start", response_model=GeneratorStatus)
    async def start_generator(name: str, _: None = dependency) -> GeneratorStatus:
        data = deps.start_generator(name)
        return GeneratorStatus(**data)

    @router.post("/{name}/stop", response_model=GeneratorStatus)
    async def stop_generator(name: str, _: None = dependency) -> GeneratorStatus:
        data = deps.stop_generator(name)
        return GeneratorStatus(**data)

    @router.post("/{name}/restart", response_model=GeneratorStatus)
    async def restart_generator(name: str, _: None = dependency) -> GeneratorStatus:
        data = deps.restart_generator(name)
        return GeneratorStatus(**data)

    return router


__all__ = ["create_generators_router"]
