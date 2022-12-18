import datetime

import pytest

from openfisca_core.periods import DateUnit, Period, Instant

day, month, year, eternity = DateUnit


@pytest.fixture
def instant():
    """Returns a ``Instant``."""

    return Instant((2022, 12, 31))


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [month, Instant((2022, 1, 1)), 12, "2022"],
    [month, Instant((2022, 3, 1)), 12, "year:2022-03"],
    [year, Instant((2022, 1, 1)), 1, "2022"],
    [year, Instant((2022, 1, 1)), 3, "year:2022:3"],
    [year, Instant((2022, 1, 3)), 3, "year:2022:3"],
    [year, Instant((2022, 3, 1)), 1, "year:2022-03"],
    ])
def test_str_with_years(date_unit, instant, size, expected):
    """Returns the expected string."""

    assert str(Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [month, Instant((2022, 1, 1)), 1, "2022-01"],
    [month, Instant((2022, 1, 1)), 3, "month:2022-01:3"],
    [month, Instant((2022, 3, 1)), 3, "month:2022-03:3"],
    ])
def test_str_with_months(date_unit, instant, size, expected):
    """Returns the expected string."""

    assert str(Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [day, Instant((2022, 1, 1)), 1, "2022-01-01"],
    [day, Instant((2022, 1, 1)), 3, "day:2022-01-01:3"],
    [day, Instant((2022, 3, 1)), 3, "day:2022-03-01:3"],
    ])
def test_str_with_days(date_unit, instant, size, expected):
    """Returns the expected string."""

    assert str(Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("period_unit, unit, start, cease, count", [
    [day, day, Instant((2022, 12, 31)), Instant((2023, 1, 2)), 3],
    [month, day, Instant((2022, 12, 31)), Instant((2023, 3, 30)), 90],
    [month, month, Instant((2022, 12, 1)), Instant((2023, 2, 1)), 3],
    [year, day, Instant((2022, 12, 31)), Instant((2025, 12, 30)), 1096],
    [year, month, Instant((2022, 12, 1)), Instant((2025, 11, 1)), 36],
    [year, year, Instant((2022, 1, 1)), Instant((2024, 1, 1)), 3],
    ])
def test_subperiods(instant, period_unit, unit, start, cease, count):
    """Returns the expected subperiods."""

    period = Period((period_unit, instant, 3))
    subperiods = period.subperiods(unit)

    assert len(subperiods) == count
    assert subperiods[0] == Period((unit, start, 1))
    assert subperiods[-1] == Period((unit, cease, 1))


@pytest.mark.parametrize("period_unit, offset, unit, expected", [
    [day, "first-of", month, Period((day, Instant((2022, 12, 1)), 3))],
    [day, "first-of", year, Period((day, Instant((2022, 1, 1)), 3))],
    [day, "last-of", month, Period((day, Instant((2022, 12, 31)), 3))],
    [day, "last-of", year, Period((day, Instant((2022, 12, 31)), 3))],
    [day, -3, year, Period((day, Instant((2019, 12, 31)), 3))],
    [day, 1, month, Period((day, Instant((2023, 1, 31)), 3))],
    [day, 3, day, Period((day, Instant((2023, 1, 3)), 3))],
    [month, "first-of", month, Period((month, Instant((2022, 12, 1)), 3))],
    [month, "first-of", year, Period((month, Instant((2022, 1, 1)), 3))],
    [month, "last-of", month, Period((month, Instant((2022, 12, 31)), 3))],
    [month, "last-of", year, Period((month, Instant((2022, 12, 31)), 3))],
    [month, -3, year, Period((month, Instant((2019, 12, 31)), 3))],
    [month, 1, month, Period((month, Instant((2023, 1, 31)), 3))],
    [month, 3, day, Period((month, Instant((2023, 1, 3)), 3))],
    [year, "first-of", month, Period((year, Instant((2022, 12, 1)), 3))],
    [year, "first-of", year, Period((year, Instant((2022, 1, 1)), 3))],
    [year, "last-of", month, Period((year, Instant((2022, 12, 31)), 3))],
    [year, "last-of", year, Period((year, Instant((2022, 12, 31)), 3))],
    [year, -3, year, Period((year, Instant((2019, 12, 31)), 3))],
    [year, 1, month, Period((year, Instant((2023, 1, 31)), 3))],
    [year, 3, day, Period((year, Instant((2023, 1, 3)), 3))],
    ])
def test_offset(instant, period_unit, offset, unit, expected):
    """Returns the expected ``Period``."""

    period = Period((period_unit, instant, 3))

    assert period.offset(offset, unit) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [month, Instant((2012, 1, 3)), 3, 3],
    [month, Instant((2012, 2, 3)), 1, 1],
    [month, Instant((2022, 1, 3)), 3, 3],
    [month, Instant((2022, 12, 1)), 1, 1],
    [year, Instant((2012, 1, 1)), 1, 12],
    [year, Instant((2022, 1, 1)), 2, 24],
    [year, Instant((2022, 12, 1)), 1, 12],
    ])
