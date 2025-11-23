"""Logging setup utilities for LogForge."""

from __future__ import annotations

import gzip
import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Callable, Tuple

from logforge.core.config import ConfigError, LoggingConfig


def _parse_size(value: str) -> int:
    units = {"kb": 1024, "mb": 1024**2, "gb": 1024**3, "tb": 1024**4}
    stripped = value.strip()
    if stripped.isdigit():
        return int(stripped)
    try:
        number = "".join(ch for ch in stripped if ch.isdigit())
        suffix = stripped[len(number) :].lower()
        if not number:
            raise ValueError
        base = int(number)
    except ValueError as exc:
        raise ConfigError(f"Invalid rotation max_size value: {value!r}") from exc
    if suffix not in units:
        raise ConfigError(f"Unsupported size suffix in {value!r}")
    return base * units[suffix]


def _parse_interval(value: str) -> Tuple[str, int]:
    units = {"s": "S", "m": "M", "h": "H", "d": "D"}
    stripped = value.strip().lower()
    if stripped.isdigit():
        return ("S", int(stripped))
    number = "".join(ch for ch in stripped if ch.isdigit())
    suffix = stripped[len(number) :]
    if not number or suffix not in units:
        raise ConfigError(f"Invalid time rotation max_age value: {value!r}")
    return (units[suffix], int(number))


def _configure_compression(handler: logging.Handler) -> None:
    def namer(name: str) -> str:
        return f"{name}.gz"

    def rotator(source: str, dest: str) -> None:
        with open(source, "rb") as src, gzip.open(dest, "wb") as dst:
            dst.writelines(src)
        os.remove(source)

    handler.namer = namer  # type: ignore[attr-defined]
    handler.rotator = rotator  # type: ignore[attr-defined]


def setup_logging(config: LoggingConfig) -> logging.Logger:
    level = getattr(logging, config.level, logging.INFO)
    log_path = Path(config.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    rotation_type = getattr(config.rotation, "type", "size")
    compress = bool(getattr(config.rotation, "compress", False))

    if rotation_type == "size":
        max_bytes = _parse_size(getattr(config.rotation, "max_size", "50MB"))
        backup_count = getattr(config.rotation, "backup_count", 5)

        def handler_factory() -> logging.Handler:
            return RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )

    elif rotation_type == "time":
        max_age = getattr(config.rotation, "max_age", "24h")
        when, interval = _parse_interval(max_age)
        backup_count = getattr(config.rotation, "backup_count", 5)

        def handler_factory() -> logging.Handler:
            return TimedRotatingFileHandler(
                log_path,
                when=when,
                interval=interval,
                backupCount=backup_count,
                encoding="utf-8",
            )

    else:
        raise ConfigError(f"Unsupported rotation.type: {rotation_type!r}")

    handler = handler_factory()
    if compress:
        _configure_compression(handler)

    handler.setFormatter(logging.Formatter(config.format))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for existing in list(root_logger.handlers):
        root_logger.removeHandler(existing)
        existing.close()

    root_logger.addHandler(handler)
    return root_logger

