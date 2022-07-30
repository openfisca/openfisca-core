import pytest

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
