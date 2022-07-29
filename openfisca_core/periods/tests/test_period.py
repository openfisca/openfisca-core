import pytest

from openfisca_core import periods
from openfisca_core.periods import DateUnit, Instant, Period


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.YEAR, Instant((2022, 1, 1)), 1, "2022"],
    [DateUnit.MONTH, Instant((2022, 1, 1)), 12, "2022"],
    [DateUnit.YEAR, Instant((2022, 3, 1)), 1, "year:2022-03"],
    [DateUnit.MONTH, Instant((2022, 3, 1)), 12, "year:2022-03"],
    [DateUnit.YEAR, Instant((2022, 1, 1)), 3, "year:2022:3"],
    [DateUnit.YEAR, Instant((2022, 1, 3)), 3, "year:2022:3"],
    ])
def test_str_with_years(date_unit, instant, size, expected):
    assert str(Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.MONTH, Instant((2022, 1, 1)), 1, "2022-01"],
    [DateUnit.MONTH, Instant((2022, 1, 1)), 3, "month:2022-01:3"],
    [DateUnit.MONTH, Instant((2022, 3, 1)), 3, "month:2022-03:3"],
    ])
def test_str_with_months(date_unit, instant, size, expected):
    assert str(Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.DAY, Instant((2022, 1, 1)), 1, "2022-01-01"],
    [DateUnit.DAY, Instant((2022, 1, 1)), 3, "day:2022-01-01:3"],
    [DateUnit.DAY, Instant((2022, 3, 1)), 3, "day:2022-03-01:3"],
    ])
def test_str_with_days(date_unit, instant, size, expected):
    assert str(Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("period, unit, length, first, last", [
    (periods.period('year:2014:2'), DateUnit.YEAR, 2, periods.period('2014'), periods.period('2015')),
    (periods.period(2017), DateUnit.MONTH, 12, periods.period('2017-01'), periods.period('2017-12')),
    (periods.period('year:2014:2'), DateUnit.MONTH, 24, periods.period('2014-01'), periods.period('2015-12')),
    (periods.period('month:2014-03:3'), DateUnit.MONTH, 3, periods.period('2014-03'), periods.period('2014-05')),
    (periods.period(2017), DateUnit.DAY, 365, periods.period('2017-01-01'), periods.period('2017-12-31')),
    (periods.period('year:2014:2'), DateUnit.DAY, 730, periods.period('2014-01-01'), periods.period('2015-12-31')),
    (periods.period('month:2014-03:3'), DateUnit.DAY, 92, periods.period('2014-03-01'), periods.period('2014-05-31')),
    ])
def test_subperiods(period, unit, length, first, last):
    subperiods = period.get_subperiods(unit)
    assert len(subperiods) == length
    assert subperiods[0] == first
    assert subperiods[-1] == last


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.MONTH, Instant((2022, 12, 1)), 1, 1],
    [DateUnit.MONTH, Instant((2012, 2, 3)), 1, 1],
    [DateUnit.MONTH, Instant((2022, 1, 3)), 3, 3],
    [DateUnit.MONTH, Instant((2012, 1, 3)), 3, 3],
    [DateUnit.YEAR, Instant((2022, 12, 1)), 1, 12],
    [DateUnit.YEAR, Instant((2012, 1, 1)), 1, 12],
    [DateUnit.YEAR, Instant((2022, 1, 1)), 2, 24],
    ])
def test_day_size_in_months(date_unit, instant, size, expected):
    period = Period((date_unit, instant, size))
    assert period.size_in_months == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.DAY, Instant((2022, 12, 31)), 1, 1],
    [DateUnit.DAY, Instant((2022, 12, 31)), 3, 3],
    [DateUnit.MONTH, Instant((2022, 12, 1)), 1, 31],
    [DateUnit.MONTH, Instant((2012, 2, 3)), 1, 29],
    [DateUnit.MONTH, Instant((2022, 1, 3)), 3, 31 + 28 + 31],
    [DateUnit.MONTH, Instant((2012, 1, 3)), 3, 31 + 29 + 31],
    [DateUnit.YEAR, Instant((2022, 12, 1)), 1, 365],
    [DateUnit.YEAR, Instant((2012, 1, 1)), 1, 366],
    [DateUnit.YEAR, Instant((2022, 1, 1)), 2, 730],
    ])
def test_day_size_in_days(date_unit, instant, size, expected):
    period = Period((date_unit, instant, size))
    assert period.size_in_days == expected
