from __future__ import annotations

from datetime import datetime

from logforge.core.config_schema import FrequencyConfig, FrequencyVariationConfig
from logforge.core.frequency import FrequencyController


def test_frequency_controller_base_rate() -> None:
    controller = FrequencyController(FrequencyConfig(base_rate=5))
    assert controller.current_rate(now=datetime(2024, 1, 1, 12, 0, 0)) == 5


def test_frequency_controller_applies_variations() -> None:
    controller = FrequencyController(
        FrequencyConfig(
            base_rate=10,
            variation=[
                FrequencyVariationConfig(days=[1, 2, 3], time="09:00-17:00", multiplier=2.0),
                FrequencyVariationConfig(days=[1], time="12:00-13:00", multiplier=0.5),
            ],
        )
    )
    rate_morning = controller.current_rate(now=datetime(2024, 1, 1, 10, 0, 0))
    rate_lunch = controller.current_rate(now=datetime(2024, 1, 1, 12, 30, 0))
    rate_evening = controller.current_rate(now=datetime(2024, 1, 1, 20, 0, 0))
    assert rate_morning == 20
    assert rate_lunch == 10  # 10 * 2 * 0.5
    assert rate_evening == 10
