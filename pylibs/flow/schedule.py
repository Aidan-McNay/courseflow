"""Specifications of when flows should run.

Author: Aidan McNay
Date: January 6th, 2025
"""

from datetime import datetime
from typing import Callable

# -----------------------------------------------------------------------------
# Schedule
# -----------------------------------------------------------------------------


class Schedule:
    """A schedule that determines when an associated flow should run."""

    def __init__(
        self: "Schedule", check_time: Callable[[datetime], bool]
    ) -> None:
        """Initialize the schedule with a member to check the time.

        Args:
            check_time (Callable[[datetime], bool]):
              A function that takes in the current time, and determines
              whether the flow should be run. This function can assume
              that the given time is rounded to the nearest minute
        """
        self.check_time = check_time

    def _curr_time(self: "Schedule") -> datetime:
        """Get the current time, rounded down to the minute."""
        return datetime.now().replace(second=0, microsecond=0)

    def should_run(self: "Schedule") -> bool:
        """Check whether a flow should be run, based on the current time.

        Returns:
            bool: Whether the associated flow should run
        """
        return self.check_time(self._curr_time())

    def __add__(self: "Schedule", other: "Schedule") -> "Schedule":
        """Add two schedules to get the union of the two schedules.

        Args:
            other (Schedule): The other schedule to add to

        Returns:
            Schedule: The union of the two schedules
        """
        return Schedule(lambda x: self.check_time(x) or other.check_time(x))

    def __sub__(self: "Schedule", other: "Schedule") -> "Schedule":
        """Subtract two schedules to get the difference of the two schedules.

        Args:
            other (Schedule): The other schedule to subtract from the current

        Returns:
            Schedule: The difference of the two schedules
        """
        return Schedule(
            lambda x: self.check_time(x) and (not other.check_time(x))
        )


# -----------------------------------------------------------------------------
# Always
# -----------------------------------------------------------------------------


class Always(Schedule):
    """A schedule to always run a flow."""

    def __init__(self: "Always") -> None:
        """Initialize the schedule to always run."""
        super().__init__(lambda x: True)


# -----------------------------------------------------------------------------
# Hourly
# -----------------------------------------------------------------------------


def check_hourly_time(curr_time: datetime) -> bool:
    """Check whether it's currently the top of the hour.

    Args:
        curr_time (datetime): The current time, rounded down to the minute

    Returns:
        bool: Whether it's the top of the hour
    """
    return curr_time.minute == 0


class Hourly(Schedule):
    """A schedule to run a flow each hour."""

    def __init__(self: "Hourly") -> None:
        """Initialize the hourly schedule."""
        super().__init__(check_hourly_time)


# -----------------------------------------------------------------------------
# Daily
# -----------------------------------------------------------------------------


def check_daily_time(curr_time: datetime, hour: int) -> bool:
    """Check whether it's currently the top of the specified hour.

    Args:
        curr_time (datetime): The current time, rounded down to the minute
        day_of_week (int): The hour to run at

    Returns:
        bool: Whether it's the top of the specified hour
    """
    return check_hourly_time(curr_time) and curr_time.hour == hour


class Daily(Schedule):
    """A schedule to run a flow once a day."""

    def __init__(self: "Daily", hour: int) -> None:
        """Initialize the daily schedule with the specified hour.

        Args:
            hour (int): The hour to run on in 24-hour time (0-23)
        """
        if hour < 0 or hour > 23:
            raise Exception(f"Invalid hour: {hour}")
        check_time = lambda x: check_daily_time(x, hour)
        super().__init__(check_time)


# -----------------------------------------------------------------------------
# Weekly
# -----------------------------------------------------------------------------


def check_weekly_time(curr_time: datetime, day_of_week: int, hour: int) -> bool:
    """Check whether it's currently the top of the specified hour of a day.

    Args:
        curr_time (datetime): The current time, rounded down to the minute
        day_of_week (int): The day to run on
        hour (int): The hour to run on

    Returns:
        bool: Whether it's the top of the specified hour of a day
    """
    return (
        check_daily_time(curr_time, hour) and curr_time.weekday() == day_of_week
    )


WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


class Weekly(Schedule):
    """A schedule to run a flow once a week."""

    def __init__(self: "Weekly", day: str, hour: int) -> None:
        """Initialize the weekly schedule with the specified hour and day.

        Args:
            day (str): The day of the week to run on
            hour (int): The hour to run on in 24-hour time (0-23)
        """
        if hour < 0 or hour > 23:
            raise Exception(f"Invalid hour: {hour}")
        day_lower = day.lower()
        if day_lower not in WEEKDAYS:
            raise Exception(f"Invalid day of the week: {day}")
        day_of_week = WEEKDAYS.index(day_lower)
        check_time = lambda x: check_weekly_time(x, day_of_week, hour)
        super().__init__(check_time)
