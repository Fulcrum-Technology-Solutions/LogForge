from __future__ import annotations

import time
from pathlib import Path

from logforge.core.config_schema import (
    FrequencyConfig,
    GeneratorConfig,
    OutputConfig,
    OutputDefinition,
    OutputRetryConfig,
)
from logforge.core.engine import GeneratorEngine, OutputFactory
from logforge.core.generator import GeneratorState


class StubRenderer:
    def render(self, template_id: str, context=None) -> str:
        return f"{template_id}:{context['generator']}"


def make_output_definition(path: Path) -> OutputDefinition:
    return OutputDefinition(
        name="file_out",
        type="file",
        path=str(path / "{generator}.log"),
    )


def make_output_config(path: Path) -> OutputConfig:
    return OutputConfig(
        buffer_size=10,
        retry=OutputRetryConfig(
            max_attempts=1,
            retry_interval=0,
            backoff_multiplier=1,
            max_backoff=0,
        ),
        definitions=[make_output_definition(path)],
    )


def make_generator_config() -> GeneratorConfig:
    return GeneratorConfig(
        name="test",
        template="vendor/product/example",
        enabled=True,
        outputs=["file_out"],
        frequency=FrequencyConfig(base_rate=5),
    )


def test_engine_start_stop(tmp_path) -> None:
    output_config = make_output_config(tmp_path)
    factory = OutputFactory(output_config)
    config = make_generator_config()
    renderer = StubRenderer()
    engine = GeneratorEngine([config], renderer, factory)
    engine.start("test")
    time.sleep(0.05)
    engine.stop("test")
    snapshot = engine.snapshot("test")
    assert snapshot.state == GeneratorState.STOPPED
    log_file = tmp_path / "test.log"
    assert log_file.exists()
    assert log_file.read_text().strip() != ""
