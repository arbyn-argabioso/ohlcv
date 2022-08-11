"""Module containing the TimeUnit class."""

from __future__ import annotations


__all__ = [
    # Class exports
    "TimeUnit",
]


class TimeUnit:
    """Data class for timeframe units."""

    YEAR = "y"
    MONTH = "M"
    WEEK = "w"
    DAY = "d"
    HOUR = "h"
    MINUTE = "m"
    SECOND = "s"
    MILLISECOND = "ms"

    UNIT_TO_SECONDS_MAPPING = {
        YEAR: 60 * 60 * 24 * 365,
        MONTH: 60 * 60 * 24 * 30,
        WEEK: 60 * 60 * 24 * 7,
        DAY: 60 * 60 * 24,
        HOUR: 60 * 60,
        MINUTE: 60,
        SECOND: 1,
        MILLISECOND: 1 / 1000,
    }

    WORD_UNITS_MAPPING = {
        YEAR: "year",
        MONTH: "month",
        WEEK: "week",
        DAY: "day",
        HOUR: "hour",
        MINUTE: "minute",
        SECOND: "second",
        MILLISECOND: "millisecond",
    }

    ADJECTIVE_UNITS_MAPPING = {
        YEAR: "yearly",
        MONTH: "monthly",
        WEEK: "weekly",
        DAY: "daily",
        HOUR: "hourly",
        MINUTE: WORD_UNITS_MAPPING[MINUTE],
        SECOND: WORD_UNITS_MAPPING[SECOND],
        MILLISECOND: WORD_UNITS_MAPPING[MILLISECOND],
    }

    PANDAS_OFFSET_UNITS_MAPPING = {
        YEAR: "Y",
        MONTH: "M",
        WEEK: "W",
        DAY: "D",
        HOUR: "H",
        MINUTE: "T",
        SECOND: "S",
        MILLISECOND: "L",
    }

    def __init__(self, unit: TimeUnit | str | None = None):
        # Input is None, so let's just assign None internally
        if not unit and unit != 0:
            self._unit = None
            return

        if not isinstance(unit, (TimeUnit, str)):
            raise TypeError(
                f"{self.__class__.__name__}() argument must be a "
                f"string or a {self.__class__.__name__}, "
                f"not '{type(unit).__name__}'"
            )

        # Input is possibly a string but its not in our
        # list of valid string units
        if str(unit) not in self.UNIT_TO_SECONDS_MAPPING:
            raise ValueError(f"Invalid timeframe unit: {unit}")

        self._unit = str(unit)

    def __hash__(self):
        return hash(self._unit)

    def __repr__(self):
        return repr(self._unit)

    def __str__(self):
        return str(self._unit)

    def __bool__(self):
        return bool(self._unit)

    def __eq__(self, other):
        if self._unit:
            return str(self) == str(other)
        return other is None

    def to_seconds(self):
        return self.UNIT_TO_SECONDS_MAPPING.get(self._unit, 0)

    def to_word(self):
        return self.WORD_UNITS_MAPPING.get(self._unit)

    def to_adjective(self):
        return self.ADJECTIVE_UNITS_MAPPING.get(self._unit)

    def to_pandas(self):
        return self.PANDAS_OFFSET_UNITS_MAPPING.get(self._unit)
