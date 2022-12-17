from __future__ import annotations

from typing import Any

import datetime

import pendulum
from pendulum.datetime import Date
from pendulum.parsing import ParserError

from ._errors import PeriodFormatError, PeriodTypeError
from ._units import DateUnit, DAY, ETERNITY, MONTH, YEAR
from .instant_ import Instant
from .period_ import Period

UNIT_MAPPING = {1: "year", 2: "month", 3: "day"}


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
    period = parse_period(value)

    if period is not None:
        return period

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
    period = parse_period(period)

    if not isinstance(period, Period):
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

    # If there are more than 2 ":" in the string, the period is invalid
    if len(rest) > 0:
        raise PeriodFormatError(value)

    # Reject ambiguous periods such as month:2014
    if period.unit > unit:
        raise PeriodFormatError(value)

    return Period((unit, period.start, size))


def parse_period(value: str) -> Period | None:
    """Parse periods respecting the ISO format.

    Args:
        value: A string such as such as "2012" or "2015-03".

    Returns:
        A Period.

    Raises:
        AttributeError: When arguments are invalid, like ``"-1"``.
        ValueError: When values are invalid, like ``"2022-32-13"``.

    Examples:
        >>> parse_period("2022")
        Period((year, Instant((2022, 1, 1)), 1))

        >>> parse_period("2022-02")
        Period((month, Instant((2022, 2, 1)), 1))

        >>> parse_period("2022-02-13")
        Period((day, Instant((2022, 2, 13)), 1))

    """

    # If it's a complex period, next!
    if len(value.split(":")) != 1:
        return None

    # Check for a non-empty string.
    if not (value and isinstance(value, str)):
        raise AttributeError

    # If it's negative period, next!
    if value[0] == "-" or len(value.split(":")) != 1:
        raise ValueError

    try:
        date = pendulum.parse(value, exact = True)

    except ParserError:
        return None

    if not isinstance(date, Date):
        raise ValueError

    # We get the shape of the string (e.g. "2012-02" = 2)
    size = len(value.split("-"))

    # We get the unit from the shape (e.g. 2 = "month")
    unit = DateUnit(pow(2, 3 - size))

    # We build the corresponding start instant
    start = Instant((date.year, date.month, date.day))

    # And return the period
    return Period((unit, start, 1))
