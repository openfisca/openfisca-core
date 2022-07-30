import datetime

import pytest

from openfisca_core import periods
from openfisca_core.periods import DateUnit, Instant, Period


@pytest.mark.parametrize("arg, expected", [
    [None, None],
    [datetime.date(1, 1, 1), Instant((1, 1, 1))],
    [Instant((1, 1, 1)), Instant((1, 1, 1))],
    [Period((DateUnit.DAY, Instant((1, 1, 1)), 365)), Instant((1, 1, 1))],
    [-1, Instant((-1, 1, 1))],
    [0, Instant((0, 1, 1))],
    [1, Instant((1, 1, 1))],
    [999, Instant((999, 1, 1))],
    [1000, Instant((1000, 1, 1))],
    ["1000", Instant((1000, 1, 1))],
    ["1000-01-01", Instant((1000, 1, 1))],
    [(None,), Instant((None, 1, 1))],
    [(None, None), Instant((None, None, 1))],
    [(None, None, None), Instant((None, None, None))],
    [(datetime.date(1, 1, 1),), Instant((datetime.date(1, 1, 1), 1, 1))],
    [(Instant((1, 1, 1)),), Instant((Instant((1, 1, 1)), 1, 1))],
    [(Period((DateUnit.DAY, Instant((1, 1, 1)), 365)),), Instant((Period((DateUnit.DAY, Instant((1, 1, 1)), 365)), 1, 1))],
    [(-1,), Instant((-1, 1, 1))],
    [(-1, -1), Instant((-1, -1, 1))],
    [(-1, -1, -1), Instant((-1, -1, -1))],
    [("-1",), Instant(("-1", 1, 1))],
    [("-1", "-1"), Instant(("-1", "-1", 1))],
    [("-1", "-1", "-1"), Instant(("-1", "-1", "-1"))],
    [("1-1",), Instant(("1-1", 1, 1))],
    [("1-1-1",), Instant(("1-1-1", 1, 1))],
    ])
def test_instant_with_a_valid_argument(arg, expected):
    assert periods.instant(arg) == expected


@pytest.mark.parametrize("arg, error", [
    ["1000-0", ValueError],
    ["1000-0-0", ValueError],
    ["1000-1", ValueError],
    ["1000-1-1", ValueError],
    ["1", ValueError],
    ["a", ValueError],
    ["999", ValueError],
    ["1:1000-01-01", ValueError],
    ["a:1000-01-01", ValueError],
    ["year:1000-01-01", ValueError],
    ["year:1000-01-01:1", ValueError],
    ["year:1000-01-01:3", ValueError],
    ["1000-01-01:a", ValueError],
    ["1000-01-01:1", ValueError],
    [(), AssertionError],
    [(None, None, None, None), AssertionError],
    ])
def test_instant_with_an_invalid_argument(arg, error):
    with pytest.raises(error):
        periods.instant(arg)
