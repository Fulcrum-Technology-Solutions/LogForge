"""Generator runtime implementation."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from logforge.core.config_schema import GeneratorConfig
from logforge.core.frequency import FrequencyController
from logforge.outputs.base import BaseOutput, Metadata
from logforge.utils.metrics import (
    events_generated_total,
    generator_errors_total,
    generators_running,
    template_render_seconds,
)


class TemplateRendererProtocol(Protocol):
    def render(
        self,
        template_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:  # pragma: no cover - protocol
        ...


class GeneratorState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


@dataclass
class GeneratorStatisticsSnapshot:
    events_generated: int = 0
    errors: int = 0
    last_event: Optional[str] = None
    started_at: Optional[float] = None

    def uptime(self) -> float:
        if self.started_at is None:
            return 0.0
        return max(0.0, time.monotonic() - self.started_at)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "events_generated": self.events_generated,
            "errors": self.errors,
            "uptime": self.uptime(),
            "last_event": self.last_event,
        }


@dataclass
class GeneratorSnapshot:
    name: str
    state: GeneratorState
    template: str
    enabled: bool
    outputs: List[str]
    frequency: Dict[str, Any]
    statistics: Dict[str, Any]


class Generator:
    """Background event generator built from configuration."""

    def __init__(
        self,
        config: GeneratorConfig,
        renderer: TemplateRendererProtocol,
        outputs: List[BaseOutput],
        frequency: FrequencyController,
        *,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config = config
        self.renderer = renderer
        self.outputs = outputs
        self.frequency = frequency
        self.state = GeneratorState.STOPPED
        self.stats = GeneratorStatisticsSnapshot()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._logger = logger or logging.getLogger(f"logforge.generator.{config.name}")

    def start(self) -> None:
        with self._lock:
            if self.state in {GeneratorState.RUNNING, GeneratorState.STARTING}:
                return
            self._stop_event.clear()
            self.state = GeneratorState.STARTING
            self.stats.started_at = time.monotonic()
            self._thread = threading.Thread(
                target=self._run_loop,
                name=f"generator-{self.config.name}",
                daemon=True,
            )
            self._thread.start()
            # Update metrics when starting
            self._update_state_metrics()

    def stop(self, timeout: float = 5.0) -> None:
        with self._lock:
            if self._thread is None:
                self.state = GeneratorState.STOPPED
                self._update_state_metrics()
                return
            self._stop_event.set()
            self._thread.join(timeout=timeout)
            self._thread = None
            self.state = GeneratorState.STOPPED
            self._update_state_metrics()

    def restart(self) -> None:
        self.stop()
        self.start()

    def _is_transient_error(self, exc: Exception) -> bool:
        """Determine if an error is transient and should be retried."""
        error_type = type(exc).__name__
        error_msg = str(exc).lower()

        # Configuration errors are not transient
        if "not found" in error_msg and "template" in error_msg:
            return False
        if "validation" in error_msg or "invalid" in error_msg:
            return False
        if "syntax" in error_msg:
            return False

        # Network/IO errors are typically transient
        if any(keyword in error_type.lower() for keyword in ["timeout", "connection", "network"]):
            return True
        if any(keyword in error_msg for keyword in ["timeout", "connection", "network", "temporary"]):
            return True

        # Default: treat as transient (can be retried)
        return True

    def _run_loop(self) -> None:
        self.state = GeneratorState.RUNNING
        self._update_state_metrics()
        consecutive_errors = 0
        max_consecutive_errors = 10

        while not self._stop_event.is_set():
            rate = self.frequency.current_rate()
            pause = 1.0 / max(rate, 1)
            iteration_started = time.monotonic()
            try:
                self.generate_once()
                consecutive_errors = 0  # Reset on success
                if self.state == GeneratorState.DEGRADED:
                    # Recovered from degraded state
                    self._logger.info("Generator '%s' recovered from degraded state", self.config.name)
                    self.state = GeneratorState.RUNNING
                    self._update_state_metrics()
            except Exception as exc:  # pragma: no cover - error path
                consecutive_errors += 1
                is_transient = self._is_transient_error(exc)
                error_type = type(exc).__name__
                generator_errors_total.labels(generator=self.config.name, error_type=error_type).inc()

                if not is_transient:
                    # Configuration error - stop generator
                    self._logger.error(
                        "Generator '%s' encountered configuration error: %s",
                        self.config.name,
                        exc,
                    )
                    self.state = GeneratorState.ERROR
                    self._update_state_metrics()
                    break
                elif consecutive_errors >= max_consecutive_errors:
                    # Too many consecutive errors - enter ERROR state
                    self._logger.error(
                        "Generator '%s' exceeded max consecutive errors (%d), entering ERROR state",
                        self.config.name,
                        max_consecutive_errors,
                    )
                    self.state = GeneratorState.ERROR
                    self._update_state_metrics()
                    break
                else:
                    # Transient error - continue but mark as degraded
                    self._logger.warning(
                        "Generator '%s' transient error (%d/%d): %s",
                        self.config.name,
                        consecutive_errors,
                        max_consecutive_errors,
                        exc,
                    )
                    if self.state == GeneratorState.RUNNING:
                        self.state = GeneratorState.DEGRADED
                        self._update_state_metrics()

            elapsed = time.monotonic() - iteration_started
            remaining = max(0.0, pause - elapsed)
            self._stop_event.wait(remaining)
        if self.state not in {GeneratorState.ERROR, GeneratorState.DEGRADED}:
            self.state = GeneratorState.STOPPED
            self._update_state_metrics()

    def generate_once(self) -> None:
        try:
            with template_render_seconds.labels(
                generator=self.config.name, template=self.config.template
            ).time():
                event = self.renderer.render(
                    self.config.template,
                    {"generator": self.config.name},
                )
        except Exception as exc:
            # Template rendering errors are usually configuration issues
            self.stats.errors += 1
            error_type = type(exc).__name__
            generator_errors_total.labels(generator=self.config.name, error_type=error_type).inc()
            raise

        timestamp = datetime.now(timezone.utc).isoformat()
        metadata: Metadata = {
            "generator": self.config.name,
            "timestamp": timestamp,
        }

        output_errors = 0
        for output in self.outputs:
            try:
                output.emit(event, metadata)
            except Exception as exc:  # pragma: no cover - error path
                output_errors += 1
                self._logger.warning(
                    "Generator '%s' output '%s' failed: %s",
                    self.config.name,
                    output.name,
                    exc,
                )
                # Don't raise - continue to other outputs
                # The error will be handled by the retry logic in the output handler

        if output_errors > 0:
            self.stats.errors += output_errors
            # If all outputs failed, this is a problem
            if output_errors == len(self.outputs):
                raise RuntimeError(f"All outputs failed for generator '{self.config.name}'")

        self.stats.events_generated += 1
        self.stats.last_event = timestamp
        events_generated_total.labels(generator=self.config.name).inc()

    def _update_state_metrics(self) -> None:
        """Update generators_running gauge based on current state."""
        # Reset all states to 0 for this generator (we track globally)
        # This is a simplified approach - in a more complex system we'd track per-generator
        # For now, we rely on the engine to update the global gauge
        pass

    def snapshot(self) -> GeneratorSnapshot:
        return GeneratorSnapshot(
            name=self.config.name,
            state=self.state,
            template=self.config.template,
            enabled=self.config.enabled,
            outputs=[output.name for output in self.outputs],
            frequency={
                "base_rate": self.frequency.config.base_rate,
            },
            statistics=self.stats.to_dict(),
        )


__all__ = ["Generator", "GeneratorState", "GeneratorSnapshot", "GeneratorStatisticsSnapshot"]
