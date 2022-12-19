from __future__ import annotations

from typing import Any, Sequence

import datetime

import pendulum
from pendulum.datetime import Date
from pendulum.parsing import ParserError

from ._dates import DateUnit, ISOFormat
from ._errors import (
    InstantFormatError,
    InstantTypeError,
    PeriodFormatError,
    PeriodTypeError,
    )
from ._instants import Instant
from ._periods import Period

day, _month, year, eternity = tuple(DateUnit)


def build_instant(value: Any) -> Instant:
    """Build a new instant, aka a triple of integers (year, month, day).

    Args:
        value: An ``instant-like`` object.

    Returns:
        An Instant.

    Raises:
        InstantFormatError: When ``value`` is invalid, like "2021-32-13".
        InstantTypeError: When ``value`` is None.

    Examples:
        >>> build_instant(datetime.date(2021, 9, 16))
        Instant((2021, 9, 16))

        >>> build_instant(Instant((2021, 9, 16)))
        Instant((2021, 9, 16))

        >>> build_instant("2021")
        Instant((2021, 1, 1))

        >>> build_instant(2021)
        Instant((2021, 1, 1))

        >>> build_instant((2021, 9))
        Instant((2021, 9, 1))

        >>> start = Instant((2021, 9, 16))

        >>> build_instant(Period((year, start, 1)))
        Traceback (most recent call last):
        InstantFormatError: 'year:2021-09' is not a valid instant.

        .. versionadded:: 39.0.0

    """

    isoformat: ISOFormat | None

    if isinstance(value, Instant):
        return value

    if isinstance(value, datetime.date):
        return Instant((value.year, value.month, value.day))

    if isinstance(value, int):
        isoformat = parse_int(value)

    elif isinstance(value, str):
        isoformat = parse_instant_str(value)

    elif isinstance(value, (list, tuple)):
        isoformat = parse_seq(value)

    else:
        raise InstantTypeError(value)

    if isoformat is None:
        raise InstantFormatError(value)

    return Instant((isoformat.year, isoformat.month, isoformat.day))


