"""Frequency calculation utilities for generators."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Optional

from logforge.core.config_schema import FrequencyConfig, FrequencyVariationConfig


def _parse_time_window(value: str) -> tuple[time, time]:
    """Parse a HH:MM-HH:MM formatted window."""

    start_text, end_text = value.split("-", 1)
    return _parse_time(start_text), _parse_time(end_text)


def _parse_time(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


def _time_in_window(now: time, start: time, end: time) -> bool:
    if start <= end:
        return start <= now <= end
    # window spans midnight
    return now >= start or now <= end


@dataclass
class FrequencyController:
    """Computes the effective events-per-second rate for a generator."""

    config: FrequencyConfig

    def __post_init__(self) -> None:
        self._variations: list[FrequencyVariationConfig] = list(self.config.variation or [])

    def current_rate(self, *, now: Optional[datetime] = None) -> int:
        """Return the effective rate for the current moment."""

        moment = now or datetime.now(timezone.utc)
        multiplier = 1.0
        for variation in self._variations:
            if self._variation_matches(moment, variation):
                multiplier *= variation.multiplier
        rate = int(max(1, round(self.config.base_rate * multiplier)))
        return rate

    def _variation_matches(self, moment: datetime, variation: FrequencyVariationConfig) -> bool:
        if variation.days and moment.isoweekday() not in variation.days:
            return False
        if variation.time:
            start, end = _parse_time_window(variation.time)
            if not _time_in_window(moment.time(), start, end):
                return False
        return True


__all__ = ["FrequencyController"]
