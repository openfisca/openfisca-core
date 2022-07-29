import datetime

import pytest

from openfisca_core import periods
from openfisca_core.periods import DateUnit, Instant, Period, helpers


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
    ["1000-01", Instant((1000, 1, 1))],
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
    [DateUnit.YEAR, ValueError],
    [DateUnit.ETERNITY, ValueError],
    ["1000-0", ValueError],
    ["1000-0-0", ValueError],
    ["1000-1", ValueError],
    ["1000-1-1", ValueError],
    ["1", ValueError],
    ["a", ValueError],
    ["year", ValueError],
    ["eternity", ValueError],
    ["999", ValueError],
    ["1:1000-01-01", ValueError],
    ["a:1000-01-01", ValueError],
    ["year:1000-01-01", ValueError],
    ["year:1000-01-01:1", ValueError],
    ["year:1000-01-01:3", ValueError],
    ["1000-01-01:a", ValueError],
    ["1000-01-01:1", ValueError],
    [(), AssertionError],
    [{}, AssertionError],
    ["", ValueError],
    [(None, None, None, None), AssertionError],
    ])
def test_instant_with_an_invalid_argument(arg, error):
    with pytest.raises(error):
        periods.instant(arg)


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


@pytest.mark.parametrize("arg, expected", [
    ["eternity", Period((DateUnit.ETERNITY, Instant((1, 1, 1)), float("inf")))],
    ["ETERNITY", Period((DateUnit.ETERNITY, Instant((1, 1, 1)), float("inf")))],
    [DateUnit.ETERNITY, Period((DateUnit.ETERNITY, Instant((1, 1, 1)), float("inf")))],
    [Instant((1, 1, 1)), Period((DateUnit.DAY, Instant((1, 1, 1)), 1))],
    [Period((DateUnit.DAY, Instant((1, 1, 1)), 365)), Period((DateUnit.DAY, Instant((1, 1, 1)), 365))],
    [-1, Period((DateUnit.YEAR, Instant((-1, 1, 1)), 1))],
    [0, Period((DateUnit.YEAR, Instant((0, 1, 1)), 1))],
    [1, Period((DateUnit.YEAR, Instant((1, 1, 1)), 1))],
    [999, Period((DateUnit.YEAR, Instant((999, 1, 1)), 1))],
    [1000, Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
    ["1000", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
    ["1000-1", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
    ["1000-1-1", Period((DateUnit.DAY, Instant((1000, 1, 1)), 1))],
    ["1000-01", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
    ["1000-01-01", Period((DateUnit.DAY, Instant((1000, 1, 1)), 1))],
    ["1004-02-29", Period((DateUnit.DAY, Instant((1004, 2, 29)), 1))],
    ["year:1000", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
    ["year:1000-01", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
    ["year:1000-01-01", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
    ["year:1000:1", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
    ["year:1000-01:1", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
    ["year:1000-01-01:1", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
    ["year:1000:3", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 3))],
    ["year:1000-01:3", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 3))],
    ["month:1000-01-01:3", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 3))],
    ["month:1000-01", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
    ["month:1000-01-01", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
    ["month:1000-01:1", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
    ["month:1000-01:3", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 3))],
    ["month:1000-01-01:3", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 3))],
    ["month:1000-01-01:3", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 3))],
    ["day:1000-01-01", Period((DateUnit.DAY, Instant((1000, 1, 1)), 1))],
    ["day:1000-01-01:3", Period((DateUnit.DAY, Instant((1000, 1, 1)), 3))],
    ])
def test_period_with_a_valid_argument(arg, expected):
    assert periods.period(arg) == expected


@pytest.mark.parametrize("arg, error", [
    [None, ValueError],
    [DateUnit.YEAR, ValueError],
    [datetime.date(1, 1, 1), ValueError],
    ["1000-0", ValueError],
    ["1000-13", ValueError],
    ["1000-0-0", ValueError],
    ["1000-1-0", ValueError],
    ["1000-2-31", ValueError],
    ["1", ValueError],
    ["a", ValueError],
    ["year", ValueError],
    ["999", ValueError],
    ["1:1000", ValueError],
    ["a:1000", ValueError],
    ["month:1000", ValueError],
    ["day:1000-01", ValueError],
    ["1000:a", ValueError],
    ["1000:1", ValueError],
    ["1000-01:1", ValueError],
    ["1000-01-01:1", ValueError],
    ["month:1000:1", ValueError],
    ["day:1000:1", ValueError],
    ["day:1000-01:1", ValueError],
    [(), ValueError],
    [{}, ValueError],
    ["", ValueError],
    [(None,), ValueError],
    [(None, None), ValueError],
    [(None, None, None), ValueError],
    [(None, None, None, None), ValueError],
    [(datetime.date(1, 1, 1),), ValueError],
    [(Instant((1, 1, 1)),), ValueError],
    [(Period((DateUnit.DAY, Instant((1, 1, 1)), 365)),), ValueError],
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
def test_period_with_an_invalid_argument(arg, error):
    with pytest.raises(error):
        periods.period(arg)


@pytest.mark.parametrize("arg, expected", [
    ["1", None],
    ["999", None],
    ["1000", Period((DateUnit.YEAR, Instant((1000, 1, 1)), 1))],
    ["1000-1", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
    ["1000-01", Period((DateUnit.MONTH, Instant((1000, 1, 1)), 1))],
    ["1000-1-1", Period((DateUnit.DAY, Instant((1000, 1, 1)), 1))],
    ["1000-01-1", Period((DateUnit.DAY, Instant((1000, 1, 1)), 1))],
    ["1000-01-01", Period((DateUnit.DAY, Instant((1000, 1, 1)), 1))],
    ["1000-01-99", None],
    ])
def test__parse_simple_period_with_a_valid_argument(arg, expected):
    assert helpers._parse_simple_period(arg) == expected


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
