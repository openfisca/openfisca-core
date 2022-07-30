import pytest

from openfisca_core import periods
from openfisca_core.periods import Instant, Period


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


@pytest.mark.parametrize("period, unit, length, first, last", [
    (periods.period('year:2014:2'), periods.YEAR, 2, periods.period('2014'), periods.period('2015')),
    (periods.period(2017), periods.MONTH, 12, periods.period('2017-01'), periods.period('2017-12')),
    (periods.period('year:2014:2'), periods.MONTH, 24, periods.period('2014-01'), periods.period('2015-12')),
    (periods.period('month:2014-03:3'), periods.MONTH, 3, periods.period('2014-03'), periods.period('2014-05')),
    (periods.period(2017), periods.DAY, 365, periods.period('2017-01-01'), periods.period('2017-12-31')),
    (periods.period('year:2014:2'), periods.DAY, 730, periods.period('2014-01-01'), periods.period('2015-12-31')),
    (periods.period('month:2014-03:3'), periods.DAY, 92, periods.period('2014-03-01'), periods.period('2014-05-31')),
    ])
def test_subperiods(period, unit, length, first, last):
    subperiods = period.get_subperiods(unit)
    assert len(subperiods) == length
    assert subperiods[0] == first
    assert subperiods[-1] == last


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
