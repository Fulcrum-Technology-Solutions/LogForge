from __future__ import annotations

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, Request

from logforge.core.config import LogForgeConfig

router = APIRouter(prefix="/api", tags=["system"])


def get_config(request: Request) -> LogForgeConfig:
    return request.app.state.config


@router.get("/health")
def health(request: Request) -> Dict[str, Any]:
    config: LogForgeConfig = get_config(request)
    uptime = time.time() - request.app.state.start_time
    return {
        "status": "healthy",
        "uptime": int(uptime),
        "version": config.version,
        "generators": {
            "total": len(config.generators),
            "running": 0,
            "degraded": 0,
            "error": 0,
        },
        "entity_registry": "unknown",
        "template_cache": "unknown",
    }


@router.get("/status")
def status(request: Request, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    request.app.state.auth_guard(authorization)
    config: LogForgeConfig = get_config(request)
    uptime = time.time() - request.app.state.start_time
    return {
        "uptime": int(uptime),
        "version": config.version,
        "generators": [],
        "system": request.app.state.system_provider(),
    }
