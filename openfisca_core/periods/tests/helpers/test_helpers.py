import datetime

import pytest

from openfisca_core import periods
from openfisca_core.periods import DateUnit, Instant, Period


@pytest.mark.parametrize(
    ("arg", "expected"),
    [
        (None, None),
        (Instant((1, 1, 1)), datetime.date(1, 1, 1)),
        (Instant((4, 2, 29)), datetime.date(4, 2, 29)),
        ((1, 1, 1), datetime.date(1, 1, 1)),
    ],
)
def test_instant_date(arg, expected) -> None:
    assert periods.instant_date(arg) == expected


@pytest.mark.parametrize(
    ("arg", "error"),
    [
        (Instant((-1, 1, 1)), ValueError),
        (Instant((1, -1, 1)), ValueError),
        (Instant((1, 13, -1)), ValueError),
        (Instant((1, 1, -1)), ValueError),
        (Instant((1, 1, 32)), ValueError),
        (Instant((1, 2, 29)), ValueError),
        (Instant(("1", 1, 1)), TypeError),
        ((1,), TypeError),
        ((1, 1), TypeError),
    ],
)
def test_instant_date_with_an_invalid_argument(arg, error) -> None:
    with pytest.raises(error):
        periods.instant_date(arg)


@pytest.mark.parametrize(
    ("arg", "expected"),
    [
        (Period((DateUnit.WEEKDAY, Instant((1, 1, 1)), 5)), "100_5"),
        (Period((DateUnit.WEEK, Instant((1, 1, 1)), 26)), "200_26"),
        (Period((DateUnit.DAY, Instant((1, 1, 1)), 365)), "100_365"),
        (Period((DateUnit.MONTH, Instant((1, 1, 1)), 12)), "200_12"),
        (Period((DateUnit.YEAR, Instant((1, 1, 1)), 2)), "300_2"),
        (Period((DateUnit.ETERNITY, Instant((1, 1, 1)), 1)), "400_1"),
    ],
)
def test_key_period_size(arg, expected) -> None:
    assert periods.key_period_size(arg) == expected


@pytest.mark.parametrize(
    ("arg", "error"),
    [
        ((DateUnit.DAY, None, 1), AttributeError),
        ((DateUnit.MONTH, None, -1000), AttributeError),
    ],
)
def test_key_period_size_when_an_invalid_argument(arg, error):
    with pytest.raises(error):
        periods.key_period_size(arg)
