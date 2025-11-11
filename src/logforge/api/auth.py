"""API key authentication helpers."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


def require_api_key(expected_key: str):
    """Return dependency enforcing Bearer token API key."""
    scheme = HTTPBearer(auto_error=False)

    async def dependency(credentials: HTTPAuthorizationCredentials = Security(scheme)) -> None:
        if not expected_key:
            return
        if credentials is None or credentials.credentials != expected_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
            )

    return Depends(dependency)
