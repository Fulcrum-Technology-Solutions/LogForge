"""Custom Jinja filters and helper functions."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Iterable


def format_datetime(value: datetime, fmt: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
    return value.strftime(fmt)


def current_timestamp() -> datetime:
    return datetime.now(timezone.utc)


def timestamp_to_iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat()


def random_int(min_value: int, max_value: int) -> int:
    return random.randint(min_value, max_value)


def random_choice(values: Iterable[Any]) -> Any:
    values = list(values)
    if not values:
        return None
    return random.choice(values)


def random_string(length: int, alphabet: str = "abcdefghijklmnopqrstuvwxyz") -> str:
    return "".join(random.choice(alphabet) for _ in range(length))


def register_filters(env) -> None:
    env.filters["format_datetime"] = format_datetime
    env.filters["timestamp_to_iso"] = timestamp_to_iso
    env.globals.update(
        {
            "now": current_timestamp,
            "random_int": random_int,
            "random_choice": random_choice,
            "random_string": random_string,
        }
    )


__all__ = [
    "register_filters",
    "format_datetime",
    "timestamp_to_iso",
    "current_timestamp",
    "random_int",
    "random_choice",
    "random_string",
]
