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
    templates = request.app.state.template_manager.list_templates()
    engine = request.app.state.generation_engine
    generator_snapshots = engine.list_generators()
    running = sum(1 for g in generator_snapshots if g["state"] == "RUNNING")
    degraded = sum(1 for g in generator_snapshots if g["state"] == "DEGRADED")
    errored = sum(1 for g in generator_snapshots if g["state"] == "ERROR")
    return {
        "status": "healthy",
        "uptime": int(uptime),
        "version": config.version,
        "generators": {
            "total": len(config.generators),
            "running": running,
            "degraded": degraded,
            "error": errored,
        },
        "entity_registry": "healthy",
        "template_cache": {"templates": len(templates)},
    }


@router.get("/status")
def status(request: Request, authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    request.app.state.auth_guard(authorization)
    config: LogForgeConfig = get_config(request)
    uptime = time.time() - request.app.state.start_time
    return {
        "uptime": int(uptime),
        "version": config.version,
        "generators": request.app.state.generation_engine.list_generators(),
        "system": request.app.state.system_provider(),
        "templates": request.app.state.template_manager.list_templates(),
    }