def build_period(value: Any) -> Period:
    """Build a new period, aka a triple (unit, start_instant, size).

    Args:
        value: A ``period-like`` object.

    Returns:
        A period.

    Raises:
        PeriodFormatError: When arguments are invalid, like "2021-32-13".
        PeriodTypeError: When ``value`` is not a ``period-like`` object.

    Examples:
        >>> build_period(Period((year, Instant((2021, 1, 1)), 1)))
        Period((year, Instant((2021, 1, 1)), 1))

        >>> build_period(Instant((2021, 1, 1)))
        Period((day, Instant((2021, 1, 1)), 1))

        >>> build_period(eternity)
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

    if value in {eternity, eternity.name, eternity.name.lower()}:
        return Period((eternity, build_instant(datetime.date.min), 1))

    if value is None or isinstance(value, DateUnit):
        raise PeriodTypeError(value)

    if isinstance(value, Period):
        return value

    if isinstance(value, Instant):
        return Period((day, value, 1))

    if isinstance(value, int):
        return Period((year, Instant((value, 1, 1)), 1))

    if not isinstance(value, str):
        raise PeriodFormatError(value)

    # Try to parse as a complex period
    isoformat = parse_period_str(value)

    if isoformat is None:
        raise PeriodFormatError(value)

    unit = DateUnit(isoformat.unit)

    return Period((unit, build_instant(isoformat[:3]), isoformat.size))


def parse_int(value: int) -> ISOFormat | None:
    """Parse an int respecting the ISO format.

    Args:
        value: The integer to parse.

    Returns:
        An ISOFormat object if ``value`` is valid.
        None otherwise.

    Examples:
        >>> parse_int(1)
        ISOFormat(year=1, month=1, day=1, unit=4, size=1)

        >>> parse_int(2023)
        ISOFormat(year=2023, month=1, day=1, unit=4, size=1)

        >>> parse_int(-1)

        >>> parse_int("2023")

        >>> parse_int(20231231)

    .. versionadded:: 39.0.0

    """

    if not isinstance(value, int):
        return None

    if not 1 <= len(str(value)) <= 4:
        return None

    try:
        if not 1 <= int(str(value)[:4]) < 10000:
            return None

    except ValueError:
        return None

    return ISOFormat(value, 1, 1, 4, 1)


def parse_seq(value: Sequence[int]) -> ISOFormat | None:
    """Parse a sequence of ints respecting the ISO format.

    Args:
        value: A sequence of ints such as [2012, 3, 13].

    Returns:
        An ISOFormat object if ``value`` is valid.
        None if ``value`` is not valid.

    Examples:
        >>> parse_seq([2022])
        ISOFormat(year=2022, month=1, day=1, unit=4, size=1)

        >>> parse_seq([2022, 1])
        ISOFormat(year=2022, month=1, day=1, unit=2, size=1)

        >>> parse_seq([2022, 1, 1])
        ISOFormat(year=2022, month=1, day=1, unit=1, size=1)

        >>> parse_seq([-2022, 1, 1])

        >>> parse_seq([2022, 13, 1])

        >>> parse_seq([2022, 1, 32])

    .. versionadded:: 39.0.0

    """

    if not isinstance(value, (list, tuple)):
        return None

    if not value:
        return None

    if not 1 <= len(value) <= 3:
        return None

    if not all(isinstance(unit, int) for unit in value):
        return None

    if not all(unit == abs(unit) for unit in value):
        return None

    # We get the shape of the string (e.g. "2012-02" = 2)
    shape = len(value)

    # We get the unit from the shape (e.g. 2 = "month")
    unit = tuple(DateUnit)[3 - shape]

    while len(value) < 3:
        value = (*value, 1)

    try:
        # We parse the date
        date = pendulum.date(*value)

    except ValueError:
        return None

    if not isinstance(date, Date):
        return None

    # We build the corresponding ISOFormat object
    return ISOFormat(date.year, date.month, date.day, unit.value, 1)


def parse_instant_str(value: str) -> ISOFormat | None:
    """Parse strings respecting the ISO format.

    Args:
        value: A string such as such as "2012" or "2015-03".

    Returns:
        An ISOFormat object if ``value`` is valid.
        None if ``value`` is not valid.

    Examples:
        >>> parse_instant_str("2022")
        ISOFormat(year=2022, month=1, day=1, unit=4, size=1)

        >>> parse_instant_str("2022-02")
        ISOFormat(year=2022, month=2, day=1, unit=2, size=1)

        >>> parse_instant_str("2022-02-13")
        ISOFormat(year=2022, month=2, day=13, unit=1, size=1)

        >>> parse_instant_str(1000)

        >>> parse_instant_str("ETERNITY")

    .. versionadded:: 39.0.0

    """

    if not isinstance(value, str):
        return None

    if not value:
        return None

    # If it is a complex value, next!
    if len(value.split(":")) != 1:
        return None

    # If it's negative period, next!
    if value[0] == "-":
        return None

    try:
        # We parse the date
        date = pendulum.parse(value, exact = True, strict = True)

    except ParserError:
        return None

    if not isinstance(date, Date):
        return None

    # We get the shape of the string (e.g. "2012-02" = 2)
    shape = len(value.split("-"))

    # We get the unit from the shape (e.g. 2 = "month")
    unit = tuple(DateUnit)[3 - shape]

    # We build the corresponding ISOFormat object
    return ISOFormat(date.year, date.month, date.day, unit.value, 1)


def parse_period_str(value: str) -> ISOFormat | None:
    """Parse complex strings representing periods.

    Args:
        value: A string such as such as "year:2012" or "month:2015-03:12".

    Returns:
        An ISOFormat object if ``value`` is valid.
        None if ``value`` is not valid.

    Examples:
        >>> parse_period_str("year:2022")
        ISOFormat(year=2022, month=1, day=1, unit=4, size=1)

        >>> parse_period_str("month:2022-02")
        ISOFormat(year=2022, month=2, day=1, unit=2, size=1)

        >>> parse_period_str("day:2022-02-13:15")
        ISOFormat(year=2022, month=2, day=13, unit=1, size=15)

        >>> parse_period_str("2022:3")

        >>> parse_period_str("ETERNITY")

    .. versionadded:: 39.0.0

    """

    if not isinstance(value, str):
        return None

    if not value:
        return None

    # If it is not a complex value, delegate!
    if len(value.split(":")) == 1:
        return parse_instant_str(value)

    first, second, *rest = value.split(":")
    unit = DateUnit.__members__.get(first.upper())
    date = parse_instant_str(second)

    # If it is an invalid unit, next!
    if unit is None:
        return None

    # If it is an invalid date, next!
    if date is None:
        return None

    # If it has no size, we'll assume ``1``
    if not rest:
        size = 1

    else:
        size = int(rest[0])

    # We build the corresponding ISOFormat object
    return ISOFormat(date.year, date.month, date.day, unit.value, size)
