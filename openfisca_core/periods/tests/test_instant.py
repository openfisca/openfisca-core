import pytest

from openfisca_core import periods


@pytest.fixture
def instant():
    return periods.Instant((2020, 2, 29))


@pytest.mark.parametrize("offset, unit, expected", [
    ["first-of", periods.YEAR, periods.Instant((2020, 1, 1))],
    ["first-of", periods.MONTH, periods.Instant((2020, 2, 1))],
    ["first-of", periods.DAY, periods.Instant((2020, 2, 29))],
    ["last-of", periods.YEAR, periods.Instant((2020, 12, 31))],
    ["last-of", periods.MONTH, periods.Instant((2020, 2, 29))],
    ["last-of", periods.DAY, periods.Instant((2020, 2, 29))],
    [-3, periods.YEAR, periods.Instant((2017, 2, 28))],
    [-3, periods.MONTH, periods.Instant((2019, 11, 29))],
    [-3, periods.DAY, periods.Instant((2020, 2, 26))],
    [3, periods.YEAR, periods.Instant((2023, 2, 28))],
    [3, periods.MONTH, periods.Instant((2020, 5, 29))],
    [3, periods.DAY, periods.Instant((2020, 3, 3))],
    ])
def test_offset(instant, offset, unit, expected):
    assert instant.offset(offset, unit) == expected
