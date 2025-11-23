from __future__ import annotations

import datetime
from typing import List, Optional

from logforge.core.config import FrequencyVariation as FrequencyVariationConfig


class FrequencyProfile:
    def __init__(self, base_rate: int, variations: Optional[List[FrequencyVariationConfig]] = None) -> None:
        self._base_rate = base_rate
        self._variations = variations or []

    def current_rate(self, now: Optional[datetime.datetime] = None) -> int:
        now = now or datetime.datetime.utcnow()
        weekday = now.isoweekday()
        current_multiplier = 1.0
        for variation in self._variations:
            if variation.days and weekday not in variation.days:
                continue
            if variation.time and not self._time_in_range(now, variation.time):
                continue
            current_multiplier *= variation.multiplier
        return max(int(self._base_rate * current_multiplier), 0)

    @staticmethod
    def _time_in_range(now: datetime.datetime, time_range: str) -> bool:
        try:
            start_str, end_str = time_range.split("-")
            start = datetime.datetime.strptime(start_str, "%H:%M").time()
            end = datetime.datetime.strptime(end_str, "%H:%M").time()
        except ValueError:
            return False
        current = now.time()
        if start <= end:
            return start <= current <= end
        return current >= start or current <= end

