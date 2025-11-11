from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from logforge.core.config import LoggingSettings, expand_path

_SIZE_UNITS = {
    "b": 1,
    "kb": 1024,
    "mb": 1024**2,
    "gb": 1024**3,
    "tb": 1024**4,
}


def _parse_size(value: str) -> int:
    raw = value.strip().lower()
    for suffix in sorted(_SIZE_UNITS.keys(), key=len, reverse=True):
        if raw.endswith(suffix):
            number = raw[: -len(suffix)].strip()
            return int(float(number) * _SIZE_UNITS[suffix])
    return int(float(raw))


def configure_logging(settings: Optional[LoggingSettings] = None, *, enable_console: bool = True) -> None:
    config = settings or LoggingSettings()
    log_level = getattr(logging, config.level.upper(), logging.INFO)

    logging.captureWarnings(True)
    root = logging.getLogger()
    root.setLevel(log_level)

    # Clear existing handlers to avoid duplicates when reconfiguring
    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter(config.format)

    file_path = expand_path(config.file)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    max_bytes = _parse_size(config.rotation.max_size)
    file_handler = RotatingFileHandler(
        filename=file_path,
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
    return logging.getLogger(name)
