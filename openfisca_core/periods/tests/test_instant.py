import calendar
import datetime

import hypothesis
import pytest
from hypothesis import strategies as st

from openfisca_core.periods import Instant, DateUnit

# Number of days in a month, for each month.
DAYS_IN_MONTH = calendar.mdays

# Valid ranges for years.
MIN_YEAR = datetime.MINYEAR
MAX_YEAR = datetime.MAXYEAR
OK_YEARS = range(MIN_YEAR, MAX_YEAR + 1)
ST_YEARS = st.integers(OK_YEARS[0] - 1, OK_YEARS[-1] + 1)

# Valid ranges for months.
MIN_MONTH = datetime.date.min.month
MAX_MONTH = datetime.date.max.month
OK_MONTHS = range(MIN_MONTH, MAX_MONTH + 1)
ST_MONTHS = st.integers(OK_MONTHS[0] - 1, OK_MONTHS[-1] + 1)

# Valid ranges for days.
MIN_DAY = datetime.date.min.day
MAX_DAY = datetime.date.max.day
OK_DAYS = range(MIN_DAY, MAX_DAY + 1)
ST_DAYS = st.integers(OK_DAYS[0] - 1, OK_DAYS[-1] + 1)

# Valid date unit ranges for offset.
OK_UNITS = DateUnit.isoformat

# Fail if test execution time is slower than 1ms.
DEADLINE = datetime.timedelta(milliseconds = 10)

# Number of random examples to run.
MAX_EXAMPLES = 5000


def one_of(*sts):
    """Random floats, strings, etc…"""

    return st.one_of(*sts, st.floats(), st.text(), st.none())


@pytest.fixture(scope = "module")
def instant():
    """An instant."""

    return Instant((2020, 12, 31))


def test_instant_with_wrong_arity():
    """Raises ValueError when the wrong number of units are passed."""

    with pytest.raises(ValueError, match = f"expected 3"):
        Instant((1,))


@hypothesis.given(one_of(ST_YEARS), one_of(ST_MONTHS), one_of(ST_DAYS))
@hypothesis.settings(deadline = DEADLINE, max_examples = MAX_EXAMPLES)
def test_instant_contract(year, month, day):
    """Raises with wrong year/month/day, works otherwise."""

    # All units have to be integers, otherwise we raise.
    for unit in year, month, day:
        if not isinstance(unit, int):
            with pytest.raises(TypeError, match = "integer"):
                Instant((year, month, day))
            return

    # We draw exact number of days for the month ``month``.
    if month in OK_MONTHS:
        ok_days = range(1, DAYS_IN_MONTH[month] + 1)

    # If it is a leap year and ``month`` is February, we add ``29``.
    if calendar.isleap(year) and month == 2:
        ok_days = range(1, ok_days.stop + 1)

    # Year has to be within a valid range, otherwise we fail.
    if year not in OK_YEARS:
        with pytest.raises(ValueError, match = f"year {year} is out of range"):
            Instant((year, month, day))
        return

    # Month has to be within a valid range, otherwise we fail.
    if month not in OK_MONTHS:
        with pytest.raises(ValueError, match = "month must be in 1..12"):
            Instant((year, month, day))
        return

    # Day has to be within a valid range, otherwise we fail.
    if day not in ok_days:
        with pytest.raises(ValueError, match = "day is out of range"):
            Instant((year, month, day))
        return

    *units, = Instant((year, month, day))

    assert units == [year, month, day]


def test_period_deprecation(instant):
    """Throws a deprecation warning when called."""

    with pytest.warns(DeprecationWarning):
        instant.period(DateUnit.DAY)


def test_period_for_eternity(instant):
    """Throws an AssertionError when called with the eternity unit."""

    with pytest.raises(AssertionError, match = "eternity"):
        instant.period(DateUnit.ETERNITY)


def test_period_with_invalid_size(instant):
    """Throws an AssertionError when called with an invalid size."""

    with pytest.raises(AssertionError, match = "int >= 1"):
        instant.period(DateUnit.DAY, size = 0)


@hypothesis.given(
    st.sampled_from(OK_YEARS),
    st.sampled_from(OK_MONTHS),
    st.sampled_from(OK_DAYS),
    one_of(st.sampled_from(("first-of", "last-of", *OK_YEARS))),
    one_of(st.sampled_from(DateUnit)),
    )
