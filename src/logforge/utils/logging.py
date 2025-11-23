"""Logging utilities."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Iterator, Optional

from logforge.core.config_schema import LoggingConfig, LoggingRotationConfig
from logforge.core.home import resolve_logforge_home

SIZE_SUFFIXES = {"kb": 1024, "mb": 1024**2, "gb": 1024**3}
TIME_SUFFIXES = {"s": ("S", 1), "m": ("M", 1), "h": ("H", 1), "d": ("D", 1)}


def configure_logging(config: LoggingConfig, *, logforge_home: Optional[Path] = None) -> None:
    """Configure root logger based on LoggingConfig."""

    home = resolve_logforge_home(override=logforge_home)
    log_path = _resolve_path(config.file, home)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = _build_handler(log_path, config.rotation)
    formatter = logging.Formatter(config.format)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(config.level)
    root.handlers.clear()
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance."""

    return logging.getLogger(name)


@contextmanager
def log_context(
    logger: logging.Logger,
    message: str,
    level: int = logging.INFO,
    **extra: object,
) -> Iterator[None]:
    """Context manager that logs start/finish (and errors) for a block."""

    logger.log(level, "%s - start", message, extra=extra or None)
    try:
        yield
    except Exception:  # pragma: no cover - re-raised after logging
        logger.exception("%s - failed", message, extra=extra or None)
        raise
    else:
        logger.log(level, "%s - complete", message, extra=extra or None)


def _build_handler(
    path: Path,
    rotation: Optional[LoggingRotationConfig],
) -> logging.Handler:
    if rotation is None:
        return logging.FileHandler(path, encoding="utf-8")

    rotation_type = rotation.type
    handler: logging.Handler
    if rotation_type == "size":
        max_bytes = _parse_size(rotation.max_size or "10MB")
        backup_count = rotation.backup_count
        handler = RotatingFileHandler(
            path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
    elif rotation_type == "time":
        when, interval = _parse_time(rotation.max_age or "1d")
        handler = TimedRotatingFileHandler(
            path,
            when=when,
            interval=interval,
            backupCount=rotation.backup_count,
            encoding="utf-8",
        )
    else:  # pragma: no cover - guarded by schema
        raise ValueError(f"Unsupported rotation type: {rotation_type}")

    handler.namer = lambda name: f"{name}.gz" if rotation.compress else name
    return handler


def _parse_size(raw: str) -> int:
    value = raw.strip().lower()
    for suffix, multiplier in SIZE_SUFFIXES.items():
        if value.endswith(suffix):
            base = float(value[: -len(suffix)])
            return int(base * multiplier)
    return int(value)


def _parse_time(raw: str) -> tuple[str, int]:
    value = raw.strip().lower()
    for suffix, (when, multiplier) in TIME_SUFFIXES.items():
        if value.endswith(suffix):
            base = int(value[: -len(suffix)])
            return when, base * multiplier
    raise ValueError(f"Invalid time duration '{raw}'")


def _resolve_path(path_str: str, home: Path) -> Path:
    resolved = path_str.replace("${LOGFORGE_HOME}", str(home))
    return Path(resolved).expanduser()


__all__ = ["configure_logging", "get_logger", "log_context"]
