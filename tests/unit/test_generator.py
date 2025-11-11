from __future__ import annotations

import time

from logforge.core.generator import Generator, GeneratorState
from logforge.outputs.base import OutputHandler


class CaptureHandler(OutputHandler):
    def __init__(self) -> None:
        self.events = []

    def write(self, event: str) -> None:
        self.events.append(event)


class StubTemplateManager:
    def render(self, template_id: str):
        return '{"message": "hello"}'


class StubOutputManager:
    def __init__(self, handler: OutputHandler) -> None:
        self.handler = handler

    def create_handlers(self, generator_name, outputs):
        return [self.handler]


def test_generator_start_and_stop():
    handler = CaptureHandler()
    generator = Generator(
        name="demo",
        config={"template": "acme/simple", "outputs": ["console"], "frequency": {"base_rate": 5}},
        template_manager=StubTemplateManager(),
        output_manager=StubOutputManager(handler),
        max_events=2,
    )

    generator.start()
    time.sleep(0.2)
    generator.stop()

    assert handler.events
    assert generator.state in {GeneratorState.STOPPED, GeneratorState.ERROR}