@hypothesis.settings(deadline = DEADLINE, max_examples = MAX_EXAMPLES)
def test_offset_contract(year, month, day, offset, unit):
    """Raises when called with invalid values, works otherwise."""

    # We calculate the valid offset values for year.
    min_offset = - year + 1
    max_offset = MAX_YEAR - year + 1
    ok_offsets = range(min_offset, max_offset)

    # We already know it raises if out of bounds, so we continue.
    if offset not in ok_offsets:
        return

    # We draw exact number of days for the month ``month``.
    if month in OK_MONTHS:
        ok_days = range(1, DAYS_IN_MONTH[month] + 1)

    # If it is a leap year and ``month`` is February, we add ``29``.
    if calendar.isleap(year) and month == 2:
        ok_days = range(1, ok_days.stop + 1)

    # We already know it raises if out of bounds, so we continue.
    if day not in ok_days:
        return

    # Now we can create our Instant.
    start = Instant((year, month, day))

    # If the unit is invalid, we raise.
    if unit not in OK_UNITS:
        with pytest.raises(AssertionError, match = "day, month, year"):
            start.offset(offset, unit)
        return

    # If the unit is day, we can only do integer offsets.
    if unit == DateUnit.DAY and isinstance(offset, str):
        with pytest.raises(AssertionError, match = "any int"):
            start.offset(offset, unit)
        return

    # Up to this point, we know any non str/int offset is invalid.
    if not isinstance(offset, (str, int)):
        with pytest.raises(AssertionError, match = "any int"):
            start.offset(offset, unit)
        return

    # Any string not in nth-of is invalid.
    if isinstance(offset, str) and offset not in ("first-of", "last-of"):
        with pytest.raises(AssertionError, match = "any int"):
            start.offset(offset, unit)
        return

    # Finally if unit is year, it can't be out of bounds.
    if unit == DateUnit.YEAR and offset not in ok_offsets:
        with pytest.raises(ValueError, match = "out of range"):
            start.offset(offset, unit)
        return

    # Now we know our offset should always work.
    assert isinstance(start.offset(offset, unit), Instant)


@pytest.mark.parametrize("start, offset, after", [
    ((2020, 1, 1), ("first-of", DateUnit.MONTH), (2020, 1, 1)),
    ((2020, 1, 1), ("first-of", DateUnit.YEAR), (2020, 1, 1)),
    ((2020, 2, 1), ("first-of", DateUnit.MONTH), (2020, 2, 1)),
    ((2020, 2, 1), ("first-of", DateUnit.YEAR), (2020, 1, 1)),
    ((2020, 2, 3), ("first-of", DateUnit.MONTH), (2020, 2, 1)),
    ((2020, 2, 3), ("first-of", DateUnit.YEAR), (2020, 1, 1)),
    ])
def test_offset_first_of(start, offset, after):
    """It works ;)."""

    assert Instant(start).offset(*offset) == Instant(after)


@pytest.mark.parametrize("start, offset, after", [
    ((2020, 1, 1), ("last-of", DateUnit.MONTH), (2020, 1, 31)),
    ((2020, 1, 1), ("last-of", DateUnit.YEAR), (2020, 12, 31)),
    ((2020, 2, 1), ("last-of", DateUnit.MONTH), (2020, 2, 29)),
    ((2020, 2, 1), ("last-of", DateUnit.YEAR), (2020, 12, 31)),
    ((2020, 2, 3), ("last-of", DateUnit.MONTH), (2020, 2, 29)),
    ((2020, 2, 3), ("last-of", DateUnit.YEAR), (2020, 12, 31)),
    ])
def test_offset_last_of(start, offset, after):
    """It works ;)."""

    assert Instant(start).offset(*offset) == Instant(after)


@pytest.mark.parametrize("start, offset, after", [
    ((2020, 1, 1), (-1, DateUnit.YEAR), (2019, 1, 1)),
    ((2020, 1, 1), (-3, DateUnit.YEAR), (2017, 1, 1)),
    ((2020, 1, 1), (1, DateUnit.YEAR), (2021, 1, 1)),
    ((2020, 1, 1), (3, DateUnit.YEAR), (2023, 1, 1)),
    ((2020, 1, 31), (1, DateUnit.YEAR), (2021, 1, 31)),
    ((2020, 2, 29), (-1, DateUnit.YEAR), (2019, 2, 28)),
    ((2020, 2, 29), (1, DateUnit.YEAR), (2021, 2, 28)),
    ])
def test_offset_year(start, offset, after):
    """It works, including leap years ;)."""

    assert Instant(start).offset(*offset) == Instant(after)


@pytest.mark.parametrize("start, offset, after", [
    ((2020, 1, 1), (-1, DateUnit.MONTH), (2019, 12, 1)),
    ((2020, 1, 1), (-3, DateUnit.MONTH), (2019, 10, 1)),
    ((2020, 1, 1), (1, DateUnit.MONTH), (2020, 2, 1)),
    ((2020, 1, 31), (1, DateUnit.MONTH), (2020, 2, 29)),
    ((2020, 10, 2), (3, DateUnit.MONTH), (2021, 1, 2)),
    ((2020, 2, 28), (1, DateUnit.MONTH), (2020, 3, 28)),
    ((2020, 3, 31), (-1, DateUnit.MONTH), (2020, 2, 29)),
    ])
def test_offset_month(start, offset, after):
    """It works, including leap years ;)."""

    assert Instant(start).offset(*offset) == Instant(after)


@pytest.mark.parametrize("start, offset, after", [
    ((2020, 1, 1), (-1, DateUnit.DAY), (2019, 12, 31)),
    ((2020, 1, 1), (-3, DateUnit.DAY), (2019, 12, 29)),
    ((2020, 1, 1), (1, DateUnit.DAY), (2020, 1, 2)),
    ((2020, 1, 30), (3, DateUnit.DAY), (2020, 2, 2)),
    ((2020, 1, 31), (1, DateUnit.DAY), (2020, 2, 1)),
    ((2020, 2, 28), (1, DateUnit.DAY), (2020, 2, 29)),
    ((2020, 3, 1), (-1, DateUnit.DAY), (2020, 2, 29)),
    ])
def test_offset_day(start, offset, after):
    """It works, including leap years ;)."""

    assert Instant(start).offset(*offset) == Instant(after)
