import pytest

from openfisca_core import periods
from openfisca_core.periods import Instant, Period


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
