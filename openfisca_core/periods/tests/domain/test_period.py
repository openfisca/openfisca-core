import pytest

from openfisca_core import periods


@pytest.fixture
def instant():
    """Returns a ``Instant``."""
    return periods.Instant((2022, 12, 31))


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.DateUnit.YEAR, periods.Instant((2022, 1, 1)), 1, "2022"],
    [periods.DateUnit.MONTH, periods.Instant((2022, 1, 1)), 12, "2022"],
    [periods.DateUnit.YEAR, periods.Instant((2022, 3, 1)), 1, "year:2022-03"],
    [periods.DateUnit.MONTH, periods.Instant((2022, 3, 1)), 12, "year:2022-03"],
    [periods.DateUnit.YEAR, periods.Instant((2022, 1, 1)), 3, "year:2022:3"],
    [periods.DateUnit.YEAR, periods.Instant((2022, 1, 3)), 3, "year:2022:3"],
    ])
def test_str_with_years(date_unit, instant, size, expected):
    """Returns the expected string."""

    assert str(periods.Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.DateUnit.MONTH, periods.Instant((2022, 1, 1)), 1, "2022-01"],
    [periods.DateUnit.MONTH, periods.Instant((2022, 1, 1)), 3, "month:2022-01:3"],
    [periods.DateUnit.MONTH, periods.Instant((2022, 3, 1)), 3, "month:2022-03:3"],
    ])
def test_str_with_months(date_unit, instant, size, expected):
    """Returns the expected string."""

    assert str(periods.Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.DateUnit.DAY, periods.Instant((2022, 1, 1)), 1, "2022-01-01"],
    [periods.DateUnit.DAY, periods.Instant((2022, 1, 1)), 3, "day:2022-01-01:3"],
    [periods.DateUnit.DAY, periods.Instant((2022, 3, 1)), 3, "day:2022-03-01:3"],
    ])
def test_str_with_days(date_unit, instant, size, expected):
    """Returns the expected string."""

    assert str(periods.Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.DateUnit.MONTH, periods.Instant((2022, 12, 1)), 1, 1],
    [periods.DateUnit.MONTH, periods.Instant((2012, 2, 3)), 1, 1],
    [periods.DateUnit.MONTH, periods.Instant((2022, 1, 3)), 3, 3],
    [periods.DateUnit.MONTH, periods.Instant((2012, 1, 3)), 3, 3],
    [periods.DateUnit.YEAR, periods.Instant((2022, 12, 1)), 1, 12],
    [periods.DateUnit.YEAR, periods.Instant((2012, 1, 1)), 1, 12],
    [periods.DateUnit.YEAR, periods.Instant((2022, 1, 1)), 2, 24],
    ])
def test_day_size_in_months(date_unit, instant, size, expected):
    """Returns the expected number of months."""

    period = periods.Period((date_unit, instant, size))

    assert period.size_in_months == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [periods.DateUnit.DAY, periods.Instant((2022, 12, 31)), 1, 1],
    [periods.DateUnit.DAY, periods.Instant((2022, 12, 31)), 3, 3],
    [periods.DateUnit.MONTH, periods.Instant((2012, 1, 3)), 3, 31 + 29 + 31],
    [periods.DateUnit.MONTH, periods.Instant((2012, 2, 3)), 1, 29],
    [periods.DateUnit.MONTH, periods.Instant((2022, 1, 3)), 3, 31 + 28 + 31],
    [periods.DateUnit.MONTH, periods.Instant((2022, 12, 1)), 1, 31],
    [periods.DateUnit.YEAR, periods.Instant((2012, 1, 1)), 1, 366],
    [periods.DateUnit.YEAR, periods.Instant((2022, 1, 1)), 2, 730],
    [periods.DateUnit.YEAR, periods.Instant((2022, 12, 1)), 1, 365],
    ])
def test_day_size_in_days(date_unit, instant, size, expected):
    """Returns the expected number of days."""

    period = periods.Period((date_unit, instant, size))

    assert period.size_in_days == expected


@pytest.mark.parametrize("period_unit, unit, start, cease, count", [
    [periods.DateUnit.YEAR, periods.DateUnit.YEAR, periods.Instant((2022, 1, 1)), periods.Instant((2024, 1, 1)), 3],
    [periods.DateUnit.YEAR, periods.DateUnit.MONTH, periods.Instant((2022, 12, 1)), periods.Instant((2025, 11, 1)), 36],
    [periods.DateUnit.YEAR, periods.DateUnit.DAY, periods.Instant((2022, 12, 31)), periods.Instant((2025, 12, 30)), 1096],
    [periods.DateUnit.MONTH, periods.DateUnit.MONTH, periods.Instant((2022, 12, 1)), periods.Instant((2023, 2, 1)), 3],
    [periods.DateUnit.MONTH, periods.DateUnit.DAY, periods.Instant((2022, 12, 31)), periods.Instant((2023, 3, 30)), 90],
    [periods.DateUnit.DAY, periods.DateUnit.DAY, periods.Instant((2022, 12, 31)), periods.Instant((2023, 1, 2)), 3],
    ])
