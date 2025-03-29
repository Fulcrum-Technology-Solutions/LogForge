"""Scheduler for time-based patterns in log generation."""

import datetime
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


class DayOfWeek(Enum):
    """Enum for days of the week."""
    
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass
class TimePattern:
    """Pattern for time-based log generation.
    
    Attributes:
        name: The name of the time pattern
        base_frequency: The base frequency in entries per second
        start_time: The start time of the pattern (HH:MM format)
        end_time: The end time of the pattern (HH:MM format)
        days_of_week: The days of the week the pattern is active
        multiplier: The multiplier to apply to the base frequency during the pattern
    """
    
    name: str
    base_frequency: float
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format
    days_of_week: List[DayOfWeek] = None
    multiplier: float = 1.0
    
    def __post_init__(self):
        """Initialize the pattern."""
        if self.days_of_week is None:
            # Default to all days
            self.days_of_week = [day for day in DayOfWeek]
            
    def is_active(self, now: Optional[datetime.datetime] = None) -> bool:
        """Check if the pattern is active at the given time.
        
        Args:
            now: The time to check against (defaults to current time)
            
        Returns:
            True if the pattern is active, False otherwise
        """
        if now is None:
            now = datetime.datetime.now()
            
        # Check if current day is in days_of_week
        current_day = DayOfWeek(now.weekday())
        if current_day not in self.days_of_week:
            return False
            
        # Parse start and end times
        start_hour, start_minute = map(int, self.start_time.split(':'))
        end_hour, end_minute = map(int, self.end_time.split(':'))
        
        start_time = datetime.time(hour=start_hour, minute=start_minute)
        end_time = datetime.time(hour=end_hour, minute=end_minute)
        
        # Handle overnight patterns (where end time is before start time)
        current_time = now.time()
        if start_time <= end_time:
            # Normal case: start_time <= current_time <= end_time
            return start_time <= current_time <= end_time
        else:
            # Overnight case: current_time >= start_time OR current_time <= end_time
            return current_time >= start_time or current_time <= end_time


class Scheduler:
    """Scheduler for time-based patterns in log generation."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.patterns: Dict[str, TimePattern] = {}
        
    def add_pattern(self, pattern: TimePattern):
        """Add a time pattern.
        
        Args:
            pattern: The pattern to add
        """
        logger.info(f"Adding time pattern: {pattern.name}")
        self.patterns[pattern.name] = pattern
        
    def get_multiplier(self, pattern_names: List[str], now: Optional[datetime.datetime] = None) -> float:
        """Get the multiplier for a set of patterns.
        
        Args:
            pattern_names: The names of the patterns to check
            now: The time to check against (defaults to current time)
            
        Returns:
            The multiplier to apply to the base frequency
        """
        if now is None:
            now = datetime.datetime.now()
            
        # Start with a default multiplier of 1.0
        multiplier = 1.0
        
        # Apply multipliers from all active patterns
        for name in pattern_names:
            if name in self.patterns and self.patterns[name].is_active(now):
                multiplier *= self.patterns[name].multiplier
                
        return multiplier