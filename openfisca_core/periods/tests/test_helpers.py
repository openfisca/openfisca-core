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
DEADLINE = datetime.timedelta(milliseconds = 10)

# Number of random examples to run.
MAX_EXAMPLES = 5000


def one_of(*sts):
    """Random floats, strings, etc…"""

    return st.one_of(
        *sts,
        st.integers(datetime.MINYEAR, datetime.MAXYEAR),
        st.floats(),
        st.text(),
        st.none(),
        st.dates(),
        st.dates().map(datetime.date.isoformat),
        st.lists(*sts),
        st.tuples(*sts),
        )


def isintdate(date):
    return date.strip().isdecimal() and int(date) in OK_YEARS


def isisodate(date):
    try:
        return datetime.date.fromisoformat(date)
    except ValueError:
        with pytest.raises(ValueError):
            periods.instant(date)
        return


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
@hypothesis.settings(deadline = DEADLINE, max_examples = MAX_EXAMPLES)
def test_instant_contract(instant):
    """Raises when called with invalid arguments, works otherwise."""

    if instant is None:
        assert not periods.instant(instant)
        return

    if isinstance(instant, (Period, Instant, datetime.date, int)):
        assert isinstance(periods.instant(instant), Instant)
        return

    if isinstance(instant, str):
        if instant.find(":") != -1:
            unit, date, *rest = instant.split(":")

            if isintdate(date):
                instant = periods.instant(":".join([unit, date, *rest]))
                assert isinstance(instant, Instant)
                return

            if instant.find("-") != -1 and isisodate(instant):
                assert isinstance(periods.instant(instant), Instant)
                return

        if isintdate(instant):
            assert isinstance(periods.instant(instant), Instant)
            return

        if instant.find("-") != -1 and isisodate(instant):
            assert isinstance(periods.instant(instant), Instant)
            return

    if isinstance(instant, (list, tuple)):
        if len(instant) == 0:
            assert isinstance(periods.instant(instant), Instant)
            return

        if all(isinstance(unit, int) for unit in instant):
            assert isinstance(periods.instant(instant), Instant)
            return

        if all(isinstance(unit, str) and isintdate(unit) for unit in instant):
            assert isinstance(periods.instant(instant), Instant)
            return

    with pytest.raises(ValueError):
        periods.instant(instant)


@pytest.mark.parametrize("actual, expected", [
    (periods.instant("2021-09"), Instant((2021, 9, 1))),
    (periods.instant("2021-9-16"), Instant((2021, 9, 16))),
    (periods.instant("month:2021-9:2"), Instant((2021, 9, 1))),
    (periods.instant("year:2021"), Instant((2021, 1, 1))),
    (periods.instant("year:2021:1"), Instant((2021, 1, 1))),
    (periods.instant((2021, "9", "16")), Instant((2021, 9, 16))),
    (periods.instant((2021, 9, 16)), Instant((2021, 9, 16))),
    (periods.instant((2021, 9, 16, 42)), Instant((2021, 9, 16))),
    (periods.instant(["2021", "09", "16"]), Instant((2021, 9, 16))),
    (periods.instant(["2021", "9"]), Instant((2021, 9, 1))),
    ])
def test_instant(actual, expected):
    """It works :)."""

    assert actual == expected


def test_instant_date_deprecation():
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        periods.instant_date()


@hypothesis.given(
    one_of(
        st.sampled_from((
            Period((DateUnit.YEAR, Instant((1, 1, 1)), 3)),
            Instant((1, 1, 1)),
            DateUnit.ETERNITY,
            [2021, "-12"],
            "2021-31-12",
            "2021-foo",
            object()
            )),
        )
    )
@hypothesis.settings(deadline = DEADLINE, max_examples = MAX_EXAMPLES)
def test_period_contract(period):
    """Raises when called with invalid arguments, works otherwise."""

    if period is None:
        assert not periods.instant(period)
        return

    if period and period == DateUnit.ETERNITY:
        assert isinstance(periods.period(period), Period)
        return

    if isinstance(period, (Period, Instant, datetime.date, int)):
        assert isinstance(periods.period(period), Period)
        return

    if isinstance(period, str):
        if period.find(":") != -1:
            unit, date, *rest = period.split(":")

            if unit in DateUnit.isoformat and isisodate(date):
                assert isinstance(periods.period(period), Period)
                return

        if isintdate(period):
            assert isinstance(periods.period(period), Period)
            return

        if isisodate(period):
            assert isinstance(periods.period(period), Period)
            return

    with pytest.raises(ValueError):
        periods.period(period)


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
