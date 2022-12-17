import datetime

import pytest

from openfisca_core import periods


@pytest.fixture
def instant():
    """Returns a ``Instant``."""

    return periods.instant((2022, 12, 31))


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.MONTH, periods.instant((2022, 1, 1)), 12, "2022"],
    [periods.MONTH, periods.instant((2022, 3, 1)), 12, "year:2022-03"],
    [periods.YEAR, periods.instant((2022, 1, 1)), 1, "2022"],
    [periods.YEAR, periods.instant((2022, 1, 1)), 3, "year:2022:3"],
    [periods.YEAR, periods.instant((2022, 1, 3)), 3, "year:2022:3"],
    [periods.YEAR, periods.instant((2022, 3, 1)), 1, "year:2022-03"],
    ])
def test_str_with_years(date_unit, instant, size, expected):
    """Returns the expected string."""

    assert str(periods.period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.MONTH, periods.instant((2022, 1, 1)), 1, "2022-01"],
    [periods.MONTH, periods.instant((2022, 1, 1)), 3, "month:2022-01:3"],
    [periods.MONTH, periods.instant((2022, 3, 1)), 3, "month:2022-03:3"],
    ])
def test_str_with_months(date_unit, instant, size, expected):
    """Returns the expected string."""

    assert str(periods.period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.DAY, periods.instant((2022, 1, 1)), 1, "2022-01-01"],
    [periods.DAY, periods.instant((2022, 1, 1)), 3, "day:2022-01-01:3"],
    [periods.DAY, periods.instant((2022, 3, 1)), 3, "day:2022-03-01:3"],
    ])
def test_str_with_days(date_unit, instant, size, expected):
    """Returns the expected string."""

    assert str(periods.period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("period_unit, unit, start, cease, count", [
    [periods.DAY, periods.DAY, periods.instant((2022, 12, 31)), periods.instant((2023, 1, 2)), 3],
    [periods.MONTH, periods.DAY, periods.instant((2022, 12, 31)), periods.instant((2023, 3, 30)), 90],
    [periods.MONTH, periods.MONTH, periods.instant((2022, 12, 1)), periods.instant((2023, 2, 1)), 3],
    [periods.YEAR, periods.DAY, periods.instant((2022, 12, 31)), periods.instant((2025, 12, 30)), 1096],
    [periods.YEAR, periods.MONTH, periods.instant((2022, 12, 1)), periods.instant((2025, 11, 1)), 36],
    [periods.YEAR, periods.YEAR, periods.instant((2022, 1, 1)), periods.instant((2024, 1, 1)), 3],
    ])
def test_subperiods(instant, period_unit, unit, start, cease, count):
    """Returns the expected subperiods."""

    period = periods.period((period_unit, instant, 3))
    subperiods = period.subperiods(unit)

    assert len(subperiods) == count
    assert subperiods[0] == periods.period((unit, start, 1))
    assert subperiods[-1] == periods.period((unit, cease, 1))


@pytest.mark.parametrize("period_unit, offset, unit, expected", [
    [periods.DAY, "first-of", periods.MONTH, periods.period((periods.DAY, periods.instant((2022, 12, 1)), 3))],
    [periods.DAY, "first-of", periods.YEAR, periods.period((periods.DAY, periods.instant((2022, 1, 1)), 3))],
    [periods.DAY, "last-of", periods.MONTH, periods.period((periods.DAY, periods.instant((2022, 12, 31)), 3))],
    [periods.DAY, "last-of", periods.YEAR, periods.period((periods.DAY, periods.instant((2022, 12, 31)), 3))],
    [periods.DAY, -3, periods.YEAR, periods.period((periods.DAY, periods.instant((2019, 12, 31)), 3))],
    [periods.DAY, 1, periods.MONTH, periods.period((periods.DAY, periods.instant((2023, 1, 31)), 3))],
    [periods.DAY, 3, periods.DAY, periods.period((periods.DAY, periods.instant((2023, 1, 3)), 3))],
    [periods.MONTH, "first-of", periods.MONTH, periods.period((periods.MONTH, periods.instant((2022, 12, 1)), 3))],
    [periods.MONTH, "first-of", periods.YEAR, periods.period((periods.MONTH, periods.instant((2022, 1, 1)), 3))],
    [periods.MONTH, "last-of", periods.MONTH, periods.period((periods.MONTH, periods.instant((2022, 12, 31)), 3))],
    [periods.MONTH, "last-of", periods.YEAR, periods.period((periods.MONTH, periods.instant((2022, 12, 31)), 3))],
    [periods.MONTH, -3, periods.YEAR, periods.period((periods.MONTH, periods.instant((2019, 12, 31)), 3))],
    [periods.MONTH, 1, periods.MONTH, periods.period((periods.MONTH, periods.instant((2023, 1, 31)), 3))],
    [periods.MONTH, 3, periods.DAY, periods.period((periods.MONTH, periods.instant((2023, 1, 3)), 3))],
    [periods.YEAR, "first-of", periods.MONTH, periods.period((periods.YEAR, periods.instant((2022, 12, 1)), 3))],
    [periods.YEAR, "first-of", periods.YEAR, periods.period((periods.YEAR, periods.instant((2022, 1, 1)), 3))],
    [periods.YEAR, "last-of", periods.MONTH, periods.period((periods.YEAR, periods.instant((2022, 12, 31)), 3))],
    [periods.YEAR, "last-of", periods.YEAR, periods.period((periods.YEAR, periods.instant((2022, 12, 31)), 3))],
    [periods.YEAR, -3, periods.YEAR, periods.period((periods.YEAR, periods.instant((2019, 12, 31)), 3))],
    [periods.YEAR, 1, periods.MONTH, periods.period((periods.YEAR, periods.instant((2023, 1, 31)), 3))],
    [periods.YEAR, 3, periods.DAY, periods.period((periods.YEAR, periods.instant((2023, 1, 3)), 3))],
    ])
def test_offset(instant, period_unit, offset, unit, expected):
    """Returns the expected ``Period``."""

    period = periods.period((period_unit, instant, 3))

    assert period.offset(offset, unit) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.MONTH, periods.instant((2012, 1, 3)), 3, 3],
    [periods.MONTH, periods.instant((2012, 2, 3)), 1, 1],
    [periods.MONTH, periods.instant((2022, 1, 3)), 3, 3],
    [periods.MONTH, periods.instant((2022, 12, 1)), 1, 1],
    [periods.YEAR, periods.instant((2012, 1, 1)), 1, 12],
    [periods.YEAR, periods.instant((2022, 1, 1)), 2, 24],
    [periods.YEAR, periods.instant((2022, 12, 1)), 1, 12],
    ])
