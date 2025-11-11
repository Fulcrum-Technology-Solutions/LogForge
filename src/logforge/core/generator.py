from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from logforge.core.frequency import FrequencyController
from logforge.templates.manager import TemplateManager
from logforge.outputs.manager import OutputManager
from logforge.outputs.base import OutputHandler


class GeneratorState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


@dataclass
class GeneratorStatistics:
    events_generated: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    start_time: Optional[float] = None


class Generator:
    def __init__(
        self,
        name: str,
        config: Dict,
        template_manager: TemplateManager,
        output_manager: OutputManager,
        *,
        max_events: Optional[int] = None,
    ) -> None:
        self.name = name
        self.config = config
        self.template_manager = template_manager
        self.output_manager = output_manager
        self.frequency = FrequencyController(config.get("frequency", {"base_rate": 1}))
        self.outputs: List[OutputHandler] = []
        self.state = GeneratorState.STOPPED
        self.stats = GeneratorStatistics()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._max_events = max_events

    def start(self) -> None:
        if self.state in {GeneratorState.RUNNING, GeneratorState.STARTING}:
            return
        self._prepare_outputs()
        self.state = GeneratorState.STARTING
        self._stop_event.clear()
        self.stats.start_time = time.time()
        self._thread = threading.Thread(target=self._run_loop, name=f"generator-{self.name}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self.state in {GeneratorState.STOPPED, GeneratorState.STOPPING}:
            return
        self.state = GeneratorState.STOPPING
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        for handler in self.outputs:
            handler.close()
        self.state = GeneratorState.STOPPED

    def _prepare_outputs(self) -> None:
        self.outputs = self.output_manager.create_handlers(self.name, self.config.get("outputs", []))

    def _run_loop(self) -> None:
        try:
            self.state = GeneratorState.RUNNING
            generated = 0
            while not self._stop_event.is_set():
                rate = self.frequency.current_rate()
                delay = 1.0 / rate if rate > 0 else 1.0

                try:
                    payload = self.template_manager.render(self.config["template"])
                    for handler in self.outputs:
                        handler.write(payload)
                    self.stats.events_generated += 1
                    generated += 1
                except Exception as exc:  # pragma: no cover - runtime issues
                    self.state = GeneratorState.ERROR
                    self.stats.errors += 1
                    self.stats.last_error = str(exc)
                    break

                if self._max_events is not None and generated >= self._max_events:
                    break

                time.sleep(delay)
        finally:
            if self.state not in {GeneratorState.ERROR, GeneratorState.STOPPING}:
                self.state = GeneratorState.STOPPED

    def snapshot(self) -> Dict[str, object]:
        uptime = None
        if self.stats.start_time:
            uptime = int(time.time() - self.stats.start_time)
        return {
            "name": self.name,
            "template": self.config.get("template"),
            "state": self.state.value,
            "events_generated": self.stats.events_generated,
            "errors": self.stats.errors,
            "last_error": self.stats.last_error,
            "outputs": self.config.get("outputs", []),
            "uptime": uptime,
        }
