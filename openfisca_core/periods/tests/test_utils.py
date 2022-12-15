import pytest

from openfisca_core import periods


@pytest.mark.parametrize("arg, expected", [
    [periods.Period((periods.DateUnit.DAY, periods.Instant((1, 1, 1)), 365)), "100_365"],
    [periods.Period((periods.DateUnit.MONTH, periods.Instant((1, 1, 1)), 12)), "200_12"],
    [periods.Period((periods.DateUnit.YEAR, periods.Instant((1, 1, 1)), 2)), "300_2"],
    [periods.Period((periods.DateUnit.ETERNITY, periods.Instant((1, 1, 1)), 1)), "400_1"],
    [(periods.DateUnit.DAY, None, 1), "100_1"],
    [(periods.DateUnit.MONTH, None, -1000), "200_-1000"],
    ])
def test_key_period_size(arg, expected):
    """Returns the corresponding period's weight."""

    assert periods.key_period_size(arg) == expected
