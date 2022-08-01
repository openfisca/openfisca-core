import pytest

from openfisca_core.periods import DateUnit, Instant


@pytest.mark.parametrize("instant, offset, unit, expected", [
    [Instant((2022, 2, 29)), -3, DateUnit.YEAR, Instant((2019, 2, 28))],
    [Instant((2022, 2, 29)), -3, DateUnit.MONTH, Instant((2021, 11, 29))],
    [Instant((2022, 2, 29)), -3, DateUnit.DAY, Instant((2022, 2, 26))],
    ])
def test_offset(instant, offset, unit, expected):
    assert instant.offset(offset, unit) == expected
