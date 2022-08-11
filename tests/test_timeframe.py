"""Tests for ohlcv.timeframe"""

import pytest

from dateutil.relativedelta import relativedelta

from ohlcv import Timeframe


class TestTimeframe:
    def test__timeframe__invalid_type(self):
        with pytest.raises(TypeError) as excinfo:
            Timeframe(interval=[1, 2], unit="h")

        assert "argument must be " in str(excinfo.value).lower()
        assert ", not " in str(excinfo.value).lower()

        with pytest.raises(TypeError) as excinfo:
            Timeframe(interval=1, unit=[1, 2])

        assert "argument must be " in str(excinfo.value).lower()
        assert ", not " in str(excinfo.value).lower()

    def test__timeframe__equality(self):
        """Test case found in the `Timeframe` docstring."""
        timeframe_1 = Timeframe("1h")
        timeframe_2 = Timeframe(interval=1, unit="h")
        timeframe_3 = Timeframe(timeframe_1)

        assert timeframe_1 == timeframe_2 == timeframe_3
        assert Timeframe("1d") == Timeframe("24h")

        assert timeframe_1 == timeframe_1  # pylint: disable=comparison-with-itself
        assert Timeframe("1h") == "1h"

        assert Timeframe("1d") == Timeframe("24h")
        assert Timeframe() == Timeframe()

    def test__timeframe__interval_is_none(self):
        timeframe = Timeframe()

        # assert timeframe.unit == TimeUnit(None)
        assert timeframe.interval is None
        assert timeframe.unit is None

    def test__timeframe__with_interval_no_unit_invalid_interval(self):
        with pytest.raises(ValueError) as excinfo:
            Timeframe("42dd4ga")

        assert "invalid timeframe interval" in str(excinfo.value).lower()

    def test__timeframe__with_interval_no_unit_invalid_unit(self):
        with pytest.raises(ValueError) as excinfo:
            Timeframe("4ga")

        assert "invalid timeframe unit" in str(excinfo.value).lower()

    def test__timeframe__with_interval_no_unit_interval_is_int(self):
        with pytest.raises(ValueError) as excinfo:
            Timeframe(interval=1, unit=None)

        assert "unit argument is required if interval is a number" in (
            str(excinfo.value).lower()
        )

    def test__timeframe__with_interval_no_unit_interval_is_string(self):
        with pytest.raises(ValueError):
            Timeframe(interval="1", unit=None)

    def test__timeframe__with_interval_and_unit_use_unit(self):
        timeframe = Timeframe(interval="1", unit="h")

        assert timeframe.interval == 1
        assert timeframe.unit == "h"

    def test__timeframe__mass_initialization(self):
        timeframe = Timeframe(interval=3, unit="d")
        assert isinstance(timeframe, Timeframe)
        assert timeframe.interval == 3
        assert timeframe.unit == "d"

        timeframe = Timeframe(interval="8", unit="h")
        assert timeframe.interval == 8
        assert timeframe.unit == "h"

        timeframe = Timeframe(timeframe)
        assert timeframe.interval == 8
        assert timeframe.unit == "h"

        timeframe = Timeframe()
        assert timeframe.interval is None
        assert timeframe.unit is None

        timeframe = Timeframe(interval=8.0, unit="h")
        assert timeframe.interval == 8
        assert timeframe.unit == "h"

        timeframe = Timeframe("250ms")
        assert timeframe.interval == 250
        assert timeframe.unit == "ms"

        with pytest.raises(TypeError):
            Timeframe(interval=["invalid", "interval"], unit="h")

        with pytest.raises(TypeError):
            Timeframe(interval={1: 2, 3: 4}, unit="h")

        with pytest.raises(TypeError):
            Timeframe(interval={1: 2, 3: 4}, unit="h")

        with pytest.raises(ValueError):
            Timeframe(interval="5.7.8", unit="h")

    def test__timeframe__hash_dunder(self):
        timeframe_set = {
            Timeframe("3h"),
            Timeframe("3h"),
            Timeframe("5h"),
        }

        assert len(timeframe_set) == 2

    def test__timeframe__repr_dunder(self):
        timeframe = Timeframe("3h")
        assert repr(timeframe) == (
            f"{timeframe.__class__.__name__}("
            f"interval={timeframe.interval!r}, "
            f"unit={timeframe.unit!r}"
            ")"
        )

    def test__timeframe__str_dunder(self):
        timeframe = Timeframe("3d")
        assert str(timeframe) == "3d"

        timeframe = Timeframe("5.7h")
        assert str(timeframe) == "5h"

        timeframe = Timeframe()
        assert str(timeframe) == "0"

    def test__timeframe__get_duration(self):
        timeframe = Timeframe("3d")

        assert pytest.approx(timeframe.get_duration("y")) == 0.008219178082
        assert pytest.approx(timeframe.get_duration("w")) == 0.428571428571
        assert pytest.approx(timeframe.get_duration("M")) == 0.1
        assert timeframe.get_duration("d") == 3
        assert timeframe.get_duration("h") == 72
        assert timeframe.get_duration("m") == 4320
        assert timeframe.get_duration("s") == 259200
        assert timeframe.get_duration("ms") == 259200000

        assert Timeframe().get_duration() == 0

        with pytest.raises(ValueError):
            timeframe.get_duration("some unknown unit")

    def test__timeframe__to_timedelta(self):
        timeframe = Timeframe("3d")

        assert timeframe.to_timedelta() == relativedelta(days=3)

        assert pytest.approx(
            Timeframe("1M").to_timedelta().days
        ) == relativedelta(days=365 / 12).days

        assert Timeframe("1d").to_timedelta() == relativedelta(hours=24)
        assert Timeframe("1y").to_timedelta() == relativedelta(days=365)
        assert Timeframe("3d").to_timedelta() == relativedelta(days=3)
        assert Timeframe("4h").to_timedelta() == relativedelta(hours=4)
        assert Timeframe("69ms").to_timedelta().microseconds == relativedelta(
            microseconds=69000
        ).microseconds

    def test__timeframe__manual_property_setting(self):
        timeframe = Timeframe()
        timeframe.interval = 5
        timeframe.unit = "m"

        assert timeframe.interval == 5
        assert timeframe.unit == "m"

        timeframe.interval = None

        assert timeframe.interval is None
        assert timeframe.unit is None

        timeframe.interval = ["invalid", "interval"]

        assert timeframe.interval is None
        assert timeframe.unit is None
