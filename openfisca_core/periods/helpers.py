from __future__ import annotations

from typing import Any

import datetime

from ._errors import PeriodFormatError, PeriodTypeError
from ._parsers import ISOFormat
from ._units import DateUnit, DAY, ETERNITY, MONTH, YEAR
from .instant_ import Instant
from .period_ import Period


def build_period(value: Any) -> Period:
    """Build a new period, aka a triple (unit, start_instant, size).

    Args:
        value: A ``period-like`` object.

    Returns:
        :obj:`.Period`: A period.

    Raises:
        PeriodFormatError: When the arguments were invalid, like "2021-32-13".

    Examples:
        >>> build_period(Period((YEAR, Instant((2021, 1, 1)), 1)))
        Period((year, Instant((2021, 1, 1)), 1))

        >>> build_period(Instant((2021, 1, 1)))
        Period((day, Instant((2021, 1, 1)), 1))

        >>> build_period(ETERNITY)
        Period((eternity, Instant((1, 1, 1)), 1))

        >>> build_period(2021)
        Period((year, Instant((2021, 1, 1)), 1))

        >>> build_period("2014")
        Period((year, Instant((2014, 1, 1)), 1))

        >>> build_period("year:2014")
        Period((year, Instant((2014, 1, 1)), 1))

        >>> build_period("month:2014-02")
        Period((month, Instant((2014, 2, 1)), 1))

        >>> build_period("year:2014-02")
        Period((year, Instant((2014, 2, 1)), 1))

        >>> build_period("day:2014-02-02")
        Period((day, Instant((2014, 2, 2)), 1))

        >>> build_period("day:2014-02-02:3")
        Period((day, Instant((2014, 2, 2)), 3))

    """

    if value in {ETERNITY, ETERNITY.name, ETERNITY.name.lower()}:
        return Period((ETERNITY, Instant.build(datetime.date.min), 1))

    if value is None or isinstance(value, DateUnit):
        raise PeriodTypeError(value)

    if isinstance(value, Period):
        return value

    if isinstance(value, Instant):
        return Period((DAY, value, 1))

    if isinstance(value, int):
        return Period((YEAR, Instant((value, 1, 1)), 1))

    if not isinstance(value, str):
        raise PeriodFormatError(value)

    # Try to parse as a simple period
    period = ISOFormat.parse(value)

    if period is not None:
        return Period((DateUnit(period.unit), Instant((period[1:-1])), 1))

    # Complex periods must have a ':' in their strings
    if ":" not in value:
        raise PeriodFormatError(value)

    # We know the first element has to be a ``unit``
    unit, *rest = value.split(":")

    # Units are case insensitive so we need to upper them
    unit = unit.upper()

    # Left-most component must be a valid unit
    if unit not in dir(DateUnit):
        raise PeriodFormatError(value)

    unit = DateUnit[unit]

    # We get the first remaining component
    period, *rest = rest

    # Middle component must be a valid ISO period
    period = ISOFormat.parse(period)

    if period is None:
        raise PeriodFormatError(value)

    # Finally we try to parse the size, if any
    try:
        size, *rest = rest

    except ValueError:
        size = 1

    # If provided, make sure the size is an integer
    try:
        size = int(size)

    except ValueError:
        raise PeriodFormatError(value)

    # If there were more than 2 ":" in the string, the period is invalid
    if len(rest) > 0:
        raise PeriodFormatError(value)

    # Reject ambiguous periods such as month:2014
    if period.unit > unit:
        raise PeriodFormatError(value)

    return Period((unit, Instant((period[1:-1])), size))
