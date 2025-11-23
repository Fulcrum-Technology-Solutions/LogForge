from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from logforge.api.context import APIContext
from logforge.core.config import APIConfig

AUTH_HEADER = "Authorization"
BEARER_PREFIX = "Bearer "


def get_context(request: Request) -> APIContext:
    context = getattr(request.app.state, "context", None)
    if context is None:
        raise RuntimeError("API context not configured on application state.")
    return context


def get_api_config(context: APIContext = Depends(get_context)) -> APIConfig:
    return context.config.api


def require_api_key(
    request: Request,
    api_config: APIConfig = Depends(get_api_config),
) -> None:
    if not api_config.auth.enabled:
        return

    header_value = request.headers.get(AUTH_HEADER)
    if not header_value or not header_value.startswith(BEARER_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    token = header_value[len(BEARER_PREFIX) :].strip()
    if not api_config.auth.key or token != api_config.auth.key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

