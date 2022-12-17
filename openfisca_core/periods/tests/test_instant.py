import datetime

import pytest

from openfisca_core import periods


@pytest.fixture
def instant():
    """Returns a ``Instant``."""

    return periods.instant((2020, 2, 29))


@pytest.mark.parametrize("offset, unit, expected", [
    ["first-of", periods.MONTH, periods.instant((2020, 2, 1))],
    ["first-of", periods.YEAR, periods.instant((2020, 1, 1))],
    ["last-of", periods.MONTH, periods.instant((2020, 2, 29))],
    ["last-of", periods.YEAR, periods.instant((2020, 12, 31))],
    [-3, periods.DAY, periods.instant((2020, 2, 26))],
    [-3, periods.MONTH, periods.instant((2019, 11, 29))],
    [-3, periods.YEAR, periods.instant((2017, 2, 28))],
    [3, periods.DAY, periods.instant((2020, 3, 3))],
    [3, periods.MONTH, periods.instant((2020, 5, 29))],
    [3, periods.YEAR, periods.instant((2023, 2, 28))],
    ])
def test_offset(instant, offset, unit, expected):
    """Returns the expected ``Instant``."""

    assert instant.offset(offset, unit) == expected


@pytest.mark.parametrize("arg, expected", [
    ["1000", periods.instant((1000, 1, 1))],
    ["1000-01", periods.instant((1000, 1, 1))],
    ["1000-01-01", periods.instant((1000, 1, 1))],
    [1000, periods.instant((1000, 1, 1))],
    [(1000,), periods.instant((1000, 1, 1))],
    [(1000, 1), periods.instant((1000, 1, 1))],
    [(1000, 1, 1), periods.instant((1000, 1, 1))],
    [datetime.date(1, 1, 1), periods.instant((1, 1, 1))],
    [periods.instant((1, 1, 1)), periods.instant((1, 1, 1))],
    ])
def test_build_instant(arg, expected):
    """Returns the expected ``Instant``."""

    assert periods.instant.build(arg) == expected


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
    [periods.ETERNITY, TypeError],
    [periods.YEAR, TypeError],
    [periods.period((periods.DAY, periods.instant((1, 1, 1)), 365)), TypeError],
    ])
def test_build_instant_with_an_invalid_argument(arg, error):
    """Raises ``ValueError`` when given an invalid argument."""

    with pytest.raises(error):
        periods.instant.build(arg)
