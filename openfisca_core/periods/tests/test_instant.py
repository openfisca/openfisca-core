import pytest

from openfisca_core.periods import Instant, DateUnit


@pytest.fixture
def instant():
    return Instant((2021, 12, 31))


def test_instant_init_with_nothing():
    """Raises ValueError when no units are passed."""

    with pytest.raises(ValueError, match = "(expected 3, got 0)"):
        Instant(())


def test_instant_init_with_year():
    """Raises ValueError when only year is passed."""

    with pytest.raises(ValueError, match = "(expected 3, got 1)"):
        Instant((2021,))


def test_instant_init_with_year_and_month():
    """Raises ValueError when only year and month are passed."""

    with pytest.raises(ValueError, match = "(expected 3, got 2)"):
        Instant((2021, 12))


def test_instant_init_when_bad_year():
    """Raises ValueError when the year is out of bounds."""

    with pytest.raises(ValueError, match = "year 0 is out of range"):
        Instant((0, 13, 31))


def test_instant_init_when_bad_month():
    """Raises ValueError when the month is out of bounds."""

    with pytest.raises(ValueError, match = "month must be in 1..12"):
        Instant((2021, 0, 31))


def test_instant_init_when_bad_day():
    """Raises ValueError when the day is out of bounds."""

    with pytest.raises(ValueError, match = "day is out of range for month"):
        Instant((2021, 12, 0))


def test_period_deprecation(instant):
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        instant.period(DateUnit.DAY.value)


def test_period_for_eternity(instant):
    """Throws an AssertionError when called with the eternity unit."""

    with pytest.raises(AssertionError, match = "eternity"):
        instant.period(DateUnit.ETERNITY.value)


def test_period_with_invalid_size(instant):
    """Throws an AssertionError when called with an invalid size."""

    with pytest.raises(AssertionError, match = "int >= 1"):
        instant.period(DateUnit.DAY.value, size = 0)


def test_offset_for_eternity(instant):
    """Throws an AssertionError when called with the eternity unit."""

    with pytest.raises(AssertionError, match = "eternity"):
        instant.offset("first-of", DateUnit.ETERNITY.value)


def test_offset_with_invalid_offset(instant):
    """Throws an AssertionError when called with an invalid offset."""

    with pytest.raises(AssertionError, match = "any int"):
        instant.offset("doomsday", DateUnit.YEAR.value)


@pytest.mark.parametrize("actual, offset, expected", [
    ((2020, 1, 1), (1, DateUnit.DAY.value), (2020, 1, 2)),
    ((2020, 1, 1), (1, DateUnit.MONTH.value), (2020, 2, 1)),
    ((2020, 1, 1), (1, DateUnit.YEAR.value), (2021, 1, 1)),
    ((2020, 1, 31), (1, DateUnit.DAY.value), (2020, 2, 1)),
    ((2020, 1, 31), (1, DateUnit.MONTH.value), (2020, 2, 29)),
    ((2020, 1, 31), (1, DateUnit.YEAR.value), (2021, 1, 31)),
    ((2020, 2, 28), (1, DateUnit.DAY.value), (2020, 2, 29)),
    ((2020, 2, 28), (1, DateUnit.MONTH.value), (2020, 3, 28)),
    ((2020, 2, 29), (1, DateUnit.YEAR.value), (2021, 2, 28)),
    ((2020, 1, 1), (-1, DateUnit.DAY.value), (2019, 12, 31)),
    ((2020, 1, 1), (-1, DateUnit.MONTH.value), (2019, 12, 1)),
    ((2020, 1, 1), (-1, DateUnit.YEAR.value), (2019, 1, 1)),
    ((2020, 3, 1), (-1, DateUnit.DAY.value), (2020, 2, 29)),
    ((2020, 3, 31), (-1, DateUnit.MONTH.value), (2020, 2, 29)),
    ((2020, 2, 29), (-1, DateUnit.YEAR.value), (2019, 2, 28)),
    ((2020, 1, 30), (3, DateUnit.DAY.value), (2020, 2, 2)),
    ((2020, 10, 2), (3, DateUnit.MONTH.value), (2021, 1, 2)),
    ((2020, 1, 1), (3, DateUnit.YEAR.value), (2023, 1, 1)),
    ((2020, 1, 1), (-3, DateUnit.DAY.value), (2019, 12, 29)),
    ((2020, 1, 1), (-3, DateUnit.MONTH.value), (2019, 10, 1)),
    ((2020, 1, 1), (-3, DateUnit.YEAR.value), (2017, 1, 1)),
    ((2020, 1, 1), ("first-of", DateUnit.MONTH.value), (2020, 1, 1)),
    ((2020, 2, 1), ("first-of", DateUnit.MONTH.value), (2020, 2, 1)),
    ((2020, 2, 3), ("first-of", DateUnit.MONTH.value), (2020, 2, 1)),
    ((2020, 1, 1), ("first-of", DateUnit.YEAR.value), (2020, 1, 1)),
    ((2020, 2, 1), ("first-of", DateUnit.YEAR.value), (2020, 1, 1)),
    ((2020, 2, 3), ("first-of", DateUnit.YEAR.value), (2020, 1, 1)),
    ((2020, 1, 1), ("last-of", DateUnit.MONTH.value), (2020, 1, 31)),
    ((2020, 2, 1), ("last-of", DateUnit.MONTH.value), (2020, 2, 29)),
    ((2020, 2, 3), ("last-of", DateUnit.MONTH.value), (2020, 2, 29)),
    ((2020, 1, 1), ("last-of", DateUnit.YEAR.value), (2020, 12, 31)),
    ((2020, 2, 1), ("last-of", DateUnit.YEAR.value), (2020, 12, 31)),
    ((2020, 2, 3), ("last-of", DateUnit.YEAR.value), (2020, 12, 31)),
    ])
def test_offset(actual, offset, expected):
    """It works ;)."""

    assert Instant(actual).offset(*offset) == Instant(expected)
