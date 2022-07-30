import datetime

import pytest

from openfisca_core import periods
from openfisca_core.periods import Instant


@pytest.mark.parametrize("arg, expected", [
    [None, None],
    [Instant((1, 1, 1)), datetime.date(1, 1, 1)],
    [Instant((4, 2, 29)), datetime.date(4, 2, 29)],
    [(1, 1, 1), datetime.date(1, 1, 1)],
    ])
def test_instant_date_with_a_valid_argument(arg, expected):
    assert periods.instant_date(arg) == expected


@pytest.mark.parametrize("arg, error", [
    [Instant((-1, 1, 1)), ValueError],
    [Instant((1, -1, 1)), ValueError],
    [Instant((1, 13, -1)), ValueError],
    [Instant((1, 1, -1)), ValueError],
    [Instant((1, 1, 32)), ValueError],
    [Instant((1, 2, 29)), ValueError],
    [Instant(("1", 1, 1)), TypeError],
    [(1,), TypeError],
    [(1, 1), TypeError],
    ])
def test_instant_date_with_an_invalid_argument(arg, error):
    with pytest.raises(error):
        periods.instant_date(arg)
