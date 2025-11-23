from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Dict, Optional

import psutil

from logforge.core.config import GeneratorConfig
from logforge.core.generator import GeneratorLifecycleState, GeneratorRuntime
from logforge.core.frequency import FrequencyProfile
from logforge.core.telemetry import (
    EngineSnapshot,
    EngineTotals,
    GeneratorStatistics,
    GeneratorTelemetry,
    SystemTelemetry,
)
from logforge.outputs.base import OutputHandler
from logforge.utils.metrics import MetricsRegistry
from logforge.templates.engine import TemplateEngine

LOGGER = logging.getLogger(__name__)


class GenerationEngine:
    def __init__(
        self,
        template_engine: TemplateEngine,
        metrics: Optional[MetricsRegistry] = None,
        outputs: Optional[Dict[str, OutputHandler]] = None,
    ) -> None:
        self._template_engine = template_engine
        self._generators: Dict[str, GeneratorRuntime] = {}
        self._lock = asyncio.Lock()
        self._uptime_start = asyncio.get_event_loop().time()
        self._process = psutil.Process()
        self._metrics = metrics or MetricsRegistry()
        self._outputs = outputs or {}

    async def register_generator(self, config: GeneratorConfig) -> None:
        async with self._lock:
            if config.name in self._generators:
                raise ValueError(f"Generator {config.name} already registered.")
            generator_outputs = [
                self._outputs[output_name]
                for output_name in config.outputs
                if output_name in self._outputs
            ]
            missing = set(config.outputs) - set(self._outputs.keys())
            if missing:
                raise ValueError(f"Generator {config.name} references unknown outputs: {', '.join(missing)}")

            runtime = GeneratorRuntime(
                config=config,
                engine=self._template_engine,
                frequency=FrequencyProfile(
                    base_rate=config.frequency.base_rate,
                    variations=config.frequency.variation,
                ),
                outputs=generator_outputs,
            )
            self._generators[config.name] = runtime
            for handler in generator_outputs:
                self._metrics.set_backlog(handler.name, 0)
                self._metrics.set_last_emit(config.name, handler.name, 0.0)

    async def start_generator(self, name: str) -> None:
        async with self._lock:
            runtime = self._require_generator(name)
            if runtime.state in {GeneratorLifecycleState.RUNNING, GeneratorLifecycleState.STARTING}:
                LOGGER.debug("Generator %s already running.", name)
                return
            self._set_state(runtime, GeneratorLifecycleState.STARTING, reason="start_requested")
            runtime.stop_event.clear()
            runtime.task = asyncio.create_task(self._run_generator(runtime))

    async def stop_generator(self, name: str) -> None:
        async with self._lock:
            runtime = self._require_generator(name)
            if runtime.task is None:
                self._set_state(runtime, GeneratorLifecycleState.STOPPED, reason="stop_requested")
                return
            self._set_state(runtime, GeneratorLifecycleState.STOPPING, reason="stop_requested")
            runtime.stop_event.set()

        if runtime.task:
            await runtime.task
        async with self._lock:
            self._set_state(runtime, GeneratorLifecycleState.STOPPED, reason="stop_completed")
            runtime.task = None

    async def _run_generator(self, runtime: GeneratorRuntime) -> None:
        self._set_state(runtime, GeneratorLifecycleState.RUNNING, reason="generator_started")
        backoff = 1.0
        try:
            while not runtime.stop_event.is_set():
                current_rate = runtime.frequency.current_rate()
                sleep_interval = 1.0 / max(current_rate, 1)
                await asyncio.sleep(sleep_interval)
                success = await self._generate_event(runtime)
                if not success:
                    self._increment_errors(runtime)
                    self._set_state(runtime, GeneratorLifecycleState.DEGRADED, reason="output_failure")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 60)
                    continue
                backoff = 1.0
                self._set_state(runtime, GeneratorLifecycleState.RUNNING, reason="output_recovered")
        except Exception as exc:  # pragma: no cover - safety net
            LOGGER.exception("Generator %s failed: %s", runtime.config.name, exc)
            self._set_state(runtime, GeneratorLifecycleState.ERROR, reason=str(exc))
        finally:
            self._set_state(runtime, GeneratorLifecycleState.STOPPED, reason="generator_exit")

    async def _generate_event(self, runtime: GeneratorRuntime) -> bool:
        start = time.perf_counter()
        try:
            rendered = self._template_engine.render_event(runtime.config.template)
            duration = time.perf_counter() - start
            self._metrics.observe_template_render(runtime.config.name, duration)
            outputs_success = True
            if runtime.outputs:
                for handler in runtime.outputs:
                    if not await handler.emit(rendered, runtime.config.name):
                        outputs_success = False
            if outputs_success:
                self._increment_events(runtime, rendered)
                self._metrics.increment_events(runtime.config.name, "engine")
            return outputs_success
        except Exception as exc:
            duration = time.perf_counter() - start
            LOGGER.error("Failed to render event for %s: %s", runtime.config.name, exc)
            self._metrics.increment_errors(runtime.config.name, "render")
            self._metrics.observe_template_render(runtime.config.name, duration)
            self._increment_errors(runtime)
            return False

    def _require_generator(self, name: str) -> GeneratorRuntime:
        runtime = self._generators.get(name)
        if not runtime:
            raise ValueError(f"Generator {name} is not registered.")
        return runtime

    def snapshot(self) -> EngineSnapshot:
        totals = EngineTotals(
            total=len(self._generators),
            running=sum(1 for g in self._generators.values() if g.state == GeneratorLifecycleState.RUNNING),
            degraded=sum(1 for g in self._generators.values() if g.state == GeneratorLifecycleState.DEGRADED),
            error=sum(1 for g in self._generators.values() if g.state == GeneratorLifecycleState.ERROR),
        )
        self._metrics.record_generator_state(
            {
                "RUNNING": totals.running,
                "DEGRADED": totals.degraded,
                "ERROR": totals.error,
                "STOPPED": totals.total - (totals.running + totals.degraded + totals.error),
            }
        )
        generators = [runtime.to_telemetry() for runtime in self._generators.values()]
        uptime = int(asyncio.get_event_loop().time() - self._uptime_start)
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_mb = self._process.memory_info().rss / (1024 * 1024)
        thread_count = self._process.num_threads()
        self._metrics.set_system_metrics(cpu_percent, memory_mb, thread_count)
        system = SystemTelemetry(cpu_percent=cpu_percent, memory_mb=memory_mb, threads=thread_count)
        return EngineSnapshot(
            uptime_seconds=uptime,
            totals=totals,
            generators=generators,
            system=system,
        )

    def _set_state(
        self,
        runtime: GeneratorRuntime,
        new_state: GeneratorLifecycleState,
        reason: Optional[str] = None,
    ) -> None:
        previous = runtime.state
        if previous == new_state:
            return
        runtime.state = new_state
        payload = {
            "event": "generator_state_transition",
            "generator": runtime.config.name,
            "from": previous.value,
            "to": new_state.value,
        }
        if reason:
            payload["reason"] = reason
        LOGGER.info(json.dumps(payload))

    def _increment_events(self, runtime: GeneratorRuntime, last_event: Optional[str] = None) -> None:
        stats = runtime.statistics
        runtime.statistics = GeneratorStatistics(
            events_generated=stats.events_generated + 1,
            errors=stats.errors,
            uptime_seconds=stats.uptime_seconds,
            last_event=last_event or stats.last_event,
        )

    def _increment_errors(self, runtime: GeneratorRuntime) -> None:
        stats = runtime.statistics
        runtime.statistics = GeneratorStatistics(
            events_generated=stats.events_generated,
            errors=stats.errors + 1,
            uptime_seconds=stats.uptime_seconds,
            last_event=stats.last_event,
        )

