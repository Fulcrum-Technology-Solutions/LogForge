"""Generator engine and orchestration."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

from logforge.core.config_schema import ConfigModel, GeneratorConfig, OutputDefinition
from logforge.core.frequency import FrequencyController
from logforge.core.generator import Generator, GeneratorSnapshot
from logforge.outputs import build_output
from logforge.outputs.base import BaseOutput
from logforge.templates.renderer import TemplateRenderer


class OutputFactory:
    """Builds output instances for a specific generator."""

    def __init__(self, definitions: Iterable[OutputDefinition]) -> None:
        self._definitions = {definition.name: definition for definition in definitions}

    def create(self, names: Iterable[str], generator_name: str) -> List[BaseOutput]:
        outputs: List[BaseOutput] = []
        for name in names:
            definition = self._definitions.get(name)
            if definition is None:
                raise KeyError(
                    f"Unknown output '{name}' requested by generator '{generator_name}'."
                )
            outputs.append(build_output(definition, generator_name=generator_name))
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
        factory = OutputFactory(config.outputs.definitions)
        return cls(config.generators, renderer, factory)

    def start(self, name: str) -> GeneratorSnapshot:
        generator = self._get(name)
        generator.start()
        return generator.snapshot()

    def stop(self, name: str) -> GeneratorSnapshot:
        generator = self._get(name)
        generator.stop()
        return generator.snapshot()

    def restart(self, name: str) -> GeneratorSnapshot:
        generator = self._get(name)
        generator.restart()
        return generator.snapshot()

    def start_all(self) -> None:
        for generator in self._generators.values():
            if generator.config.enabled:
                generator.start()

    def stop_all(self) -> None:
        for generator in self._generators.values():
            generator.stop()

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
