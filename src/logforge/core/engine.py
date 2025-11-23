"""Generator engine and orchestration."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

from logforge.core.config_schema import ConfigModel, GeneratorConfig, OutputConfig
from logforge.core.frequency import FrequencyController
from logforge.core.generator import Generator, GeneratorSnapshot, GeneratorState
from logforge.outputs import build_output
from logforge.outputs.base import BaseOutput
from logforge.templates.renderer import TemplateRenderer
from logforge.utils.metrics import generators_running


class OutputFactory:
    """Builds output instances for a specific generator."""

    def __init__(self, config: OutputConfig) -> None:
        self._definitions = {definition.name: definition for definition in config.definitions}
        self._buffer_size = config.buffer_size
        retry_config = config.retry
        self._retry_policy = {
            "max_attempts": retry_config.max_attempts,
            "retry_interval": retry_config.retry_interval,
            "backoff_multiplier": retry_config.backoff_multiplier,
            "max_backoff": retry_config.max_backoff,
        }

    def create(self, names: Iterable[str], generator_name: str) -> List[BaseOutput]:
        outputs: List[BaseOutput] = []
        for name in names:
            definition = self._definitions.get(name)
            if definition is None:
                raise KeyError(
                    f"Unknown output '{name}' requested by generator '{generator_name}'."
                )
            outputs.append(
                build_output(
                    definition,
                    generator_name=generator_name,
                    retry_policy=self._retry_policy,
                    buffer_size=self._buffer_size,
                )
            )
        return outputs


class GeneratorEngine:
    """Manages generator lifecycle and exposes status snapshots."""

    def __init__(
        self,
        generator_configs: Iterable[GeneratorConfig],
        renderer: TemplateRenderer,
        output_factory: OutputFactory,
        *,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._logger = logger or logging.getLogger("logforge.engine")
        self._generators: Dict[str, Generator] = {}
        for config in generator_configs:
            frequency = FrequencyController(config.frequency)
            outputs = output_factory.create(config.outputs, config.name)
            generator = Generator(
                config=config,
                renderer=renderer,
                outputs=outputs,
                frequency=frequency,
                logger=self._logger.getChild(config.name),
            )
            self._generators[config.name] = generator

    @classmethod
    def from_config(cls, config: ConfigModel, renderer: TemplateRenderer) -> GeneratorEngine:
        factory = OutputFactory(config.outputs)
        return cls(config.generators, renderer, factory)

    def start(self, name: str) -> GeneratorSnapshot:
        generator = self._get(name)
        generator.start()
        self._update_generator_metrics()
        return generator.snapshot()

    def stop(self, name: str) -> GeneratorSnapshot:
        generator = self._get(name)
        generator.stop()
        self._update_generator_metrics()
        return generator.snapshot()

    def restart(self, name: str) -> GeneratorSnapshot:
        generator = self._get(name)
        generator.restart()
        self._update_generator_metrics()
        return generator.snapshot()

    def start_all(self) -> None:
        for generator in self._generators.values():
            if generator.config.enabled:
                generator.start()
        self._update_generator_metrics()

    def stop_all(self) -> None:
        for generator in self._generators.values():
            generator.stop()
        self._update_generator_metrics()

    def _update_generator_metrics(self) -> None:
        """Update generators_running gauge based on current generator states."""
        states = {state: 0 for state in GeneratorState}
        for generator in self._generators.values():
            states[generator.state] = states.get(generator.state, 0) + 1
        for state in GeneratorState:
            generators_running.labels(state=state.value).set(states.get(state, 0))

    def list_snapshots(self) -> List[GeneratorSnapshot]:
        return [generator.snapshot() for generator in self._generators.values()]

    def snapshot(self, name: str) -> GeneratorSnapshot:
        return self._get(name).snapshot()

    def _get(self, name: str) -> Generator:
        try:
            return self._generators[name]
        except KeyError as exc:  # pragma: no cover - defensive
            raise KeyError(f"Unknown generator '{name}'") from exc


__all__ = ["GeneratorEngine", "OutputFactory"]