def test_day_size_in_months(date_unit, instant, size, expected):
    """Returns the expected number of months."""

    period = Period((date_unit, instant, size))

    assert period.count(month) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [day, Instant((2022, 12, 31)), 1, 1],
    [day, Instant((2022, 12, 31)), 3, 3],
    [month, Instant((2012, 1, 3)), 3, 31 + 29 + 31],
    [month, Instant((2012, 2, 3)), 1, 29],
    [month, Instant((2022, 1, 3)), 3, 31 + 28 + 31],
    [month, Instant((2022, 12, 1)), 1, 31],
    [year, Instant((2012, 1, 1)), 1, 366],
    [year, Instant((2022, 1, 1)), 2, 730],
    [year, Instant((2022, 12, 1)), 1, 365],
    ])
def test_day_size_in_days(date_unit, instant, size, expected):
    """Returns the expected number of days."""

    period = Period((date_unit, instant, size))

    assert period.count(day) == expected


@pytest.mark.parametrize("arg, expected", [
    ["1000", Period((year, Instant((1000, 1, 1)), 1))],
    ["1000-01", Period((month, Instant((1000, 1, 1)), 1))],
    ["1000-01-01", Period((day, Instant((1000, 1, 1)), 1))],
    ["1004-02-29", Period((day, Instant((1004, 2, 29)), 1))],
    ["ETERNITY", Period((eternity, Instant((1, 1, 1)), 1))],
    ["day:1000-01-01", Period((day, Instant((1000, 1, 1)), 1))],
    ["day:1000-01-01:3", Period((day, Instant((1000, 1, 1)), 3))],
    ["eternity", Period((eternity, Instant((1, 1, 1)), 1))],
    ["month:1000-01", Period((month, Instant((1000, 1, 1)), 1))],
    ["month:1000-01-01", Period((month, Instant((1000, 1, 1)), 1))],
    ["month:1000-01-01:3", Period((month, Instant((1000, 1, 1)), 3))],
    ["month:1000-01:3", Period((month, Instant((1000, 1, 1)), 3))],
    ["year:1000", Period((year, Instant((1000, 1, 1)), 1))],
    ["year:1000-01", Period((year, Instant((1000, 1, 1)), 1))],
    ["year:1000-01-01", Period((year, Instant((1000, 1, 1)), 1))],
    ["year:1000-01-01:3", Period((year, Instant((1000, 1, 1)), 3))],
    ["year:1000-01:3", Period((year, Instant((1000, 1, 1)), 3))],
    ["year:1000:3", Period((year, Instant((1000, 1, 1)), 3))],
    [1000, Period((year, Instant((1000, 1, 1)), 1))],
    [eternity, Period((eternity, Instant((1, 1, 1)), 1))],
    [Instant((1, 1, 1)), Period((day, Instant((1, 1, 1)), 1))],
    [Period((day, Instant((1, 1, 1)), 365)), Period((day, Instant((1, 1, 1)), 365))],
    ])
def test_build(arg, expected):
    """Returns the expected ``Period``."""

    assert Period.build(arg) == expected


@pytest.mark.parametrize("arg, error", [
    ["1000-0", ValueError],
    ["1000-0-0", ValueError],
    ["1000-01-01:1", ValueError],
    ["1000-01:1", ValueError],
    ["1000-1", ValueError],
    ["1000-1-0", ValueError],
    ["1000-1-1", ValueError],
    ["1000-13", ValueError],
    ["1000-2-31", ValueError],
    ["1000:1", ValueError],
    ["day:1000-01", ValueError],
    ["day:1000-01:1", ValueError],
    ["day:1000:1", ValueError],
    ["month:1000", ValueError],
    ["month:1000:1", ValueError],
    [None, TypeError],
    [datetime.date(1, 1, 1), ValueError],
    [year, TypeError],
    ])
def test_build_with_an_invalid_argument(arg, error):
    """Raises ``ValueError`` when given an invalid argument."""

    with pytest.raises(error):
        Period.build(arg)
