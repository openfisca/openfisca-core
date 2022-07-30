import pytest

from openfisca_core import periods
from openfisca_core.periods import Instant, Period


@pytest.mark.parametrize("arg, expected", [
    [Period((periods.DAY, Instant((1, 1, 1)), 365)), "100_365"],
    [Period((periods.MONTH, Instant((1, 1, 1)), 12)), "200_12"],
    [Period((periods.YEAR, Instant((1, 1, 1)), 2)), "300_2"],
    [Period((periods.ETERNITY, Instant((1, 1, 1)), 1)), "400_1"],
    [(periods.DAY, None, 1), "100_1"],
    [(periods.MONTH, None, -1000), "200_-1000"],
    ])
def test_key_period_size_with_a_valid_argument(arg, expected):
    assert periods.key_period_size(arg) == expected


@pytest.mark.parametrize("arg, error", [
    [None, TypeError],
    [Instant((1, 1, 1)), KeyError],
    [1, TypeError],
    ["1", ValueError],
    ["111", KeyError],
    [(), ValueError],
    [(1, 1, 1), KeyError],
    ])
def test_key_period_size_with_an_invalid_argument(arg, error):
    with pytest.raises(error):
        periods.key_period_size(arg)
