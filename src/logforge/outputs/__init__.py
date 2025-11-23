from __future__ import annotations

import sys
from typing import Mapping

from logforge.core.config_schema import OutputDefinition
from logforge.outputs.base import BaseOutput, RetryPolicy
from logforge.outputs.console import ConsoleOutput
from logforge.outputs.file import FileOutput
from logforge.outputs.http import HttpOutput
from logforge.outputs.syslog import SyslogOutput
from logforge.outputs.tcp import TcpOutput


def build_output(
    definition: OutputDefinition,
    *,
    generator_name: str,
    retry_policy: Mapping[str, float | int],
    buffer_size: int,
) -> BaseOutput:
    """Instantiate an output handler from a configuration definition."""

    policy = RetryPolicy.from_config(retry_policy)
    output_type = definition.type
    if output_type == "file":
        if not definition.path:
            raise ValueError("File outputs require a 'path'.")
        return FileOutput(
            definition.name,
            path_template=definition.path,
            generator_name=generator_name,
            rotation=definition.rotation,
            retry_policy=policy,
            buffer_size=buffer_size,
        )
    if output_type == "console":
        stream_name = (definition.stream or "stdout").lower()
        stream = sys.stderr if stream_name == "stderr" else sys.stdout
        return ConsoleOutput(
            definition.name,
            stream=stream,
            format=definition.format or "plain",
            retry_policy=policy,
            buffer_size=buffer_size,
        )
    if output_type == "http":
        if not definition.url:
            raise ValueError("HTTP outputs require 'url'.")
        return HttpOutput(
            definition.name,
            url=definition.url,
            method=definition.method or "POST",
            headers=definition.headers,
            retry_policy=policy,
            buffer_size=buffer_size,
        )
    if output_type == "tcp":
        if not definition.host or not definition.port:
            raise ValueError("TCP outputs require 'host' and 'port'.")
        return TcpOutput(
            definition.name,
            host=definition.host,
            port=definition.port,
            delimiter=definition.delimiter or "\n",
            retry_policy=policy,
            buffer_size=buffer_size,
        )
    if output_type == "syslog":
        if not definition.host or not definition.port:
            raise ValueError("Syslog outputs require 'host' and 'port'.")
        return SyslogOutput(
            definition.name,
            host=definition.host,
            port=definition.port,
            protocol=definition.protocol or "udp",
            retry_policy=policy,
            buffer_size=buffer_size,
        )
    raise ValueError(f"Unsupported output type '{output_type}'.")


__all__ = [
    "build_output",
    "BaseOutput",
    "ConsoleOutput",
    "FileOutput",
    "HttpOutput",
    "TcpOutput",
    "SyslogOutput",
]
