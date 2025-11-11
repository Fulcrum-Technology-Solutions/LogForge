from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Iterable, Sequence


def now() -> datetime:
    return datetime.now(timezone.utc)


def format_datetime(value: datetime, fmt: str = "%Y-%m-%dT%H:%M:%S.%fZ") -> str:
    return value.astimezone(timezone.utc).strftime(fmt)


def random_int(min_value: int, max_value: int) -> int:
    return random.randint(min_value, max_value)


def random_choice(options: Sequence) -> object:
    if not options:
        raise ValueError("random_choice requires at least one option")
    return random.choice(list(options))
