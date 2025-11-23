from __future__ import annotations

import asyncio
from typing import List

import pytest
from fastapi.testclient import TestClient

from logforge.api.context import APIContext
from logforge.api.server import create_app
from logforge.core.config import LogForgeConfig


class StubGenerationEngine:
    def __init__(self):
        self.started: List[str] = []
        self.stopped: List[str] = []

    async def start_generator(self, name: str) -> None:
        if name != "known":
            raise ValueError(f"Generator {name} is not registered.")
        self.started.append(name)

    async def stop_generator(self, name: str) -> None:
        if name != "known":
            raise ValueError(f"Generator {name} is not registered.")
        self.stopped.append(name)

    def snapshot(self):
        from logforge.core.telemetry import EngineSnapshot, EngineTotals, SystemTelemetry, GeneratorTelemetry, GeneratorStatistics, GeneratorState

        return EngineSnapshot(
            uptime_seconds=10,
            totals=EngineTotals(total=1, running=1, degraded=0, error=0),
            generators=[
                GeneratorTelemetry(
                    name="known",
                    template="tpl",
                    enabled=True,
                    state=GeneratorState.RUNNING,
                    frequency_base_rate=1,
                    frequency_current_rate=1,
                    outputs=[],
                    statistics=GeneratorStatistics(events_generated=5, errors=0, uptime_seconds=10),
                )
            ],
            system=SystemTelemetry(cpu_percent=0.0, memory_mb=0.0, threads=1),
        )


@pytest.fixture()
def api_client() -> TestClient:
    config = LogForgeConfig.parse_obj(
        {
            "version": "1.0",
            "engine": {"log_level": "INFO"},
            "api": {"enabled": True, "host": "127.0.0.1", "port": 8080, "auth": {"enabled": False, "key": None}},
            "entity_registry": {"path": "entities.yaml", "auto_save": False, "save_interval": 60, "backup_enabled": False, "backup_count": 1},
            "templates": {"local_path": ".", "default_path": ".", "custom_path": ".", "precedence": "custom_first"},
            "logging": {"level": "INFO", "file": "logforge.log", "rotation": {"max_size": "50MB", "backup_count": 5}, "format": "%(message)s"},
            "outputs": {"retry": {"max_attempts": -1, "retry_interval": 5, "backoff_multiplier": 2.0, "max_backoff": 300}, "buffer_size": 1000, "definitions": []},
            "generators": [],
        }
    )
    engine = StubGenerationEngine()
    context = APIContext(config=config, telemetry=engine, engine=engine)
    app = create_app(context)
    return TestClient(app)


def test_list_generators(api_client: TestClient):
    response = api_client.get("/api/generators")
    assert response.status_code == 200
    data = response.json()
    assert data["generators"][0]["name"] == "known"


def test_start_generator(api_client: TestClient):
    response = api_client.post("/api/generators/known/start")
    assert response.status_code == 200
    assert response.json()["message"] == "Generator starting"


def test_start_unknown_generator(api_client: TestClient):
    response = api_client.post("/api/generators/unknown/start")
    assert response.status_code == 404