def test_day_size_in_months(date_unit, instant, size, expected):
    """Returns the expected number of months."""

    period = periods.period((date_unit, instant, size))

    assert period.count(periods.MONTH) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.DAY, periods.instant((2022, 12, 31)), 1, 1],
    [periods.DAY, periods.instant((2022, 12, 31)), 3, 3],
    [periods.MONTH, periods.instant((2012, 1, 3)), 3, 31 + 29 + 31],
    [periods.MONTH, periods.instant((2012, 2, 3)), 1, 29],
    [periods.MONTH, periods.instant((2022, 1, 3)), 3, 31 + 28 + 31],
    [periods.MONTH, periods.instant((2022, 12, 1)), 1, 31],
    [periods.YEAR, periods.instant((2012, 1, 1)), 1, 366],
    [periods.YEAR, periods.instant((2022, 1, 1)), 2, 730],
    [periods.YEAR, periods.instant((2022, 12, 1)), 1, 365],
    ])
def test_day_size_in_days(date_unit, instant, size, expected):
    """Returns the expected number of days."""

    period = periods.period((date_unit, instant, size))

    assert period.count(periods.DAY) == expected


@pytest.mark.parametrize("arg, expected", [
    ["1000", periods.period((periods.YEAR, periods.instant((1000, 1, 1)), 1))],
    ["1000-01", periods.period((periods.MONTH, periods.instant((1000, 1, 1)), 1))],
    ["1000-01-01", periods.period((periods.DAY, periods.instant((1000, 1, 1)), 1))],
    ["1004-02-29", periods.period((periods.DAY, periods.instant((1004, 2, 29)), 1))],
    ["ETERNITY", periods.period((periods.ETERNITY, periods.instant((1, 1, 1)), 1))],
    ["day:1000-01-01", periods.period((periods.DAY, periods.instant((1000, 1, 1)), 1))],
    ["day:1000-01-01:3", periods.period((periods.DAY, periods.instant((1000, 1, 1)), 3))],
    ["eternity", periods.period((periods.ETERNITY, periods.instant((1, 1, 1)), 1))],
    ["month:1000-01", periods.period((periods.MONTH, periods.instant((1000, 1, 1)), 1))],
    ["month:1000-01-01", periods.period((periods.MONTH, periods.instant((1000, 1, 1)), 1))],
    ["month:1000-01-01:3", periods.period((periods.MONTH, periods.instant((1000, 1, 1)), 3))],
    ["month:1000-01:3", periods.period((periods.MONTH, periods.instant((1000, 1, 1)), 3))],
    ["year:1000", periods.period((periods.YEAR, periods.instant((1000, 1, 1)), 1))],
    ["year:1000-01", periods.period((periods.YEAR, periods.instant((1000, 1, 1)), 1))],
    ["year:1000-01-01", periods.period((periods.YEAR, periods.instant((1000, 1, 1)), 1))],
    ["year:1000-01-01:3", periods.period((periods.YEAR, periods.instant((1000, 1, 1)), 3))],
    ["year:1000-01:3", periods.period((periods.YEAR, periods.instant((1000, 1, 1)), 3))],
    ["year:1000:3", periods.period((periods.YEAR, periods.instant((1000, 1, 1)), 3))],
    [1000, periods.period((periods.YEAR, periods.instant((1000, 1, 1)), 1))],
    [periods.ETERNITY, periods.period((periods.ETERNITY, periods.instant((1, 1, 1)), 1))],
    [periods.instant((1, 1, 1)), periods.period((periods.DAY, periods.instant((1, 1, 1)), 1))],
    [periods.period((periods.DAY, periods.instant((1, 1, 1)), 365)), periods.period((periods.DAY, periods.instant((1, 1, 1)), 365))],
    ])
def test_build(arg, expected):
    """Returns the expected ``Period``."""

    assert periods.build(arg) == expected


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
    [periods.YEAR, TypeError],
    ])
def test_build_with_an_invalid_argument(arg, error):
    """Raises ``ValueError`` when given an invalid argument."""

    with pytest.raises(error):
        periods.build(arg)
