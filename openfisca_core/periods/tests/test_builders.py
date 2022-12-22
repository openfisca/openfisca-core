import datetime

import pytest

from openfisca_core import periods
from openfisca_core.periods import DateUnit, Instant, Period

day, month, year, eternity = DateUnit


@pytest.mark.parametrize("arg, expected", [
    ["1000", Instant(1000, 1, 1)],
    ["1000-01", Instant(1000, 1, 1)],
    ["1000-01-01", Instant(1000, 1, 1)],
    [1000, Instant(1000, 1, 1)],
    [(1000,), Instant(1000, 1, 1)],
    [(1000, 1), Instant(1000, 1, 1)],
    [(1000, 1, 1), Instant(1000, 1, 1)],
    [datetime.date(1, 1, 1), Instant(1, 1, 1)],
    [Instant(1, 1, 1), Instant(1, 1, 1)],
    ])
def test_build_instant(arg, expected):
    """Returns the expected ``Instant``."""

    assert periods.instant(arg) == expected


@pytest.mark.parametrize("arg, error", [
    ["1000-0", ValueError],
    ["1000-0-0", ValueError],
    ["1000-01-0", ValueError],
    ["1000-01-01-01", ValueError],
    ["1000-01-1", ValueError],
    ["1000-01-32", ValueError],
    ["1000-1", ValueError],
    ["1000-1-1", ValueError],
    ["1000-13", ValueError],
    ["month:1000", ValueError],
    ["month:1000:1", ValueError],
    ["year:1000-01-01", ValueError],
    ["year:1000-01-01:1", ValueError],
    ["year:1000-01-01:3", ValueError],
    [None, TypeError],
    [eternity, ValueError],
    [year, ValueError],
    [Period(day, Instant(1, 1, 1), 365), ValueError],
    ])
def test_build_instant_with_an_invalid_argument(arg, error):
    """Raises ``ValueError`` when given an invalid argument."""

    with pytest.raises(error):
        periods.instant(arg)


@pytest.mark.parametrize("arg, expected", [
    ["1000", Period(year, Instant(1000, 1, 1), 1)],
    ["1000-01", Period(month, Instant(1000, 1, 1), 1)],
    ["1000-01-01", Period(day, Instant(1000, 1, 1), 1)],
    ["1004-02-29", Period(day, Instant(1004, 2, 29), 1)],
    ["ETERNITY", Period(eternity, Instant(1, 1, 1), 1)],
    ["day:1000-01-01", Period(day, Instant(1000, 1, 1), 1)],
    ["day:1000-01-01:3", Period(day, Instant(1000, 1, 1), 3)],
    ["eternity", Period(eternity, Instant(1, 1, 1), 1)],
    ["month:1000-01", Period(month, Instant(1000, 1, 1), 1)],
    ["month:1000-01-01", Period(month, Instant(1000, 1, 1), 1)],
    ["month:1000-01-01:3", Period(month, Instant(1000, 1, 1), 3)],
    ["month:1000-01:3", Period(month, Instant(1000, 1, 1), 3)],
    ["year:1000", Period(year, Instant(1000, 1, 1), 1)],
    ["year:1000-01", Period(year, Instant(1000, 1, 1), 1)],
    ["year:1000-01-01", Period(year, Instant(1000, 1, 1), 1)],
    ["year:1000-01-01:3", Period(year, Instant(1000, 1, 1), 3)],
    ["year:1000-01:3", Period(year, Instant(1000, 1, 1), 3)],
    ["year:1000:3", Period(year, Instant(1000, 1, 1), 3)],
    [1000, Period(year, Instant(1000, 1, 1), 1)],
    [eternity, Period(eternity, Instant(1, 1, 1), 1)],
    [Instant(1, 1, 1), Period(day, Instant(1, 1, 1), 1)],
    [Period(day, Instant(1, 1, 1), 365), Period(day, Instant(1, 1, 1), 365)],
    ["month:1000:1", Period(2, Instant(1000, 1, 1), 1)],
    ["month:1000", Period(2, Instant(1000, 1, 1), 1)],
    ["day:1000:1", Period(1, Instant(1000, 1, 1), 1)],
    ["day:1000-01:1", Period(1, Instant(1000, 1, 1), 1)],
    ["day:1000-01", Period(1, Instant(1000, 1, 1), 1)],
    ])
def test_build_period(arg, expected):
    """Returns the expected ``Period``."""

    assert periods.period(arg) == expected


@pytest.mark.parametrize("arg, error", [
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
    [None, TypeError],
    [datetime.date(1, 1, 1), ValueError],
    [year, TypeError],
    ])
def test_build_period_with_an_invalid_argument(arg, error):
    """Raises ``ValueError`` when given an invalid argument."""

    with pytest.raises(error):
        periods.period(arg)
