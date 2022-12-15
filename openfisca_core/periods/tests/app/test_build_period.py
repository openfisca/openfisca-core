import datetime

import pytest

from openfisca_core import periods


@pytest.mark.parametrize("arg, expected", [
    ["1000", periods.Period((periods.DateUnit.YEAR, periods.Instant((1000, 1, 1)), 1))],
    ["1000-01", periods.Period((periods.DateUnit.MONTH, periods.Instant((1000, 1, 1)), 1))],
    ["1000-01-01", periods.Period((periods.DateUnit.DAY, periods.Instant((1000, 1, 1)), 1))],
    ["1004-02-29", periods.Period((periods.DateUnit.DAY, periods.Instant((1004, 2, 29)), 1))],
    ["ETERNITY", periods.Period((periods.DateUnit.ETERNITY, periods.Instant((1, 1, 1)), 1))],
    ["day:1000-01-01", periods.Period((periods.DateUnit.DAY, periods.Instant((1000, 1, 1)), 1))],
    ["day:1000-01-01:3", periods.Period((periods.DateUnit.DAY, periods.Instant((1000, 1, 1)), 3))],
    ["eternity", periods.Period((periods.DateUnit.ETERNITY, periods.Instant((1, 1, 1)), 1))],
    ["month:1000-01", periods.Period((periods.DateUnit.MONTH, periods.Instant((1000, 1, 1)), 1))],
    ["month:1000-01-01", periods.Period((periods.DateUnit.MONTH, periods.Instant((1000, 1, 1)), 1))],
    ["month:1000-01-01:3", periods.Period((periods.DateUnit.MONTH, periods.Instant((1000, 1, 1)), 3))],
    ["month:1000-01:3", periods.Period((periods.DateUnit.MONTH, periods.Instant((1000, 1, 1)), 3))],
    ["year:1000", periods.Period((periods.DateUnit.YEAR, periods.Instant((1000, 1, 1)), 1))],
    ["year:1000-01", periods.Period((periods.DateUnit.YEAR, periods.Instant((1000, 1, 1)), 1))],
    ["year:1000-01-01", periods.Period((periods.DateUnit.YEAR, periods.Instant((1000, 1, 1)), 1))],
    ["year:1000-01-01:3", periods.Period((periods.DateUnit.YEAR, periods.Instant((1000, 1, 1)), 3))],
    ["year:1000-01:3", periods.Period((periods.DateUnit.YEAR, periods.Instant((1000, 1, 1)), 3))],
    ["year:1000:3", periods.Period((periods.DateUnit.YEAR, periods.Instant((1000, 1, 1)), 3))],
    [-1, periods.Period((periods.DateUnit.YEAR, periods.Instant((-1, 1, 1)), 1))],
    [0, periods.Period((periods.DateUnit.YEAR, periods.Instant((0, 1, 1)), 1))],
    [1, periods.Period((periods.DateUnit.YEAR, periods.Instant((1, 1, 1)), 1))],
    [1000, periods.Period((periods.DateUnit.YEAR, periods.Instant((1000, 1, 1)), 1))],
    [1000, periods.Period((periods.DateUnit.YEAR, periods.Instant((1000, 1, 1)), 1))],
    [999, periods.Period((periods.DateUnit.YEAR, periods.Instant((999, 1, 1)), 1))],
    [periods.DateUnit.ETERNITY, periods.Period((periods.DateUnit.ETERNITY, periods.Instant((1, 1, 1)), 1))],
    [periods.Instant((1, 1, 1)), periods.Period((periods.DateUnit.DAY, periods.Instant((1, 1, 1)), 1))],
    [periods.Period((periods.DateUnit.DAY, periods.Instant((1, 1, 1)), 365)), periods.Period((periods.DateUnit.DAY, periods.Instant((1, 1, 1)), 365))],
    ])
def test_build_period(arg, expected):
    """Returns the expected ``Period``."""
    assert periods.build_period(arg) == expected


@pytest.mark.parametrize("arg, error", [
    ["", AttributeError],
    ["1", ValueError],
    ["1000-0", ValueError],
    ["1000-0-0", ValueError],
    ["1000-01-01:1", ValueError],
    ["1000-01:1", ValueError],
    ["1000-1", ValueError],
    ["1000-1-0", ValueError],
    ["1000-1-1", ValueError],
    ["1000-13", ValueError],
    ["1000-2-31", ValueError],
    ["1000:1", ValueError],
    ["1000:a", ValueError],
    ["1:1000", ValueError],
    ["999", ValueError],
    ["a", ValueError],
    ["a:1000", ValueError],
    ["day:1000-01", ValueError],
    ["day:1000-01:1", ValueError],
    ["day:1000:1", ValueError],
    ["month:1000", ValueError],
    ["month:1000:1", ValueError],
    ["year", ValueError],
    [("-1", "-1"), ValueError],
    [("-1", "-1", "-1"), ValueError],
    [("-1",), ValueError],
    [("1-1",), ValueError],
    [("1-1-1",), ValueError],
    [(), ValueError],
    [(-1, -1), ValueError],
    [(-1, -1, -1), ValueError],
    [(-1,), ValueError],
    [(1, 1), ValueError],
    [(1, 1, 1), ValueError],
    [(1,), ValueError],
    [(None, None), ValueError],
    [(None, None, None), ValueError],
    [(None, None, None, None), ValueError],
    [(None,), ValueError],
    [(datetime.date(1, 1, 1),), ValueError],
    [(periods.Instant((1, 1, 1)),), ValueError],
    [(periods.Period((periods.DateUnit.DAY, periods.Instant((1, 1, 1)), 365)),), ValueError],
    [None, ValueError],
    [datetime.date(1, 1, 1), ValueError],
    [periods.DateUnit.YEAR, ValueError],
    [{}, ValueError],
    ])
def test_build_period_with_an_invalid_argument(arg, error):
    """Raises ``ValueError`` when given an invalid argument."""

    with pytest.raises(error):
        periods.build_period(arg)
