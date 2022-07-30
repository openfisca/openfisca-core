import datetime

import pytest

from openfisca_core import periods
from openfisca_core.periods import Instant, Period


@pytest.mark.parametrize("arg, expected", [
    ["eternity", Period((periods.ETERNITY, Instant((1, 1, 1)), float("inf")))],
    ["ETERNITY", Period((periods.ETERNITY, Instant((1, 1, 1)), float("inf")))],
    [periods.ETERNITY, Period((periods.ETERNITY, Instant((1, 1, 1)), float("inf")))],
    [Instant((1, 1, 1)), Period((periods.DAY, Instant((1, 1, 1)), 1))],
    [Period((periods.DAY, Instant((1, 1, 1)), 365)), Period((periods.DAY, Instant((1, 1, 1)), 365))],
    [-1, Period((periods.YEAR, Instant((-1, 1, 1)), 1))],
    [0, Period((periods.YEAR, Instant((0, 1, 1)), 1))],
    [1, Period((periods.YEAR, Instant((1, 1, 1)), 1))],
    [999, Period((periods.YEAR, Instant((999, 1, 1)), 1))],
    [1000, Period((periods.YEAR, Instant((1000, 1, 1)), 1))],
    ["1000", Period((periods.YEAR, Instant((1000, 1, 1)), 1))],
    ["1000-1", Period((periods.MONTH, Instant((1000, 1, 1)), 1))],
    ["1000-1-1", Period((periods.DAY, Instant((1000, 1, 1)), 1))],
    ["1000-01", Period((periods.MONTH, Instant((1000, 1, 1)), 1))],
    ["1000-01-01", Period((periods.DAY, Instant((1000, 1, 1)), 1))],
    ["year:1000-01-01", Period((periods.YEAR, Instant((1000, 1, 1)), 1))],
    ["year:1000-01-01:1", Period((periods.YEAR, Instant((1000, 1, 1)), 1))],
    ["year:1000-01-01:3", Period((periods.YEAR, Instant((1000, 1, 1)), 3))],
    ])
def test_instant_with_a_valid_argument(arg, expected):
    assert periods.period(arg) == expected


@pytest.mark.parametrize("arg, error", [
    [None, ValueError],
    [periods.YEAR, ValueError],
    [datetime.date(1, 1, 1), ValueError],
    ["1000-0", ValueError],
    ["1000-0-0", ValueError],
    ["1", ValueError],
    ["a", ValueError],
    ["year", ValueError],
    ["999", ValueError],
    ["1:1000-01-01", ValueError],
    ["a:1000-01-01", ValueError],
    ["1000-01-01:a", ValueError],
    ["1000-01-01:1", ValueError],
    [(), ValueError],
    [(None,), ValueError],
    [(None, None), ValueError],
    [(None, None, None), ValueError],
    [(None, None, None, None), ValueError],
    [(datetime.date(1, 1, 1),), ValueError],
    [(Instant((1, 1, 1)),), ValueError],
    [(Period((periods.DAY, Instant((1, 1, 1)), 365)),), ValueError],
    [(1,), ValueError],
    [(1, 1), ValueError],
    [(1, 1, 1), ValueError],
    [(-1,), ValueError],
    [(-1, -1), ValueError],
    [(-1, -1, -1), ValueError],
    [("-1",), ValueError],
    [("-1", "-1"), ValueError],
    [("-1", "-1", "-1"), ValueError],
    [("1-1",), ValueError],
    [("1-1-1",), ValueError],
    ])
def test_instant_with_an_invalid_argument(arg, error):
    with pytest.raises(error):
        periods.period(arg)
