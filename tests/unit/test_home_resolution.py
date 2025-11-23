from __future__ import annotations

from pathlib import Path

from logforge.core.home import (
    DEFAULT_INTERACTIVE_HOME,
    DEFAULT_SERVICE_HOME,
    resolve_logforge_home,
)


def test_env_override_takes_precedence(tmp_path) -> None:
    env = {"LOGFORGE_HOME": str(tmp_path / "custom")}
    result = resolve_logforge_home(env=env)
    assert result == Path(env["LOGFORGE_HOME"]).resolve()


def test_service_mode_flag() -> None:
    env = {"LOGFORGE_SERVICE_MODE": "true"}
    result = resolve_logforge_home(env=env)
    assert result == DEFAULT_SERVICE_HOME


def test_username_logforge_implies_service(tmp_path, monkeypatch) -> None:
    env = {}
    result = resolve_logforge_home(env=env, username="logforge")
    assert result == DEFAULT_SERVICE_HOME


def test_default_interactive_home(monkeypatch) -> None:
    env = {}
    result = resolve_logforge_home(env=env, username="alice")
    assert result == DEFAULT_INTERACTIVE_HOME
