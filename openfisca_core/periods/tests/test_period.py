import pytest

from openfisca_core import periods
from openfisca_core.periods import Instant, Period


@pytest.fixture
def instant():
    return Instant((2022, 12, 31))


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.YEAR, Instant((2022, 1, 1)), 1, "2022"],
    [periods.MONTH, Instant((2022, 1, 1)), 12, "2022"],
    [periods.YEAR, Instant((2022, 3, 1)), 1, "year:2022-03"],
    [periods.MONTH, Instant((2022, 3, 1)), 12, "year:2022-03"],
    [periods.YEAR, Instant((2022, 1, 1)), 3, "year:2022:3"],
    [periods.YEAR, Instant((2022, 1, 3)), 3, "year:2022:3"],
    ])
def test_str_with_years(date_unit, instant, size, expected):
    assert str(Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.MONTH, Instant((2022, 1, 1)), 1, "2022-01"],
    [periods.MONTH, Instant((2022, 1, 1)), 3, "month:2022-01:3"],
    [periods.MONTH, Instant((2022, 3, 1)), 3, "month:2022-03:3"],
    ])
def test_str_with_months(date_unit, instant, size, expected):
    assert str(Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.DAY, Instant((2022, 1, 1)), 1, "2022-01-01"],
    [periods.DAY, Instant((2022, 1, 1)), 3, "day:2022-01-01:3"],
    [periods.DAY, Instant((2022, 3, 1)), 3, "day:2022-03-01:3"],
    ])
def test_str_with_days(date_unit, instant, size, expected):
    assert str(Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("period_unit, unit, start, cease, count", [
    [periods.YEAR, periods.YEAR, Instant((2022, 1, 1)), Instant((2024, 1, 1)), 3],
    [periods.YEAR, periods.MONTH, Instant((2022, 12, 1)), Instant((2025, 11, 1)), 36],
    [periods.YEAR, periods.DAY, Instant((2022, 12, 31)), Instant((2025, 12, 30)), 1096],
    [periods.MONTH, periods.MONTH, Instant((2022, 12, 1)), Instant((2023, 2, 1)), 3],
    [periods.MONTH, periods.DAY, Instant((2022, 12, 31)), Instant((2023, 3, 30)), 90],
    [periods.DAY, periods.DAY, Instant((2022, 12, 31)), Instant((2023, 1, 2)), 3],
    ])
def test_subperiods(instant, period_unit, unit, start, cease, count):
    period = Period((period_unit, instant, 3))
    subperiods = period.get_subperiods(unit)
    assert len(subperiods) == count
    assert subperiods[0] == Period((unit, start, 1))
    assert subperiods[-1] == Period((unit, cease, 1))


@pytest.mark.parametrize("period_unit, offset, unit, expected", [
    [periods.YEAR, "first-of", periods.YEAR, Period(('year', Instant((2022, 1, 1)), 3))],
    [periods.YEAR, "first-of", periods.MONTH, Period(('year', Instant((2022, 12, 1)), 3))],
    [periods.YEAR, "last-of", periods.YEAR, Period(('year', Instant((2022, 12, 31)), 3))],
    [periods.YEAR, "last-of", periods.MONTH, Period(('year', Instant((2022, 12, 31)), 3))],
    [periods.YEAR, -3, periods.YEAR, Period(('year', Instant((2019, 12, 31)), 3))],
    [periods.YEAR, 1, periods.MONTH, Period(('year', Instant((2023, 1, 31)), 3))],
    [periods.YEAR, 3, periods.DAY, Period(('year', Instant((2023, 1, 3)), 3))],
    [periods.MONTH, "first-of", periods.YEAR, Period(('month', Instant((2022, 1, 1)), 3))],
    [periods.MONTH, "first-of", periods.MONTH, Period(('month', Instant((2022, 12, 1)), 3))],
    [periods.MONTH, "last-of", periods.YEAR, Period(('month', Instant((2022, 12, 31)), 3))],
    [periods.MONTH, "last-of", periods.MONTH, Period(('month', Instant((2022, 12, 31)), 3))],
    [periods.MONTH, -3, periods.YEAR, Period(('month', Instant((2019, 12, 31)), 3))],
    [periods.MONTH, 1, periods.MONTH, Period(('month', Instant((2023, 1, 31)), 3))],
    [periods.MONTH, 3, periods.DAY, Period(('month', Instant((2023, 1, 3)), 3))],
    [periods.DAY, "first-of", periods.YEAR, Period(('day', Instant((2022, 1, 1)), 3))],
    [periods.DAY, "first-of", periods.MONTH, Period(('day', Instant((2022, 12, 1)), 3))],
    [periods.DAY, "last-of", periods.YEAR, Period(('day', Instant((2022, 12, 31)), 3))],
    [periods.DAY, "last-of", periods.MONTH, Period(('day', Instant((2022, 12, 31)), 3))],
    [periods.DAY, -3, periods.YEAR, Period(('day', Instant((2019, 12, 31)), 3))],
    [periods.DAY, 1, periods.MONTH, Period(('day', Instant((2023, 1, 31)), 3))],
    [periods.DAY, 3, periods.DAY, Period(('day', Instant((2023, 1, 3)), 3))],
    ])
def test_offset(instant, period_unit, offset, unit, expected):
    period = Period((period_unit, instant, 3))
    assert period.offset(offset, unit) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.MONTH, Instant((2022, 12, 1)), 1, 1],
    [periods.MONTH, Instant((2012, 2, 3)), 1, 1],
    [periods.MONTH, Instant((2022, 1, 3)), 3, 3],
    [periods.MONTH, Instant((2012, 1, 3)), 3, 3],
    [periods.YEAR, Instant((2022, 12, 1)), 1, 12],
    [periods.YEAR, Instant((2012, 1, 1)), 1, 12],
    [periods.YEAR, Instant((2022, 1, 1)), 2, 24],
    ])
def test_day_size_in_months(date_unit, instant, size, expected):
    period = Period((date_unit, instant, size))
    assert period.size_in_months == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.DAY, Instant((2022, 12, 31)), 1, 1],
    [periods.DAY, Instant((2022, 12, 31)), 3, 3],
    [periods.MONTH, Instant((2022, 12, 1)), 1, 31],
    [periods.MONTH, Instant((2012, 2, 3)), 1, 29],
    [periods.MONTH, Instant((2022, 1, 3)), 3, 31 + 28 + 31],
    [periods.MONTH, Instant((2012, 1, 3)), 3, 31 + 29 + 31],
    [periods.YEAR, Instant((2022, 12, 1)), 1, 365],
    [periods.YEAR, Instant((2012, 1, 1)), 1, 366],
    [periods.YEAR, Instant((2022, 1, 1)), 2, 730],
    ])
def test_day_size_in_days(date_unit, instant, size, expected):
    period = Period((date_unit, instant, size))
    assert period.size_in_days == expected
