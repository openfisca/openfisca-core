import pytest

from openfisca_core.periods import DateUnit, Instant


@pytest.mark.parametrize("instant, offset, unit, expected", [
    [Instant((2020, 2, 29)), -3, DateUnit.YEAR, Instant((2017, 2, 28))],
    # [Instant((2020, 2, 29)), -3, DateUnit.MONTH, Instant((2019, 11, 29))],
    # [Instant((2020, 2, 29)), -3, DateUnit.DAY, Instant((2020, 2, 26))],
    # [Instant((2020, 2, 29)), -3, DateUnit.WEEK, Instant((2020, 2, 8))],
    # [Instant((2020, 2, 29)), -3, DateUnit.WEEKDAY, Instant((2020, 2, 26))],
    ])
def test_offset(instant, offset, unit, expected):
    assert instant.offset(offset, unit) == expected
