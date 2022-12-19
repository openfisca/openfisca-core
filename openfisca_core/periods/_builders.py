from __future__ import annotations

from typing import Any

import datetime

from ._date_unit import DateUnit
from ._exceptions import (
    InstantFormatError,
    InstantTypeError,
    PeriodFormatError,
    PeriodTypeError,
    )
from ._instant import Instant
from ._iso_format import ISOFormat
from ._parsers import fromcomplex, fromint, fromseq, fromstr
from ._period import Period

day, _month, year, eternity = tuple(DateUnit)


def instant(value: Any) -> Instant:
    """Build a new instant, aka a triple of integers (year, month, day).

    Args:
        value: An ``instant-like`` object.

    Returns:
        An Instant.

    Raises:
        InstantFormatError: When ``value`` is invalid, like "2021-32-13".
        InstantTypeError: When ``value`` is None.

    Examples:
        >>> instant(datetime.date(2021, 9, 16))
        Instant((2021, 9, 16))

        >>> instant(Instant((2021, 9, 16)))
        Instant((2021, 9, 16))

        >>> instant("2021")
        Instant((2021, 1, 1))

        >>> instant(2021)
        Instant((2021, 1, 1))

        >>> instant((2021, 9))
        Instant((2021, 9, 1))

        >>> start = Instant((2021, 9, 16))

        >>> instant(Period((year, start, 1)))
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
        isoformat = fromint(value)

    elif isinstance(value, str):
        isoformat = fromstr(value)

    elif isinstance(value, (list, tuple)):
        isoformat = fromseq(value)

    else:
        raise InstantTypeError(value)

    if isoformat is None:
        raise InstantFormatError(value)

    return Instant((isoformat.year, isoformat.month, isoformat.day))


def period(value: Any) -> Period:
    """Build a new period, aka a triple (unit, start_instant, size).

    Args:
        value: A ``period-like`` object.

    Returns:
        A period.

    Raises:
        PeriodFormatError: When arguments are invalid, like "2021-32-13".
        PeriodTypeError: When ``value`` is not a ``period-like`` object.

    Examples:
        >>> period(Period((year, Instant((2021, 1, 1)), 1)))
        Period((year, Instant((2021, 1, 1)), 1))

        >>> period(Instant((2021, 1, 1)))
        Period((day, Instant((2021, 1, 1)), 1))

        >>> period(eternity)
        Period((eternity, Instant((1, 1, 1)), 1))

        >>> period(2021)
        Period((year, Instant((2021, 1, 1)), 1))

        >>> period("2014")
        Period((year, Instant((2014, 1, 1)), 1))

        >>> period("year:2014")
        Period((year, Instant((2014, 1, 1)), 1))

        >>> period("month:2014-02")
        Period((month, Instant((2014, 2, 1)), 1))

        >>> period("year:2014-02")
        Period((year, Instant((2014, 2, 1)), 1))

        >>> period("day:2014-02-02")
        Period((day, Instant((2014, 2, 2)), 1))

        >>> period("day:2014-02-02:3")
        Period((day, Instant((2014, 2, 2)), 3))

    """

    if value in {eternity, eternity.name, eternity.name.lower()}:
        return Period((eternity, instant(datetime.date.min), 1))

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
    isoformat = fromcomplex(value)

    if isoformat is None:
        raise PeriodFormatError(value)

    unit = DateUnit(isoformat.unit)

    return Period((unit, instant(isoformat[:3]), isoformat.size))
