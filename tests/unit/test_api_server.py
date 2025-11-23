from __future__ import annotations

from unittest import mock

from fastapi.testclient import TestClient

from logforge.api.models import (
    GeneratorStatistics,
    GeneratorStatus,
    GeneratorSummary,
    HealthResponse,
    StatusResponse,
    SystemMetrics,
)
from logforge.api.server import APIDependencies, APIServer, APISettings, create_app


def make_dependencies() -> APIDependencies:
    def health() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            uptime=5,
            generators=GeneratorSummary(total=1, running=1, degraded=0, error=0),
            entity_registry="healthy",
            template_cache="healthy",
        )

    def status() -> StatusResponse:
        return StatusResponse(
            uptime=5,
            version="1.0.0",
            generators=[
                GeneratorStatus(
                    name="test",
                    state="RUNNING",
                    template="vendor/product",
                    frequency={"base_rate": 10, "current_rate": 10},
                    outputs=["console"],
                    statistics=GeneratorStatistics(
                        events_generated=1,
                        errors=0,
                        uptime=5,
                        last_event="2024-01-01T00:00:00Z",
                    ),
                )
            ],
            system=SystemMetrics(cpu_percent=10.0, memory_mb=128, threads=4),
        )

    def metrics() -> bytes:
        return b"test_metric 1\n"

    return APIDependencies(get_health=health, get_status=status, get_metrics=metrics)


def test_health_endpoint_returns_data() -> None:
    app = create_app(dependencies=make_dependencies())
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_status_endpoint_requires_auth_when_enabled() -> None:
    app = create_app(
        settings=APISettings(auth_enabled=True, api_key="secret"),
        dependencies=make_dependencies(),
    )
    client = TestClient(app)
    assert client.get("/api/status").status_code == 401
    resp = client.get("/api/status", headers={"Authorization": "Bearer secret"})
    assert resp.status_code == 200
    assert resp.json()["version"] == "1.0.0"


def test_metrics_endpoint_returns_plain_text() -> None:
    app = create_app(dependencies=make_dependencies())
    client = TestClient(app)
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    assert resp.text.startswith("test_metric")


def test_api_server_start_stop() -> None:
    app = create_app()
    with mock.patch("uvicorn.Server.run", return_value=None) as run_mock:
        server = APIServer(app, APISettings(port=9100))
        server.start()
        server.stop()
        assert run_mock.called
