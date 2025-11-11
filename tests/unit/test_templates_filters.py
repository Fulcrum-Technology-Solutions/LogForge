from __future__ import annotations

from datetime import datetime, timezone

from logforge.templates import filters


def test_now_returns_datetime() -> None:
    value = filters.now()
    assert isinstance(value, datetime)


def test_random_int_and_choice() -> None:
    number = filters.random_int(1, 1)
    assert number == 1
    choice = filters.random_choice(["a"])
    assert choice == "a"


def test_format_datetime() -> None:
    dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    formatted = filters.format_datetime(dt, "%Y")
    assert formatted == "2024"
