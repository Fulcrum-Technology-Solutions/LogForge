from __future__ import annotations

from datetime import datetime, timezone

from logforge.core.frequency import FrequencyController


def test_frequency_controller_variation() -> None:
    config = {
        "base_rate": 10,
        "variation": [
            {"days": [datetime.now(timezone.utc).isoweekday()], "multiplier": 2.0},
        ],
    }
    controller = FrequencyController(config)
    rate = controller.current_rate(datetime.now(timezone.utc))
    assert rate == 20
