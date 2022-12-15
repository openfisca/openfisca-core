import datetime

import pytest

from openfisca_core import periods


@pytest.mark.parametrize("arg, expected", [
    ["1000", periods.Instant((1000, 1, 1))],
    ["1000", periods.Instant((1000, 1, 1))],
    ["1000-01", periods.Instant((1000, 1, 1))],
    ["1000-01", periods.Instant((1000, 1, 1))],
    ["1000-01-01", periods.Instant((1000, 1, 1))],
    ["1000-01-01", periods.Instant((1000, 1, 1))],
    [("-1", "-1"), periods.Instant(("-1", "-1", 1))],
    [("-1", "-1", "-1"), periods.Instant(("-1", "-1", "-1"))],
    [("-1",), periods.Instant(("-1", 1, 1))],
    [("1-1",), periods.Instant(("1-1", 1, 1))],
    [("1-1-1",), periods.Instant(("1-1-1", 1, 1))],
    [(-1, -1), periods.Instant((-1, -1, 1))],
    [(-1, -1, -1), periods.Instant((-1, -1, -1))],
    [(-1,), periods.Instant((-1, 1, 1))],
    [(None, None), periods.Instant((None, None, 1))],
    [(None, None, None), periods.Instant((None, None, None))],
    [(None,), periods.Instant((None, 1, 1))],
    [(datetime.date(1, 1, 1),), periods.Instant((datetime.date(1, 1, 1), 1, 1))],
    [(periods.Instant((1, 1, 1)),), periods.Instant((periods.Instant((1, 1, 1)), 1, 1))],
    [(periods.Period((periods.DateUnit.DAY, periods.Instant((1, 1, 1)), 365)),), periods.Instant((periods.Period((periods.DateUnit.DAY, periods.Instant((1, 1, 1)), 365)), 1, 1))],
    [-1, periods.Instant((-1, 1, 1))],
    [0, periods.Instant((0, 1, 1))],
    [1, periods.Instant((1, 1, 1))],
    [1000, periods.Instant((1000, 1, 1))],
    [999, periods.Instant((999, 1, 1))],
    [None, None],
    [datetime.date(1, 1, 1), periods.Instant((1, 1, 1))],
    [periods.Instant((1, 1, 1)), periods.Instant((1, 1, 1))],
    [periods.Period((periods.DateUnit.DAY, periods.Instant((1, 1, 1)), 365)), periods.Instant((1, 1, 1))],
    ])
def test_build_instant(arg, expected):
    """Returns the expected ``Instant``."""

    assert periods.build_instant(arg) == expected


@pytest.mark.parametrize("arg, error", [
    ["", ValueError],
    ["1", ValueError],
    ["1000-0", ValueError],
    ["1000-0-0", ValueError],
    ["1000-01-0", ValueError],
    ["1000-01-01:1", ValueError],
    ["1000-01-01:a", ValueError],
    ["1000-01-1", ValueError],
    ["1000-01-32", ValueError],
    ["1000-1", ValueError],
    ["1000-1-1", ValueError],
    ["1000-13", ValueError],
    ["1:1000-01-01", ValueError],
    ["999", ValueError],
    ["a", ValueError],
    ["a:1000-01-01", ValueError],
    ["eternity", ValueError],
    ["month:1000", ValueError],
    ["month:1000:1", ValueError],
    ["year", ValueError],
    ["year:1000-01-01", ValueError],
    ["year:1000-01-01:1", ValueError],
    ["year:1000-01-01:3", ValueError],
    [(), ValueError],
    [(None, None, None, None), ValueError],
    [periods.DateUnit.ETERNITY, ValueError],
    [periods.DateUnit.YEAR, ValueError],
    [{}, ValueError],
    ])
def test_build_instant_with_an_invalid_argument(arg, error):
    """Raises ``ValueError`` when given an invalid argument."""

    with pytest.raises(error):
        periods.build_instant(arg)
