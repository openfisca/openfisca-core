import datetime

import pytest

from openfisca_core import periods
from openfisca_core.periods import DateUnit, Instant, InstantError, Period


@pytest.mark.parametrize(
    ("arg", "expected"),
    [
        (datetime.date(1, 1, 1), Instant((1, 1, 1))),
        (Instant((1, 1, 1)), Instant((1, 1, 1))),
        (Period((DateUnit.DAY, Instant((1, 1, 1)), 365)), Instant((1, 1, 1))),
        (-1, Instant((-1, 1, 1))),
        (0, Instant((0, 1, 1))),
        (1, Instant((1, 1, 1))),
        (999, Instant((999, 1, 1))),
        (1000, Instant((1000, 1, 1))),
        ("1000", Instant((1000, 1, 1))),
        ("1000-01", Instant((1000, 1, 1))),
        ("1000-01-01", Instant((1000, 1, 1))),
        ((-1,), Instant((-1, 1, 1))),
        ((-1, -1), Instant((-1, -1, 1))),
        ((-1, -1, -1), Instant((-1, -1, -1))),
    ],
)
def test_instant(arg, expected) -> None:
    assert periods.instant(arg) == expected


@pytest.mark.parametrize(
    ("arg", "error"),
    [
        (None, InstantError),
        (DateUnit.YEAR, ValueError),
        (DateUnit.ETERNITY, ValueError),
        ("1000-0", ValueError),
        ("1000-0-0", ValueError),
        ("1000-1", ValueError),
        ("1000-1-1", ValueError),
        ("1", ValueError),
        ("a", ValueError),
        ("year", ValueError),
        ("eternity", ValueError),
        ("999", ValueError),
        ("1:1000-01-01", ValueError),
        ("a:1000-01-01", ValueError),
        ("year:1000-01-01", ValueError),
        ("year:1000-01-01:1", ValueError),
        ("year:1000-01-01:3", ValueError),
        ("1000-01-01:a", ValueError),
        ("1000-01-01:1", ValueError),
        ((), InstantError),
        ({}, InstantError),
        ("", InstantError),
        ((None,), InstantError),
        ((None, None), InstantError),
        ((None, None, None), InstantError),
        ((None, None, None, None), InstantError),
        (("-1",), InstantError),
        (("-1", "-1"), InstantError),
        (("-1", "-1", "-1"), InstantError),
        (("1-1",), InstantError),
        (("1-1-1",), InstantError),
        ((datetime.date(1, 1, 1),), InstantError),
        ((Instant((1, 1, 1)),), InstantError),
        ((Period((DateUnit.DAY, Instant((1, 1, 1)), 365)),), InstantError),
    ],
)
def test_instant_with_an_invalid_argument(arg, error) -> None:
    with pytest.raises(error):
        periods.instant(arg)
