"""Module containing datetime-related utility functions."""

from __future__ import annotations

import datetime as dtlib

from dateutil import parser as dtparser

from ohlcv.timeframe import Timeframe


BITCOIN_START = "2009-01-01 00:00:00+00:00"


__all__ = [
    # Constant exports
    "BITCOIN_START",

    # Function exports
    "get_valid_start_end",
    "get_datetime",
    "get_iso8601",
    "get_milliseconds",
    "get_seconds",
]


def get_valid_start_end(
    start: dtlib.datetime | str | int | None,
    end: dtlib.datetime | str | int | None,
    timeframe: Timeframe,
    *,
    timeframe_multiplier: int = 1,
    include_latest: bool = True,
    available_start: dtlib.datetime | str | int | None = None,
    now: dtlib.datetime | None = None,
) -> tuple[dtlib.datetime, dtlib.datetime]:
    """Validates and fills up the start and end times.

    Since we want the user to be able to readily use the `start`
    and `end` variables without thinking much about this small detail,
    we automatically fill up the starting and end timestamps
    based on the parameters provided. Here are the different
    fill up cases:

    * If `start` and `end` are not provided, `end` is assigned the
      latest date and `start` is `end` minus the time-equivalent of the
      timeframe multiplied by `timeframe_multiplier`.
    * If either `start` and `end` are not provided but the other one
      is, we just add or subtract the time-equivalent of the
      timeframe multiplied by `timeframe_multiplier` to compute
      for `end` or `start`.
    * Lastly, if both are provided by the user, we use those without
      any other processing.

    Arguments:
        start: Starting datetime of the data to be fetched.
            The input argument can be a string indicating a
            valid datetime-like string or a number indicating the
            timestamp in milliseconds.
        end: Ending timestamp of the data to be fetched.
            The input argument can be a string indicating a
            valid datetime-like string or a number indicating the
            timestamp in milliseconds.
        timeframe: Timeframe of the data to fetch. Some
            examples of valid timeframe strings are `"2h"` for two
            hour, `"1d"` for one day, and `"1w"` for 1 week.
        timeframe_multiplier: Amount of difference to subtract between
            the `start` and `end` if one of them or both of them
            are not given or is set to `None`. Default value is 1.
        include_latest: If the `include_latest` variable is set to
            `True`, the latest OHLCV data is not returned since it
            is not finished yet. If set to `False`, then the
            unfinished data at the time `fetch_ohlcv()` was called
            will be returned.
        available_start: If provided, this would serve as a limiter
            for both `start` and `end.
        now: If the latest timestamp or "now" is already created
            outside the function, then it can be provided as an
            internal reference "now".

    Returns:
        A tuple containing the validated start and ending datetimes.
        If the provided `start` and `end` are both older than
        `available_start` then `(available_start, available_start)`
        is returned. User can use this information to detect invalid
        starting and ending times.
    """

    if now is None:
        now = get_datetime_now()

    end = get_datetime(end)
    start = get_datetime(start)
    available_start = get_datetime(available_start)

    # Create a time adjustment variable to dynamically determine
    # the start or end times if ever one of them or both of them
    # are missing or invalid values.
    timeframe = Timeframe(timeframe)
    time_adjustment = timeframe.to_timedelta() * timeframe_multiplier

    # If both `start` and `end` are not provided then we can assign
    # these values ourself using the current datetime
    if not start and not end:
        return _get_current_start_end(
            timeframe,
            time_adjustment,
            include_latest,
            available_start,
            now=now,
        )

    # Ensure proper order between `start` and `end`
    # if they are provided by the function user
    if start and end and start > end:
        start, end = (end, start)

    # Raise error if `start` is in the future
    if start and start > now:
        raise ValueError("Starting time cannot be in the future")

    if start and not end:
        end = start + time_adjustment

    # Make sure `end` is not in the future
    if end > now:
        end = now

    if not start and end:
        start = end - time_adjustment

        # Subtract one timeframe's worth of time to `start`
        # if the user doesn't want to include latest datetime
        # because we based `start` from the `end`
        if not include_latest and end >= now:
            start -= timeframe.to_timedelta()

    # Subtract one timeframe's worth of time to `end`
    # if the user doesn't want to include latest datetime
    if not include_latest and end >= now:
        end -= timeframe.to_timedelta()

    # Make sure `start` and `end` are not over the available start
    if available_start and available_start > start:
        start = available_start
    if available_start and available_start > end:
        end = available_start

    return start, end


def _get_current_start_end(
    timeframe: Timeframe,
    time_adjustment: dtlib.timedelta,
    include_latest: bool,
    available_start: dtlib.datetime | None,
    *,
    now: dtlib.datetime | None = None,
) -> tuple[dtlib.datetime, dtlib.datetime]:
    """Special case for `start` and `end` validation."""
    if not now:
        now = get_datetime_now()

    end = now
    start = end - time_adjustment

    if not include_latest:
        end -= timeframe.to_timedelta()
        start -= timeframe.to_timedelta()

    if available_start and available_start > start:
        start = available_start

    return start, end


def get_iso8601(value: dtlib.datetime | str | int | None) -> str | None:
    if not value:
        return None

    value_ms = get_milliseconds(value)
    value = get_datetime(value)

    value_iso8601 = value.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-6] + "{:03d}"
    value_iso8601 = value_iso8601.format(int(value_ms) % 1000) + "Z"

    return value_iso8601


def get_milliseconds(value: str | int | None) -> int | None:
    if not value:
        return None

    if isinstance(value, int) and len(str(value)) >= 12:
        return value

    return int(get_seconds(value) * 1000)


def get_seconds(value: str | int | None) -> float | int | None:
    if not value:
        return None

    if isinstance(value, int) and len(str(value)) >= 12:
        return value / 1000

    return get_datetime(value).timestamp()


def get_datetime(value: str | int | None) -> dtlib.datetime | None:
    """Returns the UTC datetime equivalent of the input value.

    Arguments:
        value: The generic input. This can be a string or an integer.
            If its a datetime string, its just parsed automatically.
            If its a number like string or an actual integer,
            we check if its a Unix timestamp and is convert accordingly.

    Return:
        A datetime object.

    """
    if not value:
        return None

    value = str(value)
    if value.isdigit() and len(value) >= 12:
        datetime = dtlib.datetime.utcfromtimestamp(int(value) / 1000.0)
    else:
        first_day_current_yr = dtlib.datetime(get_datetime_now().year, 1, 1)
        datetime = dtparser.parse(value, default=first_day_current_yr)

    return datetime.replace(tzinfo=dtlib.timezone.utc)


def get_datetime_now() -> dtlib.datetime:
    return dtlib.datetime.now(dtlib.timezone.utc)
