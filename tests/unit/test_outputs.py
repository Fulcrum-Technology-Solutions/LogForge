from __future__ import annotations

import io
from types import SimpleNamespace

from logforge.outputs.base import CapturingOutput, RetryPolicy
from logforge.outputs.console import ConsoleOutput
from logforge.outputs.http import HttpOutput


def test_console_output_json_format() -> None:
    buffer = io.StringIO()
    output = ConsoleOutput(
        "console",
        stream=buffer,
        format="json",
        retry_policy=RetryPolicy(-1, 0, 1, 0),
        buffer_size=10,
    )
    output.emit("event", {"foo": "bar"})
    data = buffer.getvalue().strip()
    assert '"event": "event"' in data
    assert '"foo": "bar"' in data


def test_capturing_output_retries(monkeypatch) -> None:
    class FlakyOutput(CapturingOutput):
        def __init__(self) -> None:
            super().__init__(
                retry_policy=RetryPolicy(2, 0, 1, 0),
                buffer_size=3,
            )
            self.failures = 0

        def _send(self, event, metadata=None):
            if self.failures < 1:
                self.failures += 1
                raise RuntimeError("boom")
            super()._send(event, metadata)

    output = FlakyOutput()
    output.emit("event")
    assert output.events == ["event"]


def test_http_output_uses_session(monkeypatch):
    captured = {}

    class DummySession:
        def request(self, method, url, json=None, headers=None, timeout=10):
            captured.update(
                {
                    "method": method,
                    "url": url,
                    "payload": json,
                }
            )
            return SimpleNamespace(status_code=200, raise_for_status=lambda: None)

    output = HttpOutput(
        "http",
        url="http://example.com",
        method="POST",
        headers={"X-Test": "1"},
        retry_policy=RetryPolicy(-1, 0, 1, 0),
        buffer_size=10,
        session=DummySession(),
    )
    output.emit("event", {"foo": "bar"})
    assert captured["url"] == "http://example.com"
    assert captured["payload"]["event"] == "event"
