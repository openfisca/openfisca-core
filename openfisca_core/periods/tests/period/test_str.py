import pytest

from openfisca_core.periods import DateUnit, Instant, Period


@pytest.fixture
def first_jan():
    return Instant((2022, 1, 1))


@pytest.fixture
def first_march():
    return Instant((2022, 3, 1))


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