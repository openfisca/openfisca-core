import pytest

from openfisca_core.periods import DateUnit, Instant


@pytest.mark.parametrize(
    ("instant", "offset", "unit", "expected"),
    [
        (Instant((2020, 2, 29)), "first-of", DateUnit.YEAR, Instant((2020, 1, 1))),
        (Instant((2020, 2, 29)), "first-of", DateUnit.MONTH, Instant((2020, 2, 1))),
        (Instant((2020, 2, 29)), "first-of", DateUnit.WEEK, Instant((2020, 2, 24))),
        (Instant((2020, 2, 29)), "first-of", DateUnit.DAY, None),
        (Instant((2020, 2, 29)), "first-of", DateUnit.WEEKDAY, None),
        (Instant((2020, 2, 29)), "last-of", DateUnit.YEAR, Instant((2020, 12, 31))),
        (Instant((2020, 2, 29)), "last-of", DateUnit.MONTH, Instant((2020, 2, 29))),
        (Instant((2020, 2, 29)), "last-of", DateUnit.WEEK, Instant((2020, 3, 1))),
        (Instant((2020, 2, 29)), "last-of", DateUnit.DAY, None),
        (Instant((2020, 2, 29)), "last-of", DateUnit.WEEKDAY, None),
        (Instant((2020, 2, 29)), -3, DateUnit.YEAR, Instant((2017, 2, 28))),
        (Instant((2020, 2, 29)), -3, DateUnit.MONTH, Instant((2019, 11, 29))),
        (Instant((2020, 2, 29)), -3, DateUnit.WEEK, Instant((2020, 2, 8))),
        (Instant((2020, 2, 29)), -3, DateUnit.DAY, Instant((2020, 2, 26))),
        (Instant((2020, 2, 29)), -3, DateUnit.WEEKDAY, Instant((2020, 2, 26))),
        (Instant((2020, 2, 29)), 3, DateUnit.YEAR, Instant((2023, 2, 28))),
        (Instant((2020, 2, 29)), 3, DateUnit.MONTH, Instant((2020, 5, 29))),
        (Instant((2020, 2, 29)), 3, DateUnit.WEEK, Instant((2020, 3, 21))),
        (Instant((2020, 2, 29)), 3, DateUnit.DAY, Instant((2020, 3, 3))),
        (Instant((2020, 2, 29)), 3, DateUnit.WEEKDAY, Instant((2020, 3, 3))),
    ],
)
def test_offset(instant, offset, unit, expected) -> None:
    assert instant.offset(offset, unit) == expected
