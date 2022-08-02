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


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.WEEK, Instant((2022, 1, 1)), 1, "2021-W052"],
    [DateUnit.WEEK, Instant((2022, 1, 1)), 3, "week:2021-W052:3"],
    [DateUnit.WEEK, Instant((2022, 3, 1)), 1, "2022-W09"],
    [DateUnit.WEEK, Instant((2022, 3, 1)), 3, "week:2022-W09:3"],
    ])
def test_str_with_weeks(date_unit, instant, size, expected):
    assert str(Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("date_unit, instant, size, expected", [
    [DateUnit.WEEKDAY, Instant((2022, 1, 1)), 1, "2021-W052-6"],
    [DateUnit.WEEKDAY, Instant((2022, 1, 1)), 3, "weekday:2021-W052-6:3"],
    [DateUnit.WEEKDAY, Instant((2022, 3, 1)), 1, "2022-W09-2"],
    [DateUnit.WEEKDAY, Instant((2022, 3, 1)), 3, "weekday:2022-W09-2:3"],
    ])
def test_str_with_weekdays(date_unit, instant, size, expected):
    assert str(Period((date_unit, instant, size))) == expected


@pytest.mark.parametrize("period_unit, sub_unit, instant, start, cease, count", [
    [DateUnit.YEAR, DateUnit.YEAR, Instant((2022, 12, 31)), Instant((2022, 1, 1)), Instant((2024, 1, 1)), 3],
    [DateUnit.YEAR, DateUnit.MONTH, Instant((2022, 12, 31)), Instant((2022, 12, 1)), Instant((2025, 11, 1)), 36],
    [DateUnit.YEAR, DateUnit.DAY, Instant((2022, 12, 31)), Instant((2022, 12, 31)), Instant((2025, 12, 30)), 1096],
    [DateUnit.YEAR, DateUnit.WEEK, Instant((2022, 12, 31)), Instant((2022, 12, 26)), Instant((2025, 12, 15)), 156],
    [DateUnit.YEAR, DateUnit.WEEKDAY, Instant((2022, 12, 31)), Instant((2022, 12, 31)), Instant((2025, 12, 26)), 1092],
    [DateUnit.MONTH, DateUnit.MONTH, Instant((2022, 12, 31)), Instant((2022, 12, 1)), Instant((2023, 2, 1)), 3],
    [DateUnit.MONTH, DateUnit.DAY, Instant((2022, 12, 31)), Instant((2022, 12, 31)), Instant((2023, 3, 30)), 90],
    [DateUnit.DAY, DateUnit.DAY, Instant((2022, 12, 31)), Instant((2022, 12, 31)), Instant((2023, 1, 2)), 3],
    [DateUnit.DAY, DateUnit.WEEKDAY, Instant((2022, 12, 31)), Instant((2022, 12, 31)), Instant((2023, 1, 2)), 3],
    [DateUnit.WEEK, DateUnit.DAY, Instant((2022, 12, 31)), Instant((2022, 12, 31)), Instant((2023, 1, 20)), 21],
    [DateUnit.WEEK, DateUnit.WEEK, Instant((2022, 12, 31)), Instant((2022, 12, 26)), Instant((2023, 1, 9)), 3],
    [DateUnit.WEEK, DateUnit.WEEKDAY, Instant((2022, 12, 31)), Instant((2022, 12, 31)), Instant((2023, 1, 20)), 21],
    [DateUnit.WEEKDAY, DateUnit.DAY, Instant((2022, 12, 31)), Instant((2022, 12, 31)), Instant((2023, 1, 2)), 3],
    [DateUnit.WEEKDAY, DateUnit.WEEKDAY, Instant((2022, 12, 31)), Instant((2022, 12, 31)), Instant((2023, 1, 2)), 3],
    ])
def test_subperiods(period_unit, sub_unit, instant, start, cease, count):
    period = Period((period_unit, instant, 3))
    subperiods = period.get_subperiods(sub_unit)
    assert len(subperiods) == count
    assert subperiods[0] == Period((sub_unit, start, 1))
    assert subperiods[-1] == Period((sub_unit, cease, 1))
