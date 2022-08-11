"""Module containing the Timeframe class."""

from __future__ import annotations

from string import ascii_letters

from dateutil.relativedelta import relativedelta

from ohlcv.timeunit import TimeUnit
from ohlcv.typing import Number


__all__ = [
    # Class exports
    "Timeframe",
]


class Timeframe:
    """Object representation of a timeframe.

    Example:
    ```python
    timeframe_1 = Timeframe("1h")
    timeframe_2 = Timeframe(interval=1, unit="h")
    timeframe_3 = Timeframe(timeframe_1)

    # These three are equal
    assert timeframe_1 == timeframe_2 == timeframe_3

    # These are equal as well
    assert Timeframe("1d") == Timeframe("24h")
    ```

    Arguments:
        interval: This can be the actual interval of the timeframe
            as an `int` or `float`. It can also be used to input an
            existing `Timeframe` object or a string containing the
            interval and the unit of the timeframe.
        unit: The unit of the timeframe. Used only if the value of
            the `interval` argument is an `int` or `float`.

    Raises:
        ValueError: If the input timeframe interval and/or unit is
            invalid or is not parseable.

    Attribute:
        interval: The integer interval of the timeframe. There are times
            where the `OHLCV` class tries to automatically detect
            the timeframe. In the case where it can't detect it,
            the value of the interval is `None`.
    """

    def __init__(
        self,
        interval: Timeframe | str | Number | None = None,
        unit: TimeUnit | str | None = None,
    ):
        # `interval` is non-existent, so let's just assign `None` internally
        # this only applies to the interval argument. Having a `None` unit
        # doesn't necessarily mean that we assign `None` to everything.
        if interval is None:
            self.interval = None
            self.unit = None
            return

        # Raise `TypeError` if `interval` is not one of the expected types
        if not isinstance(interval, (str, int, float, Timeframe)):
            raise TypeError(
                f"{self.__class__.__name__}() interval argument must be a "
                f"string, a number, or a {self.__class__.__name__}, "
                "not '{type(interval).__name__}'"
            )

        # Raise `TypeError` if `unit` is not one of the expected types
        if unit and not isinstance(unit, str):
            raise TypeError(
                f"{self.__class__.__name__}() unit argument must be a "
                f"string, not '{type(interval).__name__}'"
            )

        # Input is another `Timeframe` object, let's extract the
        # internal components and assign them to the new timeframe
        if isinstance(interval, Timeframe):
            self.interval = interval.interval
            self.unit = interval.unit
            return

        # Make sure the `unit` argument is provided if interval
        # is a float or an integer data type
        if isinstance(interval, (float, int)):
            if not unit:
                raise ValueError(
                    "unit argument is required if interval is a number"
                )

            self.interval = interval
            self.unit = unit
            return

        # Check if the Interval is a numbers only: remove any
        # letters at the right side of the interval, if the remainder
        # is not all digits then it's not a valid interval
        numbers_only_interval = interval.rstrip(ascii_letters)
        if not numbers_only_interval.replace(".", "").isdigit():
            raise ValueError(
                f"Invalid timeframe interval: {numbers_only_interval}"
            )

        # Only allow one dot in the original `numbers_only_interval`
        if numbers_only_interval.count(".") > 1:
            raise ValueError(
                f"Invalid timeframe interval: {numbers_only_interval}"
            )

        # Retrieve the unit from `interval`. This could be an empty
        # string if `interval` is purely the interval or it could
        # be a string if the `interval` includes the unit.
        unit_from_interval = interval.replace(numbers_only_interval, "")
        if unit_from_interval:
            self.interval = numbers_only_interval
            self.unit = unit_from_interval
            return

        # Prioritize usage of `unit_from_interval`. Only use the `unit`
        # argument only if `unit_from_interval` is empty.
        if unit and not unit_from_interval:
            self.interval = numbers_only_interval
            self.unit = unit
            return

        # Not sure if this case is ever going to be reached
        raise ValueError(f"Invalid timeframe: {(interval, unit)}")

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        properties = ["interval", "unit"]
        return (
            f"{self.__class__.__name__}("
            + ", ".join([f"{p}={getattr(self, p)!r}" for p in properties])
            + ")"
        )

    def __str__(self):
        return (
            f"{self.interval if self.interval else 0}"
            f"{self.unit if self.unit else ''}"
        )

    def __bool__(self):
        return bool(self.interval and self.unit and self.interval != 0)

    def __eq__(self, other):
        if not isinstance(other, Timeframe):
            other = Timeframe(other)
        if bool(self) and bool(other):
            return self.get_duration() == other.get_duration()
        return str(self) == str(other)

    def get_duration(self, unit: str = "ms") -> Number:
        """Get the duration of the timeframe in the target unit.

        Arguments:
            unit: The target unit of time that we want the duration
                in. Valid input values are `"y"`, `"M"`, `"w"`, `"d"`,
                `"h"`, `"m"`, `"s"`, and `"ms"`.

        Return:
            A floating number representing the duration of the
            timeframe in the target unit of time. If the target unit
            is "milliseconds" then the return type is an integer.
        """
        if not self.interval or not self.unit:
            return 0

        duration_in_seconds = self.unit.to_seconds()
        duration_in_seconds *= self.interval

        # Convert target unit to our standard class
        target_unit = TimeUnit(unit)

        duration_in_target_unit = target_unit.to_seconds()
        duration_in_target_unit = 1 / duration_in_target_unit
        duration_in_target_unit *= duration_in_seconds

        # Type casting function: int for milliseconds, float for others
        type_fn = int if unit == TimeUnit.MILLISECOND else float

        return type_fn(duration_in_target_unit)

    def to_timedelta(self) -> relativedelta:
        """Returns the equivalent timedelta object of the timeframe."""

        # Month and year is not accepted as timedelta key arguments
        # so we need to cover them specifically. Note that these
        # timedeltas are not accurate because we don't take into
        # account leap years and all those edge cases.

        if self.unit == TimeUnit.MONTH:
            return relativedelta(days=(365 / 12.0) * self.interval)

        if self.unit == TimeUnit.YEAR:
            return relativedelta(days=365 * self.interval)

        if self.unit == TimeUnit.MILLISECOND:
            return relativedelta(microseconds=int(self.interval * 1_000))

        return relativedelta(
            **{f"{self.unit.to_word()}s": self.get_duration(unit=self.unit)}
        )

    @property
    def interval(self) -> int:
        return self._interval

    @interval.setter
    def interval(self, value: str | Number | None):
        if not value and value != 0:
            self._interval = None
            self.unit = None
        else:
            try:
                self._interval = int(float(value))
            except (TypeError, ValueError):
                self._interval = None
                self.unit = None

    @property
    def unit(self) -> TimeUnit:
        if self._unit._unit is None:
            return None
        return self._unit

    @unit.setter
    def unit(self, value: TimeUnit | str | None):
        self._unit = TimeUnit(value)
