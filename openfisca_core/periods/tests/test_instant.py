import datetime

import pytest

from openfisca_core import periods


@pytest.fixture
def instant():
    """Returns a ``Instant``."""
    return periods.Instant((2020, 2, 29))


@pytest.mark.parametrize("arg, expected", [
    [None, None],
    [periods.Instant((1, 1, 1)), datetime.date(1, 1, 1)],
    [periods.Instant((4, 2, 29)), datetime.date(4, 2, 29)],
    ])
def test_to_date(arg, expected):
    """Returns the expected ``date``."""
    assert periods.Instant.to_date(arg) == expected


@pytest.mark.parametrize("arg, error", [
    [(1, 1, 1), periods.InstantTypeError],
    [periods.Instant((-1, 1, 1)), ValueError],
    [periods.Instant((1, -1, 1)), ValueError],
    [periods.Instant((1, 1, -1)), ValueError],
    [periods.Instant((1, 13, 1)), ValueError],
    [periods.Instant((1, 1, 32)), ValueError],
    [periods.Instant((1, 2, 29)), ValueError],
    ])
def test_to_date_with_an_invalid_argument(arg, error):
    """Raises ``ValueError`` when given an invalid argument."""

    with pytest.raises(error):
        periods.Instant.to_date(arg)


@pytest.mark.parametrize("offset, unit, expected", [
    ["first-of", periods.YEAR, periods.Instant((2020, 1, 1))],
    ["first-of", periods.MONTH, periods.Instant((2020, 2, 1))],
    ["first-of", periods.DAY, periods.Instant((2020, 2, 29))],
    ["last-of", periods.YEAR, periods.Instant((2020, 12, 31))],
    ["last-of", periods.MONTH, periods.Instant((2020, 2, 29))],
    ["last-of", periods.DAY, periods.Instant((2020, 2, 29))],
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
