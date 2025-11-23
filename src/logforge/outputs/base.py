"""Output handler base classes."""
from __future__ import annotations

import abc
from typing import Any, Mapping

Metadata = Mapping[str, Any] | None


class BaseOutput(abc.ABC):
    """Abstract base class for all output handlers."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    def emit(self, event: str, metadata: Metadata = None) -> None:
        """Send the rendered event to the destination."""


class CapturingOutput(BaseOutput):
    """Simple in-memory output used for testing."""

    def __init__(self, name: str = "capture") -> None:
        super().__init__(name)
        self.events: list[str] = []

    def emit(self, event: str, metadata: Metadata = None) -> None:
        self.events.append(event)


__all__ = ["BaseOutput", "CapturingOutput", "Metadata"]
