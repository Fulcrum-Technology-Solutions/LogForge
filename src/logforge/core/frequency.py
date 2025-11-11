from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Dict, List, Optional


def _match_day(now: datetime, days: List[int]) -> bool:
    weekday = now.isoweekday()
    return weekday in days


def _parse_time_range(value: str) -> Optional[tuple[time, time]]:
    try:
        start_str, end_str = value.split("-")
        start_parts = [int(part) for part in start_str.split(":")]
        end_parts = [int(part) for part in end_str.split(":")]
        return time(*start_parts), time(*end_parts)
    except Exception:
        return None


def _match_time(now: datetime, time_range: Optional[str]) -> bool:
    if not time_range:
        return True
    parsed = _parse_time_range(time_range)
    if not parsed:
        return False
    start, end = parsed
    current = now.time()
    return start <= current <= end


class FrequencyController:
    def __init__(self, frequency_config: Dict) -> None:
        self.base_rate = frequency_config.get("base_rate", 1)
        self.variations = frequency_config.get("variation", [])

    def current_rate(self, now: Optional[datetime] = None) -> float:
        now = now or datetime.now(timezone.utc)
        rate = float(self.base_rate)
        for variation in self.variations:
            days = variation.get("days", list(range(1, 8)))
            time_range = variation.get("time")
            multiplier = variation.get("multiplier", 1.0)
            if multiplier is None:
                continue
            if _match_day(now, days) and _match_time(now, time_range):
                rate *= float(multiplier)
        return max(rate, 0.0)
