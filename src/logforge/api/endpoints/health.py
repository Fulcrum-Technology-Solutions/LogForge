from __future__ import annotations

import time
from fastapi import APIRouter, Depends
from starlette.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from logforge.api.auth import get_context, require_api_key
from logforge.api.context import APIContext
from logforge.api.models import HealthResponse, StatusResponse, EngineTotalsModel, GeneratorStatusModel, GeneratorFrequencyModel, GeneratorStatisticsModel, SystemStatusModel
from logforge.core.telemetry import EngineSnapshot, GeneratorTelemetry


router = APIRouter()
_api_start_time = time.time()


def _build_health_response(snapshot: EngineSnapshot) -> HealthResponse:
    totals = EngineTotalsModel(
        total=snapshot.totals.total,
        running=snapshot.totals.running,
        degraded=snapshot.totals.degraded,
        error=snapshot.totals.error,
    )
    uptime = int(time.time() - _api_start_time)
    return HealthResponse(
        status="healthy" if snapshot.totals.error == 0 else "degraded",
        uptime=uptime,
        generators=totals,
        entity_registry=snapshot.entity_registry_status,
        template_cache=snapshot.template_cache_status,
    )


def _convert_generator(generator: GeneratorTelemetry) -> GeneratorStatusModel:
    return GeneratorStatusModel(
        name=generator.name,
        template=generator.template,
        enabled=generator.enabled,
        state=generator.state.value,
        frequency=GeneratorFrequencyModel(
            base_rate=generator.frequency_base_rate,
            current_rate=generator.frequency_current_rate,
        ),
        outputs=generator.outputs,
        statistics=GeneratorStatisticsModel(
            events_generated=generator.statistics.events_generated,
            errors=generator.statistics.errors,
            uptime=generator.statistics.uptime_seconds,
            last_event=generator.statistics.last_event,
        ),
    )


@router.get("/health", response_model=HealthResponse, dependencies=[Depends(require_api_key)])
async def get_health(context: APIContext = Depends(get_context)) -> HealthResponse:
    snapshot = context.telemetry.snapshot()
    return _build_health_response(snapshot)


@router.get("/status", response_model=StatusResponse, dependencies=[Depends(require_api_key)])
async def get_status(context: APIContext = Depends(get_context)) -> StatusResponse:
    snapshot = context.telemetry.snapshot()
    uptime = int(time.time() - _api_start_time)
    generators = [_convert_generator(gen) for gen in snapshot.generators]
    system = SystemStatusModel(
        cpu_percent=snapshot.system.cpu_percent,
        memory_mb=snapshot.system.memory_mb,
        threads=snapshot.system.threads,
    )
    return StatusResponse(
        uptime=uptime,
        version=context.config.version if hasattr(context.config, "version") else "1.0",
        generators=generators,
        system=system,
    )


@router.get("/metrics", dependencies=[Depends(require_api_key)])
async def get_metrics(context: APIContext = Depends(get_context)) -> Response:
    data = generate_latest(context.metrics.registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

