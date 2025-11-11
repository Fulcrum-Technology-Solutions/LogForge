"""Logging utilities for LogForge."""

from __future__ import annotations

import logging
import logging.config
import logging.handlers
from pathlib import Path

from logforge.core.config import LoggingConfig

LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def parse_size(value: str) -> int:
    """Convert human readable size strings to bytes."""
    if not value:
        return 0
    normalized = value.strip().upper()
    multiplier = 1
    if normalized.endswith("KB"):
        multiplier = 1024
        normalized = normalized[:-2]
    elif normalized.endswith("MB"):
        multiplier = 1024**2
        normalized = normalized[:-2]
    elif normalized.endswith("GB"):
        multiplier = 1024**3
        normalized = normalized[:-2]
    elif normalized.endswith("B"):
        normalized = normalized[:-1]
    try:
        return int(float(normalized) * multiplier)
    except ValueError:  # pragma: no cover - defensive
        return 0


def configure_logging(config: LoggingConfig) -> None:
    """Configure root logging according to config."""
    level = LEVELS.get(config.level.upper(), logging.INFO)
    log_path = Path(config.file).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    max_bytes = parse_size(config.rotation.max_size)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": config.format},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level,
                "formatter": "default",
                "filename": str(log_path),
                "maxBytes": max_bytes or 10 * 1024 * 1024,
                "backupCount": config.rotation.backup_count,
                "encoding": "utf-8",
            },
        },
        "root": {"level": level, "handlers": ["console", "file"]},
    }

    logging.config.dictConfig(logging_config)
