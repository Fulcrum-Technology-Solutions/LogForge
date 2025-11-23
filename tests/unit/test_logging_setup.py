from __future__ import annotations

from pathlib import Path

from logforge.core.config_schema import (
    LoggingConfig,
    LoggingRotationConfig,
)
from logforge.utils.logging import configure_logging, get_logger, log_context


def build_config(log_path: Path) -> LoggingConfig:
    return LoggingConfig(
        file=str(log_path),
        level="INFO",
        format="%(message)s",
        rotation=LoggingRotationConfig(
            type="size",
            max_size="1KB",
            backup_count=1,
            compress=False,
        ),
    )


def test_configure_logging_writes_file(tmp_path) -> None:
    config = build_config(tmp_path / "logforge.log")
    configure_logging(config, logforge_home=tmp_path)
    logger = get_logger("test")
    logger.info("hello world")
    contents = (tmp_path / "logforge.log").read_text()
    assert "hello world" in contents


def test_log_context_logs_completion(tmp_path, caplog) -> None:
    config = build_config(tmp_path / "logforge.log")
    configure_logging(config, logforge_home=tmp_path)
    logger = get_logger("context-test")
    with log_context(logger, "operation"):
        logger.info("inside")
    log_contents = (tmp_path / "logforge.log").read_text()
    assert "operation - start" in log_contents
    assert "operation - complete" in log_contents
