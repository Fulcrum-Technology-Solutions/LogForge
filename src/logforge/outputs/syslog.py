"""Syslog output handler supporting RFC 5424 and RFC 3164."""

from __future__ import annotations

import socket
from datetime import datetime, timezone
from typing import Optional

from logforge.outputs.base import BaseOutput, Metadata, RetryPolicy


class SyslogOutput(BaseOutput):
    """Sends events to a Syslog server with RFC 5424/3164 support."""

    # RFC 5424 facility codes
    FACILITY_KERN = 0
    FACILITY_USER = 1
    FACILITY_MAIL = 2
    FACILITY_DAEMON = 3
    FACILITY_AUTH = 4
    FACILITY_SYSLOG = 5
    FACILITY_LPR = 6
    FACILITY_NEWS = 7
    FACILITY_UUCP = 8
    FACILITY_CRON = 9
    FACILITY_AUTHPRIV = 10
    FACILITY_FTP = 11
    FACILITY_LOCAL0 = 16
    FACILITY_LOCAL1 = 17
    FACILITY_LOCAL2 = 18
    FACILITY_LOCAL3 = 19
    FACILITY_LOCAL4 = 20
    FACILITY_LOCAL5 = 21
    FACILITY_LOCAL6 = 22
    FACILITY_LOCAL7 = 23

    # Severity levels
    SEVERITY_EMERGENCY = 0
    SEVERITY_ALERT = 1
    SEVERITY_CRITICAL = 2
    SEVERITY_ERROR = 3
    SEVERITY_WARNING = 4
    SEVERITY_NOTICE = 5
    SEVERITY_INFO = 6
    SEVERITY_DEBUG = 7

    def __init__(
        self,
        name: str,
        *,
        host: str = "localhost",
        port: int = 514,
        protocol: str = "udp",
        format: str = "rfc5424",
        facility: int = 16,  # LOCAL0
        severity: int = 6,  # INFO
        app_name: Optional[str] = None,
        procid: Optional[str] = None,
        retry_policy: RetryPolicy,
        buffer_size: int,
    ) -> None:
        super().__init__(name, retry_policy=retry_policy, buffer_size=buffer_size)
        self.host = host
        self.port = port
        self.protocol = protocol.lower()
        self.format = format.lower()
        self.facility = facility
        self.severity = severity
        self.app_name = app_name or "logforge"
        self.procid = procid
        self._socket: Optional[socket.socket] = None

    def _connect(self) -> None:
        """Establish connection to syslog server."""
        if self._socket:
            return

        if self.protocol == "tcp":
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.host, self.port))
        elif self.protocol == "udp":
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            raise ValueError(f"Unsupported protocol: {self.protocol}")

    def _format_rfc5424(self, event: str, metadata: Optional[Metadata] = None) -> bytes:
        """Format message according to RFC 5424."""
        # PRI = (Facility * 8) + Severity
        pri = (self.facility * 8) + self.severity

        # Timestamp in ISO 8601 format
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Hostname
        hostname = socket.gethostname()

        # App-name
        app_name = self.app_name or "-"

        # ProcID
        procid = self.procid or "-"

        # MsgID (optional, using generator name if available)
        msgid = "-"
        if metadata and "generator" in metadata:
            msgid = str(metadata["generator"])

        # Structured data (optional)
        sd = "-"
        if metadata:
            sd_parts = []
            for key, value in metadata.items():
                if key != "generator":  # Already in msgid
                    sd_parts.append(f'{key}="{value}"')
            if sd_parts:
                sd = f"[logforge@12345 {' '.join(sd_parts)}]"

        # Message
        message = event

        # RFC 5424 format: <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
        formatted = (
            f"<{pri}>1 {timestamp} {hostname} {app_name} {procid} {msgid} {sd} {message}"
        )
        return formatted.encode("utf-8")

    def _format_rfc3164(self, event: str, metadata: Optional[Metadata] = None) -> bytes:
        """Format message according to RFC 3164 (BSD syslog)."""
        # PRI = (Facility * 8) + Severity
        pri = (self.facility * 8) + self.severity

        # Timestamp (MMM DD HH:MM:SS)
        now = datetime.now()
        timestamp = now.strftime("%b %d %H:%M:%S")

        # Hostname
        hostname = socket.gethostname()

        # Tag (app-name)
        tag = self.app_name or "logforge"

        # Message
        message = event
        if metadata:
            meta_str = " ".join(f"{k}={v}" for k, v in metadata.items())
            message = f"{event} {meta_str}"

        # RFC 3164 format: <PRI>TIMESTAMP HOSTNAME TAG: MESSAGE
        formatted = f"<{pri}>{timestamp} {hostname} {tag}: {message}"
        return formatted.encode("utf-8")

    def _send(self, event: str, metadata: Optional[Metadata] = None) -> None:
        """Send event to syslog server."""
        self._connect()
        if not self._socket:
            raise RuntimeError("Failed to establish syslog connection")

        if self.format == "rfc5424":
            message = self._format_rfc5424(event, metadata)
        elif self.format == "rfc3164":
            message = self._format_rfc3164(event, metadata)
        else:
            raise ValueError(f"Unsupported syslog format: {self.format}")

        if self.protocol == "udp":
            self._socket.sendto(message, (self.host, self.port))
        else:  # TCP
            self._socket.sendall(message + b"\n")


__all__ = ["SyslogOutput"]
