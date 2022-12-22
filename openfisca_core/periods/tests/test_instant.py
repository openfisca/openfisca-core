import pytest

from openfisca_core.periods import DateUnit, Instant

day, month, year, eternity = DateUnit


@pytest.fixture
def instant():
    """Returns a ``Instant``."""

    return Instant(2020, 2, 29)


@pytest.mark.parametrize("offset, unit, expected", [
    ["first-of", month, Instant(2020, 2, 1)],
    ["first-of", year, Instant(2020, 1, 1)],
    ["last-of", month, Instant(2020, 2, 29)],
    ["last-of", year, Instant(2020, 12, 31)],
    [-3, day, Instant(2020, 2, 26)],
    [-3, month, Instant(2019, 11, 29)],
    [-3, year, Instant(2017, 2, 28)],
    [3, day, Instant(2020, 3, 3)],
    [3, month, Instant(2020, 5, 29)],
    [3, year, Instant(2023, 2, 28)],
    ])
def test_offset(instant, offset, unit, expected):
    """Returns the expected ``Instant``."""

    assert instant.offset(offset, unit) == expected
