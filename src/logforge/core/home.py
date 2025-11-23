"""LOGFORGE_HOME resolution utilities."""

from __future__ import annotations

import os
import pwd
from pathlib import Path
from typing import Mapping

DEFAULT_INTERACTIVE_HOME = Path.home() / ".logforge"
DEFAULT_SERVICE_HOME = Path("/var/lib/logforge")


def resolve_logforge_home(
    *,
    env: Mapping[str, str] | None = None,
    override: str | Path | None = None,
    username: str | None = None,
) -> Path:
    """Determine LOGFORGE_HOME according to precedence rules."""

    effective_env = env or os.environ

    if override is not None:
        return Path(override).expanduser().resolve()

    env_home = effective_env.get("LOGFORGE_HOME")
    if env_home:
        return Path(env_home).expanduser().resolve()

    if username is None:
        username = _safe_get_username()

    if _is_service_mode(effective_env, username):
        return DEFAULT_SERVICE_HOME

    return DEFAULT_INTERACTIVE_HOME


def _is_service_mode(env: Mapping[str, str], username: str | None) -> bool:
    service_flag = env.get("LOGFORGE_SERVICE_MODE")
    if service_flag and service_flag.lower() in {"1", "true", "yes", "on"}:
        return True
    if username and username.lower() == "logforge":
        return True
    return False


def _safe_get_username() -> str | None:
    try:
        return pwd.getpwuid(os.getuid()).pw_name
    except Exception:
        return None


__all__ = [
    "DEFAULT_INTERACTIVE_HOME",
    "DEFAULT_SERVICE_HOME",
    "resolve_logforge_home",
]
