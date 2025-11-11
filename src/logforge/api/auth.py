from __future__ import annotations

import secrets
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from logforge.core.config import ApiAuthSettings, LogForgeConfig


def ensure_api_key(settings: ApiAuthSettings) -> ApiAuthSettings:
    if settings.enabled and not settings.key:
        settings.key = secrets.token_urlsafe(32)
    return settings


class APIKeyAuth:
    def __init__(self, settings: ApiAuthSettings) -> None:
        self._settings = ensure_api_key(settings)

    def __call__(self, authorization: Optional[str] = Header(default=None)) -> None:
        if not self._settings.enabled:
            return
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key",
            )
        token = authorization.split(" ", 1)[1]
        if token != self._settings.key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )


def get_auth_dependency(config: LogForgeConfig) -> Depends:
    return Depends(APIKeyAuth(config.api.auth))
