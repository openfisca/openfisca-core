from __future__ import annotations

from typing import Any

import datetime

from .._config import INSTANT_PATTERN, UNIT_WEIGHTS
from .._errors import InstantFormatError, InstantValueError, PeriodFormatError
from ..domain._instant import Instant
from ..domain._period import Period
from ..domain._unit import DateUnit
from ._parsers import parse_period


def build_instant(value: Any) -> Instant | None:
    """Build a new instant, aka a triple of integers (year, month, day).

    Args:
        value: An ``instant-like`` object.

    Returns:
        None: When ``instant`` is None.
        :obj:`.Instant`: Otherwise.

    Raises:
        InstantFormatError: When the arguments were invalid, like "2021-32-13".
        InstantValueError: When the length is out of range.

    Examples:
        >>> build_instant(datetime.date(2021, 9, 16))
        Instant((2021, 9, 16))

        >>> build_instant(Instant((2021, 9, 16)))
        Instant((2021, 9, 16))

        >>> build_instant(Period((DateUnit.YEAR, Instant((2021, 9, 16)), 1)))
        Instant((2021, 9, 16))

        >>> build_instant("2021")
        Instant((2021, 1, 1))

        >>> build_instant(2021)
        Instant((2021, 1, 1))

        >>> build_instant((2021, 9))
        Instant((2021, 9, 1))

    """

    if value is None:
        return None

    if isinstance(value, Instant):
        return value

    if isinstance(value, Period):
        return value.start

    if isinstance(value, str) and not INSTANT_PATTERN.match(value):
        raise InstantFormatError(value)

    if isinstance(value, str):
        instant = tuple(int(fragment) for fragment in value.split("-", 2)[:3])

    elif isinstance(value, datetime.date):
        instant = value.year, value.month, value.day

    elif isinstance(value, int):
        instant = value,

    elif isinstance(value, (tuple, list, dict)) and not 1 <= len(value) <= 3:
        raise InstantValueError(value)

    else:
        instant = tuple(value)

    if len(instant) == 1:
        return Instant((instant[0], 1, 1))

    if len(instant) == 2:
        return Instant((instant[0], instant[1], 1))

    return Instant(instant)


def build_period(value: Any) -> Period:
    """Build a new period, aka a triple (unit, start_instant, size).

    Args:
        value: A ``period-like`` object.

    Returns:
        :obj:`.Period`: A period.

    Raises:
        PeriodFormatError: When the arguments were invalid, like "2021-32-13".

    Examples:
        >>> build_period(Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1)))
        Period(('year', Instant((2021, 1, 1)), 1))

        >>> build_period(Instant((2021, 1, 1)))
        Period(('day', Instant((2021, 1, 1)), 1))

        >>> build_period(DateUnit.ETERNITY)
        Period(('eternity', Instant((1, 1, 1)), 1))

        >>> build_period(2021)
        Period(('year', Instant((2021, 1, 1)), 1))

        >>> build_period("2014")
        Period(('year', Instant((2014, 1, 1)), 1))

        >>> build_period("year:2014")
        Period(('year', Instant((2014, 1, 1)), 1))

        >>> build_period("month:2014-02")
        Period(('month', Instant((2014, 2, 1)), 1))

        >>> build_period("year:2014-02")
        Period(('year', Instant((2014, 2, 1)), 1))

        >>> build_period("day:2014-02-02")
        Period(('day', Instant((2014, 2, 2)), 1))

        >>> build_period("day:2014-02-02:3")
        Period(('day', Instant((2014, 2, 2)), 3))

    """

    if isinstance(value, Period):
        return value

    if isinstance(value, Instant):
        return Period((DateUnit.DAY, value, 1))

    if value == DateUnit.ETERNITY or value == DateUnit.ETERNITY.upper():
        return Period((DateUnit.ETERNITY, build_instant(datetime.date.min), 1))

    if isinstance(value, int):
        return Period((DateUnit.YEAR, Instant((value, 1, 1)), 1))

    if not isinstance(value, str):
        raise PeriodFormatError(value)

    # Try to parse as a simple period
    period = parse_period(value)

    if period is not None:
        return period

    if ":" not in value:
        raise PeriodFormatError(value)

    components = value.split(":")

    # Left-most component must be a valid unit
    unit = components[0]

    if unit not in (DateUnit.DAY, DateUnit.MONTH, DateUnit.YEAR):
        raise PeriodFormatError(value)

    # Middle component must be a valid iso period
    base_period = parse_period(components[1])

    if not base_period:
        raise PeriodFormatError(value)

    # Periods like year:2015-03 have a size of 1
    if len(components) == 2:
        size = 1

    elif len(components) == 3:
        try:
            size = int(components[2])

        except ValueError:
            raise PeriodFormatError(value)

    # If there are more than 2 ":" in the string, the period is invalid
    else:
        raise PeriodFormatError(value)

    # Reject ambiguous periods such as month:2014
    if UNIT_WEIGHTS[base_period.unit] > UNIT_WEIGHTS[DateUnit(unit)]:
        raise PeriodFormatError(value)

    return Period((unit, base_period.start, size))
