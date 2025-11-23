"""API authentication utilities."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


def build_auth_dependency(enabled: bool, api_key: str | None):
    """Return a FastAPI dependency enforcing optional API key auth."""

    security = HTTPBearer(auto_error=False)

    async def dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> None:
        if not enabled:
            return None
        if not credentials or credentials.credentials != api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key.",
            )
        return None

    return dependency


__all__ = ["build_auth_dependency"]