def test_subperiods(instant, period_unit, unit, start, cease, count):
    """Returns the expected subperiods."""

    period = periods.Period((period_unit, instant, 3))
    subperiods = period.subperiods(unit)

    assert len(subperiods) == count
    assert subperiods[0] == periods.Period((unit, start, 1))
    assert subperiods[-1] == periods.Period((unit, cease, 1))


@pytest.mark.parametrize("period_unit, offset, unit, expected", [
    [periods.DateUnit.YEAR, "first-of", periods.DateUnit.YEAR, periods.Period(('year', periods.Instant((2022, 1, 1)), 3))],
    [periods.DateUnit.YEAR, "first-of", periods.DateUnit.MONTH, periods.Period(('year', periods.Instant((2022, 12, 1)), 3))],
    [periods.DateUnit.YEAR, "last-of", periods.DateUnit.YEAR, periods.Period(('year', periods.Instant((2022, 12, 31)), 3))],
    [periods.DateUnit.YEAR, "last-of", periods.DateUnit.MONTH, periods.Period(('year', periods.Instant((2022, 12, 31)), 3))],
    [periods.DateUnit.YEAR, -3, periods.DateUnit.YEAR, periods.Period(('year', periods.Instant((2019, 12, 31)), 3))],
    [periods.DateUnit.YEAR, 1, periods.DateUnit.MONTH, periods.Period(('year', periods.Instant((2023, 1, 31)), 3))],
    [periods.DateUnit.YEAR, 3, periods.DateUnit.DAY, periods.Period(('year', periods.Instant((2023, 1, 3)), 3))],
    [periods.DateUnit.MONTH, "first-of", periods.DateUnit.YEAR, periods.Period(('month', periods.Instant((2022, 1, 1)), 3))],
    [periods.DateUnit.MONTH, "first-of", periods.DateUnit.MONTH, periods.Period(('month', periods.Instant((2022, 12, 1)), 3))],
    [periods.DateUnit.MONTH, "last-of", periods.DateUnit.YEAR, periods.Period(('month', periods.Instant((2022, 12, 31)), 3))],
    [periods.DateUnit.MONTH, "last-of", periods.DateUnit.MONTH, periods.Period(('month', periods.Instant((2022, 12, 31)), 3))],
    [periods.DateUnit.MONTH, -3, periods.DateUnit.YEAR, periods.Period(('month', periods.Instant((2019, 12, 31)), 3))],
    [periods.DateUnit.MONTH, 1, periods.DateUnit.MONTH, periods.Period(('month', periods.Instant((2023, 1, 31)), 3))],
    [periods.DateUnit.MONTH, 3, periods.DateUnit.DAY, periods.Period(('month', periods.Instant((2023, 1, 3)), 3))],
    [periods.DateUnit.DAY, "first-of", periods.DateUnit.YEAR, periods.Period(('day', periods.Instant((2022, 1, 1)), 3))],
    [periods.DateUnit.DAY, "first-of", periods.DateUnit.MONTH, periods.Period(('day', periods.Instant((2022, 12, 1)), 3))],
    [periods.DateUnit.DAY, "last-of", periods.DateUnit.YEAR, periods.Period(('day', periods.Instant((2022, 12, 31)), 3))],
    [periods.DateUnit.DAY, "last-of", periods.DateUnit.MONTH, periods.Period(('day', periods.Instant((2022, 12, 31)), 3))],
    [periods.DateUnit.DAY, -3, periods.DateUnit.YEAR, periods.Period(('day', periods.Instant((2019, 12, 31)), 3))],
    [periods.DateUnit.DAY, 1, periods.DateUnit.MONTH, periods.Period(('day', periods.Instant((2023, 1, 31)), 3))],
    [periods.DateUnit.DAY, 3, periods.DateUnit.DAY, periods.Period(('day', periods.Instant((2023, 1, 3)), 3))],
    ])
def test_offset(instant, period_unit, offset, unit, expected):
    """Returns the expected ``Period``."""

    period = periods.Period((period_unit, instant, 3))

    assert period.offset(offset, unit) == expected
