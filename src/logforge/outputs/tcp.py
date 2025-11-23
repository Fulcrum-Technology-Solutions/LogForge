"""TCP output handler."""

from __future__ import annotations

import socket

from logforge.outputs.base import BaseOutput, Metadata, RetryPolicy


class TcpOutput(BaseOutput):
    """Sends events over TCP."""

    def __init__(
        self,
        name: str,
        *,
        host: str,
        port: int,
        retry_policy: RetryPolicy,
        buffer_size: int,
        delimiter: str = "\n",
    ) -> None:
        super().__init__(name, retry_policy=retry_policy, buffer_size=buffer_size)
        self.host = host
        self.port = port
        self.delimiter = delimiter

    def _send(self, event: str, metadata: Metadata = None) -> None:
        payload = (event.rstrip("\n") + self.delimiter).encode("utf-8")
        with socket.create_connection((self.host, self.port), timeout=5) as conn:
            conn.sendall(payload)


__all__ = ["TcpOutput"]
