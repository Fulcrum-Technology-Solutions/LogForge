"""Tests for the scheduler module."""

import datetime
import pytest
from freezegun import freeze_time
from synth_logs.core.scheduler import Scheduler, TimePattern, DayOfWeek


class TestTimePattern:
    """Test the TimePattern class."""
    
    def test_pattern_initialization(self):
        """Test creating a TimePattern object."""
        pattern = TimePattern(
            name="test_pattern",
            base_frequency=1.0,
            start_time="09:00",
            end_time="17:00",
            days_of_week=[DayOfWeek.MONDAY, DayOfWeek.TUESDAY],
            multiplier=2.0
        )
        
        assert pattern.name == "test_pattern"
        assert pattern.base_frequency == 1.0
        assert pattern.start_time == "09:00"
        assert pattern.end_time == "17:00"
        assert DayOfWeek.MONDAY in pattern.days_of_week
        assert DayOfWeek.TUESDAY in pattern.days_of_week
        assert pattern.multiplier == 2.0
        
    @freeze_time("2023-03-06 12:00:00")  # Monday at noon
    def test_is_active_within_time_range(self):
        """Test is_active method when time is within range."""
        pattern = TimePattern(
            name="business_hours",
            base_frequency=1.0,
            start_time="09:00",
            end_time="17:00",
            days_of_week=[DayOfWeek.MONDAY],
            multiplier=2.0
        )
        
        assert pattern.is_active() is True
        
    @freeze_time("2023-03-06 08:00:00")  # Monday at 8am
    def test_is_active_outside_time_range(self):
        """Test is_active method when time is outside range."""
        pattern = TimePattern(
            name="business_hours",
            base_frequency=1.0,
            start_time="09:00",
            end_time="17:00",
            days_of_week=[DayOfWeek.MONDAY],
            multiplier=2.0
        )
        
        assert pattern.is_active() is False
        
    @freeze_time("2023-03-07 12:00:00")  # Tuesday at noon
    def test_is_active_different_day(self):
        """Test is_active method on different day."""
        pattern = TimePattern(
            name="business_hours",
            base_frequency=1.0,
            start_time="09:00",
            end_time="17:00",
            days_of_week=[DayOfWeek.MONDAY],  # Only Monday
            multiplier=2.0
        )
        
        assert pattern.is_active() is False
        
    @freeze_time("2023-03-06 12:00:00")  # Monday at noon
    def test_is_active_no_days_specified(self):
        """Test is_active method when no days are specified."""
        pattern = TimePattern(
            name="business_hours",
            base_frequency=1.0,
            start_time="09:00",
            end_time="17:00",
            days_of_week=None,  # No days specified
            multiplier=2.0
        )
        
        # Should be active since we're in time range and no days are specified
        assert pattern.is_active() is True
        
    @freeze_time("2023-03-06 12:00:00")  # Monday at noon
    def test_get_multiplier_active(self):
        """Test get_multiplier when pattern is active."""
        pattern = TimePattern(
            name="business_hours",
            base_frequency=1.0,
            start_time="09:00",
            end_time="17:00",
            days_of_week=[DayOfWeek.MONDAY],
            multiplier=2.0
        )
        
        assert pattern.get_multiplier() == 2.0
        
    @freeze_time("2023-03-06 08:00:00")  # Monday at 8am
    def test_get_multiplier_inactive(self):
        """Test get_multiplier when pattern is inactive."""
        pattern = TimePattern(
            name="business_hours",
            base_frequency=1.0,
            start_time="09:00",
            end_time="17:00",
            days_of_week=[DayOfWeek.MONDAY],
            multiplier=2.0
        )
        
        assert pattern.get_multiplier() == 1.0  # Default multiplier when inactive


class TestScheduler:
    """Test the Scheduler class."""
    
    def test_initialization(self):
        """Test initializing a Scheduler."""
        scheduler = Scheduler()
        assert scheduler.patterns == []
        
    def test_add_pattern(self):
        """Test adding a pattern to the scheduler."""
        scheduler = Scheduler()
        pattern = TimePattern(
            name="test_pattern",
            base_frequency=1.0,
            start_time="09:00",
            end_time="17:00"
        )
        
        scheduler.add_pattern(pattern)
        assert len(scheduler.patterns) == 1
        assert scheduler.patterns[0] == pattern
        
    @freeze_time("2023-03-06 12:00:00")  # Monday at noon
    def test_get_current_multiplier_single_pattern(self):
        """Test get_current_multiplier with a single active pattern."""
        scheduler = Scheduler()
        
        # Add a pattern that's active during the test time
        pattern = TimePattern(
            name="business_hours",
            base_frequency=1.0,
            start_time="09:00",
            end_time="17:00",
            days_of_week=[DayOfWeek.MONDAY],
            multiplier=2.0
        )
        scheduler.add_pattern(pattern)
        
        # Should use the pattern's multiplier
        assert scheduler.get_current_multiplier() == 2.0
        
    @freeze_time("2023-03-06 20:00:00")  # Monday at 8pm
    def test_get_current_multiplier_no_active_patterns(self):
        """Test get_current_multiplier with no active patterns."""
        scheduler = Scheduler()
        
        # Add a pattern that's not active during the test time
        pattern = TimePattern(
            name="business_hours",
            base_frequency=1.0,
            start_time="09:00",
            end_time="17:00",
            days_of_week=[DayOfWeek.MONDAY],
            multiplier=2.0
        )
        scheduler.add_pattern(pattern)
        
        # Should use the default multiplier of 1.0
        assert scheduler.get_current_multiplier() == 1.0
        
    @freeze_time("2023-03-06 12:00:00")  # Monday at noon
    def test_get_current_multiplier_multiple_patterns(self):
        """Test get_current_multiplier with multiple active patterns."""
        scheduler = Scheduler()
        
        # Add two patterns that are active during the test time
        pattern1 = TimePattern(
            name="business_hours",
            base_frequency=1.0,
            start_time="09:00",
            end_time="17:00",
            days_of_week=[DayOfWeek.MONDAY],
            multiplier=2.0
        )
        
        pattern2 = TimePattern(
            name="monday_boost",
            base_frequency=1.0,
            start_time="00:00",
            end_time="23:59",
            days_of_week=[DayOfWeek.MONDAY],
            multiplier=1.5
        )
        
        scheduler.add_pattern(pattern1)
        scheduler.add_pattern(pattern2)
        
        # Should multiply the multipliers: 2.0 * 1.5 = 3.0
        assert scheduler.get_current_multiplier() == 3.0
        
    @freeze_time("2023-03-06 12:00:00")  # Monday at noon
    def test_get_current_multiplier_empty_scheduler(self):
        """Test get_current_multiplier with no patterns."""
        scheduler = Scheduler()
        
        # Should use the default multiplier of 1.0
        assert scheduler.get_current_multiplier() == 1.0