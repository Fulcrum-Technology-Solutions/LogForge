"""Logging utilities for LogForge."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from logforge.core.config import LoggingConfig

_SIZE_UNITS = {
    "b": 1,
    "kb": 1024,
    "mb": 1024**2,
    "gb": 1024**3,
    "tb": 1024**4,
}


def parse_size(value: str) -> int:
    """Convert human readable size strings to bytes."""
    if not value:
        return 0
    raw = value.strip().lower()
    for suffix in sorted(_SIZE_UNITS.keys(), key=len, reverse=True):
        if raw.endswith(suffix):
            number = raw[: -len(suffix)].strip() or "0"
            try:
                return int(float(number) * _SIZE_UNITS[suffix])
            except ValueError:  # pragma: no cover
                return 0
    try:
        return int(float(raw))
    except ValueError:  # pragma: no cover
        return 0


def configure_logging(settings: Optional[LoggingConfig] = None, *, enable_console: bool = True) -> None:
    """Configure root logging according to the provided settings."""
    config = settings or LoggingConfig()
    log_level = getattr(logging, config.level.upper(), logging.INFO)

    logging.captureWarnings(True)
    root = logging.getLogger()
    root.setLevel(log_level)

    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter(config.format)

    log_path = Path(config.file).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    max_bytes = parse_size(config.rotation.max_size) or 10 * 1024 * 1024
    file_handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=max_bytes,
        backupCount=config.rotation.backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root.addHandler(file_handler)

    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance with the configured hierarchy."""
    return logging.getLogger(name)
