"""Tests for ohlcv.timeunit"""

import pytest

from ohlcv import TimeUnit


class TestTimeUnit:
    def test__timeunit__invalid_type(self):
        with pytest.raises(TypeError) as excinfo:
            TimeUnit([1, 2])

        assert "argument must be " in str(excinfo.value).lower()
        assert ", not " in str(excinfo.value).lower()

    def test__timeunit__unit_is_none(self):
        timeunit = TimeUnit()
        assert timeunit._unit is None

    def test__timeunit__invalid_unit(self):
        with pytest.raises(ValueError) as excinfo:
            TimeUnit("ga")

    def test__timeunit__mass_initialization(self):
        timeunit = TimeUnit("h")
        assert isinstance(timeunit, TimeUnit)

        assert not TimeUnit()
        assert not TimeUnit(None)
        assert not TimeUnit([])
        assert not TimeUnit('')

        inner_timeunit = TimeUnit("h")
        outer_timeunit = TimeUnit(inner_timeunit)

        assert isinstance(inner_timeunit, TimeUnit)
        assert isinstance(outer_timeunit, TimeUnit)

        assert inner_timeunit == "h"
        assert outer_timeunit == "h"

        with pytest.raises(ValueError):
            TimeUnit("some unknown unit")

        with pytest.raises(TypeError):
            TimeUnit(8012)

    def test__timeunit__hash_dunder(self):
        timeunit_set = {
            TimeUnit("h"),
            TimeUnit("m"),
            TimeUnit("h"),
        }

        assert len(timeunit_set) == 2

    def test__timeunit__repr_dunder(self):
        assert repr(TimeUnit("y")) == repr("y")
        assert repr(TimeUnit("M")) == repr("M")
        assert repr(TimeUnit("w")) == repr("w")
        assert repr(TimeUnit("d")) == repr("d")
        assert repr(TimeUnit("h")) == repr("h")
        assert repr(TimeUnit("m")) == repr("m")
        assert repr(TimeUnit("s")) == repr("s")
        assert repr(TimeUnit("ms")) == repr("ms")

    def test__timeunit__str_dunder(self):
        assert str(TimeUnit("y")) == "y"
        assert str(TimeUnit("M")) == "M"
        assert str(TimeUnit("w")) == "w"
        assert str(TimeUnit("d")) == "d"
        assert str(TimeUnit("h")) == "h"
        assert str(TimeUnit("m")) == "m"
        assert str(TimeUnit("s")) == "s"
        assert str(TimeUnit("ms")) == "ms"

    def test__timeunit__equality(self):
        timeunit_1 = TimeUnit("h")
        timeunit_2 = TimeUnit(unit="h")
        timeunit_3 = TimeUnit(timeunit_1)

        assert timeunit_1 == timeunit_2 == timeunit_3

        # Not ideal, we really want to use `is None`
        # this is to just cover the last case in __eq__()
        assert TimeUnit(None) == None

    def test__timeunit__constants(self):
        # Make sure that all the conversion mappings have unique values
        assert len(set(TimeUnit.UNIT_TO_SECONDS_MAPPING.values())) == len(
            TimeUnit.UNIT_TO_SECONDS_MAPPING.values()
        )

        assert len(set(TimeUnit.WORD_UNITS_MAPPING.values())) == len(
            TimeUnit.WORD_UNITS_MAPPING.values()
        )

        assert len(set(TimeUnit.ADJECTIVE_UNITS_MAPPING.values())) == len(
            TimeUnit.ADJECTIVE_UNITS_MAPPING.values()
        )

        assert len(set(TimeUnit.PANDAS_OFFSET_UNITS_MAPPING.values())) == len(
            TimeUnit.PANDAS_OFFSET_UNITS_MAPPING.values()
        )

    def test__timeunit__to_pandas(self):
        assert TimeUnit("y").to_pandas() == "Y"
        assert TimeUnit("M").to_pandas() == "M"
        assert TimeUnit("w").to_pandas() == "W"
        assert TimeUnit("d").to_pandas() == "D"
        assert TimeUnit("h").to_pandas() == "H"
        assert TimeUnit("m").to_pandas() == "T"
        assert TimeUnit("s").to_pandas() == "S"
        assert TimeUnit("ms").to_pandas() == "L"

    def test__timeunit__to_seconds(self):
        assert TimeUnit("y").to_seconds() == 31_536_000
        assert TimeUnit("M").to_seconds() == 2_592_000
        assert TimeUnit("w").to_seconds() == 604_800
        assert TimeUnit("d").to_seconds() == 86_400
        assert TimeUnit("h").to_seconds() == 3_600
        assert TimeUnit("m").to_seconds() == 60
        assert TimeUnit("s").to_seconds() == 1
        assert TimeUnit("ms").to_seconds() == 1 / 1_000

    def test__timeunit__to_word(self):
        assert TimeUnit("y").to_word() == "year"
        assert TimeUnit("M").to_word() == "month"
        assert TimeUnit("w").to_word() == "week"
        assert TimeUnit("d").to_word() == "day"
        assert TimeUnit("h").to_word() == "hour"
        assert TimeUnit("m").to_word() == "minute"
        assert TimeUnit("s").to_word() == "second"
        assert TimeUnit("ms").to_word() == "millisecond"

    def test__timeunit__to_adjective(self):
        assert TimeUnit("y").to_adjective() == "yearly"
        assert TimeUnit("M").to_adjective() == "monthly"
        assert TimeUnit("w").to_adjective() == "weekly"
        assert TimeUnit("d").to_adjective() == "daily"
        assert TimeUnit("h").to_adjective() == "hourly"
        assert TimeUnit("m").to_adjective() == "minute"
        assert TimeUnit("s").to_adjective() == "second"
        assert TimeUnit("ms").to_adjective() == "millisecond"

    def test__timeunit__to_pandas(self):
        assert TimeUnit("y").to_pandas() == "Y"
        assert TimeUnit("M").to_pandas() == "M"
        assert TimeUnit("w").to_pandas() == "W"
        assert TimeUnit("d").to_pandas() == "D"
        assert TimeUnit("h").to_pandas() == "H"
        assert TimeUnit("m").to_pandas() == "T"
        assert TimeUnit("s").to_pandas() == "S"
        assert TimeUnit("ms").to_pandas() == "L"