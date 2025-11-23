from __future__ import annotations

import asyncio

import pytest

from logforge.core.config import GeneratorConfig, GeneratorFrequencyConfig, OutputRetryConfig
from logforge.core.engine import GenerationEngine
from logforge.outputs.base import OutputHandler


class SimpleTemplateEngine:
    def __init__(self):
        self.events = 0

    def render_event(self, template_id: str, context=None) -> str:
        self.events += 1
        return '{"template": "%s"}' % template_id


class RecordingHandler(OutputHandler):
    def __init__(self):
        super().__init__(
            name="recording",
            retry_config=OutputRetryConfig(
                max_attempts=-1,
                retry_interval=1,
                backoff_multiplier=2.0,
                max_backoff=10,
            ),
            buffer_size=10,
        )
        self.events: list[str] = []

    async def _write(self, event: str, generator: str) -> None:
        self.events.append((generator, event))


@pytest.mark.asyncio
async def test_generation_engine_start_stop():
    template_engine = SimpleTemplateEngine()
    handler = RecordingHandler()
    engine = GenerationEngine(template_engine, outputs={"rec": handler})

    generator_config = GeneratorConfig(
        name="test",
        template="vendor/product/source/name",
        enabled=True,
        frequency=GeneratorFrequencyConfig(base_rate=1, variation=[]),
        outputs=["rec"],
    )

    await engine.register_generator(generator_config)
    await engine.start_generator("test")
    await asyncio.sleep(0.2)
    await engine.stop_generator("test")

    snapshot = engine.snapshot()
    assert snapshot.generators[0].statistics.events_generated >= 0
    assert handler.events, "Expected output handler to receive events"

