import datetime

import pytest

from openfisca_core import periods


@pytest.fixture
def instant():
    """Returns a ``Instant``."""
    return periods.Instant((2020, 2, 29))


@pytest.mark.parametrize("offset, unit, expected", [
    ["first-of", periods.YEAR, periods.Instant((2020, 1, 1))],
    ["first-of", periods.MONTH, periods.Instant((2020, 2, 1))],
    ["last-of", periods.YEAR, periods.Instant((2020, 12, 31))],
    ["last-of", periods.MONTH, periods.Instant((2020, 2, 29))],
    [-3, periods.YEAR, periods.Instant((2017, 2, 28))],
    [-3, periods.MONTH, periods.Instant((2019, 11, 29))],
    [-3, periods.DAY, periods.Instant((2020, 2, 26))],
    [3, periods.YEAR, periods.Instant((2023, 2, 28))],
    [3, periods.MONTH, periods.Instant((2020, 5, 29))],
    [3, periods.DAY, periods.Instant((2020, 3, 3))],
    ])
def test_offset(instant, offset, unit, expected):
    """Returns the expected ``Instant``."""
    assert instant.offset(offset, unit) == expected


@pytest.mark.parametrize("offset, unit, expected", [
    ["first-of", periods.DAY, TypeError],
    ["last-of", periods.DAY, TypeError],
    ])
def test_offset_with_an_invalid_offset(instant, offset, unit, expected):
    """Raises ``OffsetTypeError`` when given an invalid offset."""

    with pytest.raises(TypeError):
        instant.offset(offset, unit)


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
    assert periods.Instant.build(arg) == expected


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
        periods.Instant.build(arg)
