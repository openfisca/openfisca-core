import datetime

import pytest

from openfisca_core import periods


@pytest.mark.parametrize("arg, expected", [
    [None, None],
    [datetime.date(1, 1, 1), periods.Instant((1, 1, 1))],
    [periods.Instant((1, 1, 1)), periods.Instant((1, 1, 1))],
    [periods.Period((periods.DAY, periods.Instant((1, 1, 1)), 365)), periods.Instant((1, 1, 1))],
    [1000, periods.Instant((1000, 1, 1))],
    ["1000", periods.Instant((1000, 1, 1))],
    ["1000-01", periods.Instant((1000, 1, 1))],
    ["1000-01-01", periods.Instant((1000, 1, 1))],
    ])
def test_build_instant(arg, expected):
    """Returns the expected ``Instant``."""
    assert periods.build_instant(arg) == expected


@pytest.mark.parametrize("arg, error", [
    [periods.YEAR, ValueError],
    [periods.ETERNITY, ValueError],
    ["1000-0", ValueError],
    ["1000-1", ValueError],
    ["1000-13", ValueError],
    ["1000-0-0", ValueError],
    ["1000-1-1", ValueError],
    ["1000-01-0", ValueError],
    ["1000-01-1", ValueError],
    ["1000-01-32", ValueError],
    ["month:1000", ValueError],
    ["month:1000:1", ValueError],
    ["year:1000-01-01", ValueError],
    ["year:1000-01-01:1", ValueError],
    ["year:1000-01-01:3", ValueError],
    ])
def test_build_instant_with_an_invalid_argument(arg, error):
    """Raises ``ValueError`` when given an invalid argument."""

    with pytest.raises(error):
        periods.build_instant(arg)


@pytest.mark.parametrize("arg, expected", [
    ["eternity", periods.Period((periods.ETERNITY, periods.Instant((1, 1, 1)), float("inf")))],
    ["ETERNITY", periods.Period((periods.ETERNITY, periods.Instant((1, 1, 1)), float("inf")))],
    [periods.ETERNITY, periods.Period((periods.ETERNITY, periods.Instant((1, 1, 1)), float("inf")))],
    [periods.Instant((1, 1, 1)), periods.Period((periods.DAY, periods.Instant((1, 1, 1)), 1))],
    [periods.Period((periods.DAY, periods.Instant((1, 1, 1)), 365)), periods.Period((periods.DAY, periods.Instant((1, 1, 1)), 365))],
    [1000, periods.Period((periods.YEAR, periods.Instant((1000, 1, 1)), 1))],
    ["1000", periods.Period((periods.YEAR, periods.Instant((1000, 1, 1)), 1))],
    ["1000-01", periods.Period((periods.MONTH, periods.Instant((1000, 1, 1)), 1))],
    ["1000-01-01", periods.Period((periods.DAY, periods.Instant((1000, 1, 1)), 1))],
    ["1004-02-29", periods.Period((periods.DAY, periods.Instant((1004, 2, 29)), 1))],
    ["year:1000", periods.Period((periods.YEAR, periods.Instant((1000, 1, 1)), 1))],
    ["year:1000:3", periods.Period((periods.YEAR, periods.Instant((1000, 1, 1)), 3))],
    ["year:1000-01", periods.Period((periods.YEAR, periods.Instant((1000, 1, 1)), 1))],
    ["year:1000-01:3", periods.Period((periods.YEAR, periods.Instant((1000, 1, 1)), 3))],
    ["year:1000-01-01", periods.Period((periods.YEAR, periods.Instant((1000, 1, 1)), 1))],
    ["year:1000-01-01:3", periods.Period((periods.YEAR, periods.Instant((1000, 1, 1)), 3))],
    ["month:1000-01", periods.Period((periods.MONTH, periods.Instant((1000, 1, 1)), 1))],
    ["month:1000-01:3", periods.Period((periods.MONTH, periods.Instant((1000, 1, 1)), 3))],
    ["month:1000-01-01", periods.Period((periods.MONTH, periods.Instant((1000, 1, 1)), 1))],
    ["month:1000-01-01:3", periods.Period((periods.MONTH, periods.Instant((1000, 1, 1)), 3))],
    ["day:1000-01-01", periods.Period((periods.DAY, periods.Instant((1000, 1, 1)), 1))],
    ["day:1000-01-01:3", periods.Period((periods.DAY, periods.Instant((1000, 1, 1)), 3))],
    ])
def test_build_period(arg, expected):
    """Returns the expected ``Period``."""
    assert periods.build_period(arg) == expected


@pytest.mark.parametrize("arg, error", [
    [None, ValueError],
    [periods.YEAR, ValueError],
    [datetime.date(1, 1, 1), ValueError],
    ["1000:1", ValueError],
    ["1000-0", ValueError],
    ["1000-1", ValueError],
    ["1000-13", ValueError],
    ["1000-01:1", ValueError],
    ["1000-0-0", ValueError],
    ["1000-1-0", ValueError],
    ["1000-1-1", ValueError],
    ["1000-2-31", ValueError],
    ["1000-01-01:1", ValueError],
    ["month:1000", ValueError],
    ["month:1000:1", ValueError],
    ["day:1000:1", ValueError],
    ["day:1000-01", ValueError],
    ["day:1000-01:1", ValueError],
    ])
def test_build_period_with_an_invalid_argument(arg, error):
    """Raises ``ValueError`` when given an invalid argument."""

    with pytest.raises(error):
        periods.build_period(arg)


@pytest.mark.parametrize("arg, expected", [
    ["1", None],
    ["999", None],
    ["1000", periods.Period((periods.YEAR, periods.Instant((1000, 1, 1)), 1))],
    ["1000-01", periods.Period((periods.MONTH, periods.Instant((1000, 1, 1)), 1))],
    ["1000-01-01", periods.Period((periods.DAY, periods.Instant((1000, 1, 1)), 1))],
    ["1000-1", None],
    ["1000-1-1", None],
    ["1000-01-1", None],
    ["1000-01-99", None],
    ])
def test_parse_period(arg, expected):
    """Returns an ``Instant`` when given a valid ISO format string."""
    assert periods.parse_period(arg) == expected


@pytest.mark.parametrize("arg, expected", [
    [periods.Period((periods.DAY, periods.Instant((1, 1, 1)), 365)), "100_365"],
    [periods.Period((periods.MONTH, periods.Instant((1, 1, 1)), 12)), "200_12"],
    [periods.Period((periods.YEAR, periods.Instant((1, 1, 1)), 2)), "300_2"],
    [periods.Period((periods.ETERNITY, periods.Instant((1, 1, 1)), 1)), "400_1"],
    ])
def test_key_period_size_with_a_valid_argument(arg, expected):
    """Returns the corresponding period's weight."""
    assert periods.key_period_size(arg) == expected
