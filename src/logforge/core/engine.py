from __future__ import annotations

from typing import Dict, List, Optional

from logforge.core.generator import Generator, GeneratorState
from logforge.core.config import LogForgeConfig, GeneratorDefinition
from logforge.outputs.manager import OutputManager
from logforge.templates.manager import TemplateManager


class GenerationEngine:
    def __init__(self, config: LogForgeConfig, template_manager: TemplateManager, output_manager: OutputManager) -> None:
        self.config = config
        self.template_manager = template_manager
        self.output_manager = output_manager
        self.generators: Dict[str, Generator] = {}
        self.initialize_generators()

    def initialize_generators(self) -> None:
        self.generators.clear()
        for definition in self.config.generators:
            if isinstance(definition, GeneratorDefinition):
                data = definition.model_dump()
            else:
                data = definition
            generator = Generator(
                name=data["name"],
                config={
                    "template": data["template"],
                    "outputs": data.get("outputs", []),
                    "frequency": data.get("frequency") or {"base_rate": 1},
                },
                template_manager=self.template_manager,
                output_manager=self.output_manager,
            )
            self.generators[data["name"]] = generator

    def list_generators(self) -> List[Dict[str, object]]:
        return [generator.snapshot() for generator in self.generators.values()]

    def get_generator(self, name: str) -> Generator:
        if name not in self.generators:
            raise KeyError(name)
        return self.generators[name]

    def start_generator(self, name: str) -> Dict[str, object]:
        generator = self.get_generator(name)
        generator.start()
        return generator.snapshot()

    def stop_generator(self, name: str) -> Dict[str, object]:
        generator = self.get_generator(name)
        generator.stop()
        return generator.snapshot()

    def restart_generator(self, name: str) -> Dict[str, object]:
        generator = self.get_generator(name)
        generator.stop()
        generator.start()
        return generator.snapshot()

    def start_all(self) -> List[Dict[str, object]]:
        snapshots: List[Dict[str, object]] = []
        for name in self.generators:
            snapshots.append(self.start_generator(name))
        return snapshots

    def stop_all(self) -> None:
        for generator in self.generators.values():
            generator.stop()
