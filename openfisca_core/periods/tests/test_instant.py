import datetime

import pytest

from openfisca_core.periods import DateUnit, Instant, Period

day, month, year, eternity = DateUnit


@pytest.fixture
def instant():
    """Returns a ``Instant``."""

    return Instant((2020, 2, 29))


@pytest.mark.parametrize("offset, unit, expected", [
    ["first-of", month, Instant((2020, 2, 1))],
    ["first-of", year, Instant((2020, 1, 1))],
    ["last-of", month, Instant((2020, 2, 29))],
    ["last-of", year, Instant((2020, 12, 31))],
    [-3, day, Instant((2020, 2, 26))],
    [-3, month, Instant((2019, 11, 29))],
    [-3, year, Instant((2017, 2, 28))],
    [3, day, Instant((2020, 3, 3))],
    [3, month, Instant((2020, 5, 29))],
    [3, year, Instant((2023, 2, 28))],
    ])
def test_offset(instant, offset, unit, expected):
    """Returns the expected ``Instant``."""

    assert instant.offset(offset, unit) == expected


@pytest.mark.parametrize("arg, expected", [
    ["1000", Instant((1000, 1, 1))],
    ["1000-01", Instant((1000, 1, 1))],
    ["1000-01-01", Instant((1000, 1, 1))],
    [1000, Instant((1000, 1, 1))],
    [(1000,), Instant((1000, 1, 1))],
    [(1000, 1), Instant((1000, 1, 1))],
    [(1000, 1, 1), Instant((1000, 1, 1))],
    [datetime.date(1, 1, 1), Instant((1, 1, 1))],
    [Instant((1, 1, 1)), Instant((1, 1, 1))],
    ])
def test_build_instant(arg, expected):
    """Returns the expected ``Instant``."""

    assert Instant.build(arg) == expected


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
    [Period((day, Instant((1, 1, 1)), 365)), ValueError],
    ])
def test_build_instant_with_an_invalid_argument(arg, error):
    """Raises ``ValueError`` when given an invalid argument."""

    with pytest.raises(error):
        Instant.build(arg)
