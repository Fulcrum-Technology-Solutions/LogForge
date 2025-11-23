from __future__ import annotations

import logging
from pathlib import Path

import pytest

from logforge.core.config import LoggingConfig
from logforge.utils.logging import setup_logging


@pytest.fixture(autouse=True)
def _reset_logging():
    root = logging.getLogger()
    original_level = root.level
    yield
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    logging.basicConfig(level=original_level, force=True)


def _build_logging_config(path: Path, **rotation_overrides) -> LoggingConfig:
    data = {
        "level": "INFO",
        "file": str(path),
        "format": "%(message)s",
        "rotation": {
            "type": rotation_overrides.get("type", "size"),
            "max_size": rotation_overrides.get("max_size", "1MB"),
            "max_age": rotation_overrides.get("max_age", "24h"),
            "backup_count": rotation_overrides.get("backup_count", 2),
            "compress": rotation_overrides.get("compress", False),
        },
    }
    return LoggingConfig.parse_obj(data)


def test_setup_logging_with_size_rotation(tmp_path):
    log_file = tmp_path / "logforge.log"
    config = _build_logging_config(log_file)

    logger = setup_logging(config)
    logger.info("hello size rotation")

    assert log_file.exists()
    assert "hello size rotation" in log_file.read_text(encoding="utf-8")
    assert isinstance(logger.handlers[0], logging.handlers.RotatingFileHandler)


def test_setup_logging_with_time_rotation(tmp_path):
    log_file = tmp_path / "logforge.log"
    config = _build_logging_config(log_file, type="time", max_age="1d")

    logger = setup_logging(config)
    logger.info("hello time rotation")

    assert log_file.exists()
    assert isinstance(logger.handlers[0], logging.handlers.TimedRotatingFileHandler)
