from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


class OutputHandler(ABC):
    @abstractmethod
    def write(self, event: str) -> None:
        raise NotImplementedError

    def write_batch(self, events: Iterable[str]) -> None:
        for event in events:
            self.write(event)

    def close(self) -> None:
        ...
