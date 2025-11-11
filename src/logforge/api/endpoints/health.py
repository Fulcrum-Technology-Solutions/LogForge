"""Health and status endpoints."""

from __future__ import annotations

import time
from typing import Dict, List

import psutil
from fastapi import APIRouter, Request

router = APIRouter()


def _uptime_seconds(start_time: float) -> int:
    return int(time.time() - start_time)


def _summarize_generators(generators: List[Dict[str, str]]) -> Dict[str, int]:
    summary = {"total": 0, "running": 0, "degraded": 0, "error": 0}
    for generator in generators:
        summary["total"] += 1
        state = generator.get("state", "").upper()
        if state == "RUNNING":
            summary["running"] += 1
        elif state == "DEGRADED":
            summary["degraded"] += 1
        elif state == "ERROR":
            summary["error"] += 1
    return summary


@router.get("/health")
async def health(request: Request) -> Dict[str, object]:
    app = request.app
    start_time = getattr(app.state, "start_time", time.time())
    generators = app.state.get_generators()  # type: ignore[attr-defined]
    summary = _summarize_generators(generators)

    entity_health = "healthy"
    template_cache_health = "healthy"
    if hasattr(app.state, "entity_registry_health"):
        entity_health = app.state.entity_registry_health()
    if hasattr(app.state, "template_cache_health"):
        template_cache_health = app.state.template_cache_health()

    return {
        "status": "healthy" if summary["error"] == 0 else "degraded",
        "uptime": _uptime_seconds(start_time),
        "generators": summary,
        "entity_registry": entity_health,
        "template_cache": template_cache_health,
    }


@router.get("/status")
async def status(request: Request) -> Dict[str, object]:
    app = request.app
    start_time = getattr(app.state, "start_time", time.time())
    config = getattr(app.state, "config", None)
    generators = app.state.get_generators()  # type: ignore[attr-defined]

    process = psutil.Process()
    with process.oneshot():
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_mb = process.memory_info().rss / (1024 * 1024)
        threads = process.num_threads()

    return {
        "uptime": _uptime_seconds(start_time),
        "version": getattr(config, "version", "unknown"),
        "generators": generators,
        "system": {
            "cpu_percent": round(cpu_percent, 2),
            "memory_mb": round(memory_mb, 2),
            "threads": threads,
        },
    }
