from __future__ import annotations

from pathlib import Path
from unittest import mock

from fastapi import HTTPException
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

    deps = APIDependencies(get_health=health, get_status=status, get_metrics=metrics)
    generator_data = {
        "name": "windows_security",
        "state": "RUNNING",
        "template": "vendor/product",
        "enabled": True,
        "outputs": ["default"],
        "frequency": {"base_rate": 10, "current_rate": 10},
        "statistics": {"events_generated": 1, "errors": 0, "uptime": 0, "last_event": None},
    }
    deps.list_generators = lambda: [generator_data]
    deps.get_generator = lambda name: generator_data if name == "windows_security" else None
    deps.start_generator = lambda name: generator_data
    deps.stop_generator = lambda name: generator_data
    deps.restart_generator = lambda name: generator_data
    output_data = {
        "name": "default_file",
        "type": "file",
        "status": "healthy",
        "configuration": {"path": "{generator}.log"},
        "statistics": {"events_sent": 1, "errors": 0, "buffered_events": 0, "last_error": None},
    }
    deps.list_outputs = lambda: [output_data]
    deps.get_output = lambda name: output_data if name == "default_file" else None
    return deps


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


def test_entities_endpoints() -> None:
    deps = make_dependencies()
    deps.entities_summary = lambda: {"users": 1}
    deps.list_entities = lambda entity_type: [{"username": "jsmith"}]
    deps.create_entity = lambda entity_type, payload: payload | {"id": 1}
    app = create_app(dependencies=deps)
    client = TestClient(app)
    assert client.get("/api/entities").json()["users"] == 1
    assert client.get("/api/entities/users").json()["count"] == 1
    resp = client.post("/api/entities/users", json={"username": "mary"})
    assert resp.status_code == 201
    assert resp.json()["id"] == 1


def test_templates_endpoints() -> None:
    deps = make_dependencies()
    summary = {
        "id": "vendor/product/example",
        "name": "Example",
        "vendor": "vendor",
        "product": "product",
        "data_source": "system",
        "version": "1.0.0",
        "location": "default",
    }
    detail = {
        "summary": summary,
        "metadata": {
            "id": "vendor/product/example",
            "name": "Example",
            "vendor": "vendor",
            "product": "product",
            "data_source": "system",
            "format": "json",
        },
    }
    deps.list_templates = lambda: [summary]
    deps.get_template = lambda template_id: detail if template_id == summary["id"] else None
    app = create_app(dependencies=deps)
    client = TestClient(app)
    resp = client.get("/api/templates")
    assert resp.status_code == 200
    assert resp.json()["templates"][0]["id"] == summary["id"]
    detail_resp = client.get(f"/api/templates/{summary['id']}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["summary"]["name"] == "Example"


def test_generators_endpoints() -> None:
    deps = make_dependencies()
    app = create_app(dependencies=deps)
    client = TestClient(app)
    resp = client.get("/api/generators")
    assert resp.status_code == 200
    listing = resp.json()
    assert listing[0]["name"] == "windows_security"
    status_resp = client.get("/api/generators/windows_security")
    assert status_resp.status_code == 200
    start_resp = client.post("/api/generators/windows_security/start")
    assert start_resp.status_code == 200


def test_outputs_endpoints() -> None:
    deps = make_dependencies()
    app = create_app(dependencies=deps)
    client = TestClient(app)
    resp = client.get("/api/outputs")
    assert resp.status_code == 200
    outputs = resp.json()["outputs"]
    assert outputs[0]["name"] == "default_file"
    detail = client.get("/api/outputs/default_file")
    assert detail.status_code == 200


def test_community_search_endpoint(monkeypatch):
    class FakeCommunityClient:
        def search_templates(self, query: str, limit: int = 20):
            return [{"id": "vendor/product/example", "name": "Example"}]

        def download_template(self, template_id: str) -> bytes:  # pragma: no cover - not used here
            raise AssertionError("not expected")

    monkeypatch.setattr(
        "logforge.api.endpoints.community._community_client",
        lambda: FakeCommunityClient(),
    )
    app = create_app(dependencies=make_dependencies())
    client = TestClient(app)
    resp = client.get("/api/community/templates/search", params={"query": "windows"})
    assert resp.status_code == 200
    assert resp.json()["results"][0]["id"] == "vendor/product/example"


def test_community_install_endpoint(monkeypatch, tmp_path):
    class FakeCommunityClient:
        def search_templates(self, query: str, limit: int = 20):  # pragma: no cover - not used
            return []

        def download_template(self, template_id: str) -> bytes:
            return b"zipbytes"

    monkeypatch.setattr(
        "logforge.api.endpoints.community._community_client",
        lambda: FakeCommunityClient(),
    )

    def fake_install(template_id: str, archive: bytes, *, destination=None, force=False) -> Path:
        assert template_id == "vendor/product/example"
        return tmp_path / template_id

    monkeypatch.setattr(
        "logforge.api.endpoints.community.install_template_archive",
        fake_install,
    )

    app = create_app(dependencies=make_dependencies())
    client = TestClient(app)
    resp = client.post(
        "/api/community/templates/install",
        json={"template_id": "vendor/product/example", "destination": str(tmp_path), "force": True},
    )
    assert resp.status_code == 200
    assert resp.json()["path"].endswith("vendor/product/example")


def test_http_exception_handler_returns_error_payload() -> None:
    app = create_app(dependencies=make_dependencies())

    @app.get("/api/fail")
    def _fail():
        raise HTTPException(status_code=418, detail="teapot")

    client = TestClient(app)
    resp = client.get("/api/fail")
    assert resp.status_code == 418
    assert resp.json() == {"success": False, "error": "teapot", "details": None}


def test_request_validation_handler_formats_errors() -> None:
    app = create_app(dependencies=make_dependencies())
    client = TestClient(app)
    # Missing body for POST should trigger validation error
    resp = client.post("/api/entities/users")
    assert resp.status_code == 422
    body = resp.json()
    assert body["success"] is False
    assert body["error"] == "Request validation failed."
    assert isinstance(body["details"], list)


def test_unhandled_exception_handler_masks_errors() -> None:
    app = create_app(dependencies=make_dependencies())

    @app.get("/api/crash")
    def _crash():
        raise RuntimeError("boom")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/crash")
    assert resp.status_code == 500
    data = resp.json()
    assert data["success"] is False
    assert data["error"] == "Internal server error."


def test_api_server_start_stop() -> None:
    app = create_app()
    with mock.patch("uvicorn.Server.run", return_value=None) as run_mock:
        server = APIServer(app, APISettings(port=9100))
        server.start()
        server.stop()
        assert run_mock.called
