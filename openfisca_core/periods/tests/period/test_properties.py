import pytest

from openfisca_core.periods import DateUnit, Instant, Period


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.YEAR, Instant((2022, 12, 1)), 1, 1],
    [DateUnit.YEAR, Instant((2022, 1, 1)), 2, 2],
    ])
def test_size_in_years(date_unit, instant, size, expected):
    period = Period((date_unit, instant, size))
    assert period.size_in_years == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.YEAR, Instant((2020, 1, 1)), 1, 12],
    [DateUnit.YEAR, Instant((2022, 1, 1)), 2, 24],
    [DateUnit.MONTH, Instant((2012, 1, 3)), 3, 3],
    ])
def test_size_in_months(date_unit, instant, size, expected):
    period = Period((date_unit, instant, size))
    assert period.size_in_months == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.YEAR, Instant((2022, 12, 1)), 1, 365],
    [DateUnit.YEAR, Instant((2020, 1, 1)), 1, 366],
    [DateUnit.YEAR, Instant((2022, 1, 1)), 2, 730],
    [DateUnit.MONTH, Instant((2022, 12, 1)), 1, 31],
    [DateUnit.MONTH, Instant((2020, 2, 3)), 1, 29],
    [DateUnit.MONTH, Instant((2022, 1, 3)), 3, 31 + 28 + 31],
    [DateUnit.MONTH, Instant((2012, 1, 3)), 3, 31 + 29 + 31],
    [DateUnit.DAY, Instant((2022, 12, 31)), 1, 1],
    [DateUnit.DAY, Instant((2022, 12, 31)), 3, 3],
    [DateUnit.WEEK, Instant((2022, 12, 31)), 1, 7],
    [DateUnit.WEEK, Instant((2022, 12, 31)), 3, 21],
    [DateUnit.WEEKDAY, Instant((2022, 12, 31)), 1, 1],
    [DateUnit.WEEKDAY, Instant((2022, 12, 31)), 3, 3],
    ])
def test_size_in_days(date_unit, instant, size, expected):
    period = Period((date_unit, instant, size))
    assert period.size_in_days == expected
    assert period.size_in_days == period.days


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.YEAR, Instant((2022, 12, 1)), 1, 52],
    [DateUnit.YEAR, Instant((2020, 1, 1)), 5, 261],
    [DateUnit.WEEK, Instant((2022, 12, 31)), 1, 1],
    [DateUnit.WEEK, Instant((2022, 12, 31)), 3, 3],
    ])
def test_size_in_weeks(date_unit, instant, size, expected):
    period = Period((date_unit, instant, size))
    assert period.size_in_weeks == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.YEAR, Instant((2022, 12, 1)), 1, 364],
    [DateUnit.YEAR, Instant((2020, 1, 1)), 1, 364],
    [DateUnit.YEAR, Instant((2022, 1, 1)), 2, 728],
    [DateUnit.DAY, Instant((2022, 12, 31)), 1, 1],
    [DateUnit.DAY, Instant((2022, 12, 31)), 3, 3],
    [DateUnit.WEEK, Instant((2022, 12, 31)), 1, 7],
    [DateUnit.WEEK, Instant((2022, 12, 31)), 3, 21],
    [DateUnit.WEEKDAY, Instant((2022, 12, 31)), 1, 1],
    [DateUnit.WEEKDAY, Instant((2022, 12, 31)), 3, 3],
    ])
def test_size_in_weekdays(date_unit, instant, size, expected):
    period = Period((date_unit, instant, size))
    assert period.size_in_weekdays == expected
