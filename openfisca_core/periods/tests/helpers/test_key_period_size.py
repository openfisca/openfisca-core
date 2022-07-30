import datetime

import pytest

from openfisca_core import periods
from openfisca_core.periods import DateUnit, Instant, Period


@pytest.mark.parametrize("arg, expected", [
    [Period((DateUnit.DAY, Instant((1, 1, 1)), 365)), "100_365"],
    [Period((DateUnit.MONTH, Instant((1, 1, 1)), 12)), "200_12"],
    [Period((DateUnit.YEAR, Instant((1, 1, 1)), 2)), "300_2"],
    [Period((DateUnit.ETERNITY, Instant((1, 1, 1)), 1)), "400_1"],
    [(DateUnit.DAY, None, 1), "100_1"],
    [(DateUnit.MONTH, None, -1000), "200_-1000"],
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
