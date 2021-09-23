import datetime

import hypothesis
import pytest
from hypothesis import strategies as st

from openfisca_core import periods
from openfisca_core.periods import DateUnit, Instant, Period

# Valid ranges for years.
MIN_YEAR = datetime.MINYEAR
MAX_YEAR = datetime.MAXYEAR
OK_YEARS = range(MIN_YEAR, MAX_YEAR + 1)

# Fail if test execution time is slower than 1ms.
DEADLINE = datetime.timedelta(milliseconds = 1)


def one_of(*sts):
    """Random floats, strings, etc…"""

    return st.one_of(
        *sts,
        st.integers(datetime.MINYEAR, datetime.MAXYEAR),
        st.floats(),
        st.text(),
        st.none(),
        st.dates(),
        st.lists(*sts),
        st.tuples(*sts),
        )


@hypothesis.given(
    one_of(
        st.sampled_from((
            Period((DateUnit.YEAR, Instant((1, 1, 1)), 3)),
            Instant((1, 1, 1)),
            [2021, "-12"],
            "2021-31-12",
            "2021-foo",
            object()
            )),
        )
    )
@hypothesis.settings(deadline = DEADLINE, max_examples = 1000)
def test_instant_contract(instant):
    """Raises when called with invalid arguments, works otherwise."""

    if instant is None:
        assert not periods.instant(instant)
        return

    if isinstance(instant, (Period, Instant, datetime.date, int)):
        assert isinstance(periods.instant(instant), Instant)
        return

    if isinstance(instant, str):
        if instant.strip().isdigit() and int(instant) in OK_YEARS:
            assert isinstance(periods.instant(instant), Instant)
            return

    if isinstance(instant, (list, tuple)):
        if len(instant) == 0:
            assert isinstance(periods.instant(instant), Instant)
            return

        if all(isinstance(unit, int) for unit in instant):
            assert isinstance(periods.instant(instant), Instant)
            return

        if all(isinstance(unit, str) for unit in instant):
            if all(unit.strip().isdigit() for unit in instant):
                assert isinstance(periods.instant(instant), Instant)
                return

    with pytest.raises(ValueError):
        periods.instant(instant)


@pytest.mark.parametrize("actual, expected", [
    (periods.instant((2021, 9, 16)), Instant((2021, 9, 16))),
    (periods.instant(["2021", "9"]), Instant((2021, 9, 1))),
    (periods.instant(["2021", "09", "16"]), Instant((2021, 9, 16))),
    (periods.instant((2021, "9", "16")), Instant((2021, 9, 16))),
    (periods.instant((2021, 9, 16, 42)), Instant((2021, 9, 16))),
    (periods.instant("2021-09"), Instant((2021, 9, 1))),
    (periods.instant("2021-9-16"), Instant((2021, 9, 16))),
    (periods.instant("year:2021"), Instant((2021, 1, 1))),
    (periods.instant("year:2021:1"), Instant((2021, 1, 1))),
    (periods.instant("month:2021-9:2"), Instant((2021, 9, 1))),
    ])
def test_instant(actual, expected):
    """It works :)."""

    assert actual == expected


def test_instant_date_deprecation():
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        periods.instant_date()


@pytest.mark.parametrize("args", [
    [2021, "-12"],
    "2021-31-12",
    "2021-foo",
    "day:2014",
    object,
    ])
def test_period_with_invalid_arguments(args):
    """Raises a ValueError when called with invalid arguments."""

    with pytest.raises(ValueError, match = str(args)):
        periods.period(args)


@pytest.mark.parametrize("actual, expected", [
    (
        periods.period("ETERNITY"),
        Period(('eternity', Instant((1, 1, 1)), float("inf"))),
        ),
    (
        periods.period("2014-2"),
        Period(('month', Instant((2014, 2, 1)), 1)),
        ),
    (
        periods.period("2014-02"),
        Period(('month', Instant((2014, 2, 1)), 1)),
        ),
    (
        periods.period("2014-02-02"),
        Period(('day', Instant((2014, 2, 2)), 1)),
        ),
    ])
def test_period(actual, expected):
    """It works :)."""

    assert actual == expected


def test_N__deprecation():
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        periods.N_(object())
