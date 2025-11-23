from __future__ import annotations

import time
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from logforge.api.context import APIContext
from logforge.api.server import create_app
from logforge.core import config as core_config
from logforge.core.telemetry import (
    EngineSnapshot,
    EngineTelemetryProvider,
    EngineTotals,
    GeneratorStatistics,
    GeneratorTelemetry,
    GeneratorState,
    SystemTelemetry,
)
from logforge.utils.metrics import MetricsRegistry


class StubTelemetry(EngineTelemetryProvider):
    def snapshot(self) -> EngineSnapshot:
        generator = GeneratorTelemetry(
            name="windows_security",
            template="microsoft/windows/eventlog/security",
            enabled=True,
            state=GeneratorState.RUNNING,
            frequency_base_rate=10,
            frequency_current_rate=20,
            outputs=["default_file"],
            statistics=GeneratorStatistics(
                events_generated=123,
                errors=1,
                uptime_seconds=300,
                last_event="2025-11-22T10:00:00Z",
            ),
        )
        totals = EngineTotals(total=1, running=1, degraded=0, error=0)
        system = SystemTelemetry(cpu_percent=12.5, memory_mb=256.0, threads=4)
        return EngineSnapshot(
            uptime_seconds=360,
            totals=totals,
            generators=[generator],
            system=system,
            entity_registry_status="healthy",
            template_cache_status="healthy",
        )


def build_context() -> APIContext:
    config = core_config.LogForgeConfig.parse_obj(core_config.default_config_dict())
    telemetry = StubTelemetry()
    metrics = MetricsRegistry()
    return APIContext(config=config, telemetry=telemetry, metrics=metrics)


def test_health_endpoint_returns_snapshot():
    context = build_context()
    app = create_app(context)
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["generators"]["running"] == 1
    assert data["entity_registry"] == "healthy"


def test_status_endpoint_includes_generator_data():
    context = build_context()
    app = create_app(context)
    client = TestClient(app)

    response = client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert data["generators"][0]["name"] == "windows_security"
    assert data["generators"][0]["frequency"]["current_rate"] == 20
    assert data["system"]["cpu_percent"] == pytest.approx(12.5)


def test_metrics_endpoint_respects_api_key(monkeypatch):
    context = build_context()
    context.config.api.auth.enabled = True
    context.config.api.auth.key = "secret"
    app = create_app(context)
    client = TestClient(app)

    unauthorized = client.get("/api/metrics")
    assert unauthorized.status_code == 401

    authorized = client.get("/api/metrics", headers={"Authorization": "Bearer secret"})
    assert authorized.status_code == 200
    assert "logforge_events_generated_total" in authorized.text

