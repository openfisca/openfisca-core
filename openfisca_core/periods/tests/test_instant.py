import pytest

from openfisca_core import periods
from openfisca_core.periods import Instant


@pytest.fixture
def instant():
    return Instant((2020, 2, 29))


@pytest.mark.parametrize("offset, unit, expected", [
    ["first-of", periods.YEAR, Instant((2020, 1, 1))],
    ["first-of", periods.MONTH, Instant((2020, 2, 1))],
    ["first-of", periods.DAY, Instant((2020, 2, 29))],
    ["last-of", periods.YEAR, Instant((2020, 12, 31))],
    ["last-of", periods.MONTH, Instant((2020, 2, 29))],
    ["last-of", periods.DAY, Instant((2020, 2, 29))],
    [-3, periods.YEAR, Instant((2017, 2, 28))],
    [-3, periods.MONTH, Instant((2019, 11, 29))],
    [-3, periods.DAY, Instant((2020, 2, 26))],
    [3, periods.YEAR, Instant((2023, 2, 28))],
    [3, periods.MONTH, Instant((2020, 5, 29))],
    [3, periods.DAY, Instant((2020, 3, 3))],
    ])
def test_offset(instant, offset, unit, expected):
    assert expected == instant.offset(offset, unit)
