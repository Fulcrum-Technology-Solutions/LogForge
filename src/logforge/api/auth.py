"""API key authentication helpers."""

from __future__ import annotations

import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from logforge.core.config import APIAuthConfig, LogForgeConfig


def ensure_api_key(settings: APIAuthConfig) -> APIAuthConfig:
    """Populate missing API key when auth is enabled."""
    if settings.enabled and not settings.key:
        settings.key = secrets.token_urlsafe(32)
    return settings


class APIKeyAuth:
    """Reusable API key validator for CLI and request hooks."""

    def __init__(self, settings: APIAuthConfig) -> None:
        self._settings = ensure_api_key(settings)

    def __call__(self, authorization: Optional[str] = None) -> None:
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


def _build_dependency(settings: APIAuthConfig):
    scheme = HTTPBearer(auto_error=False)
    ensured = ensure_api_key(settings)

    async def dependency(credentials: HTTPAuthorizationCredentials = Security(scheme)) -> None:
        if not ensured.enabled:
            return
        if credentials is None or credentials.credentials != ensured.key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
            )

    return dependency


def get_auth_dependency(config: LogForgeConfig) -> Depends:
    """Return dependency enforcing Bearer token API key based on config."""
    return Depends(_build_dependency(config.api.auth))
