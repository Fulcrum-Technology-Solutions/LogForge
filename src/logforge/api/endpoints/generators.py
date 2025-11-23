from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from logforge.api.auth import get_context, require_api_key
from logforge.api.context import APIContext
from logforge.api.models import (
    GeneratorControlResponse,
    StatusResponse,
    GeneratorStatusModel,
    GeneratorFrequencyModel,
    GeneratorStatisticsModel,
    SystemStatusModel,
)
from logforge.core.engine import GenerationEngine
from logforge.core.telemetry import GeneratorTelemetry

router = APIRouter()


def _get_engine(context: APIContext) -> GenerationEngine:
    engine = getattr(context, "engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Generation engine unavailable.",
        )
    return engine


@router.get("/generators", dependencies=[Depends(require_api_key)], response_model=StatusResponse)
async def list_generators(context: APIContext = Depends(get_context)) -> StatusResponse:
    engine = _get_engine(context)
    snapshot = engine.snapshot()
    generators = [_convert_generator(gen) for gen in snapshot.generators]
    system = SystemStatusModel(
        cpu_percent=snapshot.system.cpu_percent,
        memory_mb=snapshot.system.memory_mb,
        threads=snapshot.system.threads,
    )
    return StatusResponse(
        uptime=snapshot.uptime_seconds,
        version=context.config.version,
        generators=generators,
        system=system,
    )


@router.post(
    "/generators/{name}/start",
    response_model=GeneratorControlResponse,
    dependencies=[Depends(require_api_key)],
)
async def start_generator(name: str, context: APIContext = Depends(get_context)) -> GeneratorControlResponse:
    engine = _get_engine(context)
    try:
        await engine.start_generator(name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return GeneratorControlResponse(name=name, state="STARTING", message="Generator starting")


@router.post(
    "/generators/{name}/stop",
    response_model=GeneratorControlResponse,
    dependencies=[Depends(require_api_key)],
)
async def stop_generator(name: str, context: APIContext = Depends(get_context)) -> GeneratorControlResponse:
    engine = _get_engine(context)
    try:
        await engine.stop_generator(name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return GeneratorControlResponse(name=name, state="STOPPED", message="Generator stopping")


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

