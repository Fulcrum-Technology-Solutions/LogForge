"""Syslog output handler."""

from __future__ import annotations

import logging
from logging.handlers import SysLogHandler

from logforge.outputs.base import BaseOutput, Metadata, RetryPolicy


class SyslogOutput(BaseOutput):
    """Sends events to a Syslog server."""

    def __init__(
        self,
        name: str,
        *,
        host: str = "localhost",
        port: int = 514,
        protocol: str = "udp",
        retry_policy: RetryPolicy,
        buffer_size: int,
    ) -> None:
        super().__init__(name, retry_policy=retry_policy, buffer_size=buffer_size)
        socktype = (
            SysLogHandler.SOCK_DGRAM if protocol.lower() == "udp" else SysLogHandler.SOCK_STREAM
        )
        self._handler = SysLogHandler(address=(host, port), socktype=socktype)
        self._logger = logging.getLogger(f"logforge.syslog.{name}")
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(self._handler)

    def _send(self, event: str, metadata: Metadata = None) -> None:
        message = event if metadata is None else f"{event} {metadata}"
        self._logger.info(message)


__all__ = ["SyslogOutput"]
