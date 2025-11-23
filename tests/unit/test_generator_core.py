from __future__ import annotations

import time
from dataclasses import dataclass

from logforge.core.config_schema import FrequencyConfig, GeneratorConfig
from logforge.core.frequency import FrequencyController
from logforge.core.generator import Generator, GeneratorState
from logforge.outputs.base import CapturingOutput


@dataclass
class DummyRenderer:
    template_id: str = ""

    def render(self, template_id: str, context=None) -> str:
        return f"{template_id}|{context['generator']}"


def make_generator(name: str = "example") -> Generator:
    config = GeneratorConfig(
        name=name,
        template="vendor/product/example",
        enabled=True,
        outputs=["capture"],
        frequency=FrequencyConfig(base_rate=5),
    )
    renderer = DummyRenderer()
    output = CapturingOutput("capture")
    frequency = FrequencyController(config.frequency)
    generator = Generator(config, renderer, [output], frequency)
    return generator


def test_generator_generate_once_records_stats() -> None:
    generator = make_generator()
    output = generator.outputs[0]
    generator.generate_once()
    assert output.events == ["vendor/product/example|example"]
    snapshot = generator.snapshot()
    assert snapshot.statistics["events_generated"] == 1
    assert snapshot.statistics["errors"] == 0


def test_generator_start_stop_runs_background_loop(monkeypatch) -> None:
    generator = make_generator()
    generator.start()
    time.sleep(0.05)
    generator.stop()
    snapshot = generator.snapshot()
    assert snapshot.state == GeneratorState.STOPPED
    assert snapshot.statistics["events_generated"] >= 1
