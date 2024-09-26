"""To parse periods and instants from strings."""

from __future__ import annotations

import datetime

import pendulum

from . import types as t
from ._errors import InstantError, ParserError, PeriodError
from .date_unit import DateUnit
from .instant_ import Instant
from .period_ import Period


def parse_instant(value: str) -> t.Instant:
    """Parse a string into an instant.

    Args:
        value (str): The string to parse.

    Returns:
        An InstantStr.

    Raises:
        InstantError: When the string is not a valid ISO Calendar/Format.
        ParserError: When the string couldn't be parsed.

    Examples:
        >>> parse_instant("2022")
        Instant((2022, 1, 1))

        >>> parse_instant("2022-02")
        Instant((2022, 2, 1))

        >>> parse_instant("2022-W02-7")
        Instant((2022, 1, 16))

        >>> parse_instant("2022-W013")
        Traceback (most recent call last):
        openfisca_core.periods._errors.InstantError: '2022-W013' is not a va...

        >>> parse_instant("2022-02-29")
        Traceback (most recent call last):
        pendulum.parsing.exceptions.ParserError: Unable to parse string [202...

    """

    if not isinstance(value, t.InstantStr):
        raise InstantError(str(value))

    date = pendulum.parse(value, exact=True)

    if not isinstance(date, datetime.date):
        msg = f"Unable to parse string [{value}]"
        raise ParserError(msg)

    return Instant((date.year, date.month, date.day))


def parse_period(value: str) -> t.Period:
    """Parses ISO format/calendar periods.

    Such as "2012" or "2015-03".

    Examples:
        >>> parse_period("2022")
        Period((<DateUnit.YEAR: 'year'>, Instant((2022, 1, 1)), 1))

        >>> parse_period("2022-02")
        Period((<DateUnit.MONTH: 'month'>, Instant((2022, 2, 1)), 1))

        >>> parse_period("2022-W02-7")
        Period((<DateUnit.WEEKDAY: 'weekday'>, Instant((2022, 1, 16)), 1))

    """

    try:
        instant = parse_instant(value)

    except InstantError as error:
        raise PeriodError(value) from error

    unit = parse_unit(value)

    return Period((unit, instant, 1))


def parse_unit(value: str) -> t.DateUnit:
    """Determine the date unit of a date string.

    Args:
        value (str): The date string to parse.

    Returns:
        A DateUnit.

    Raises:
        InstantError: when no DateUnit can be determined.

    Examples:
        >>> parse_unit("2022")
        <DateUnit.YEAR: 'year'>

        >>> parse_unit("2022-W03-1")
        <DateUnit.WEEKDAY: 'weekday'>

    """

    if not isinstance(value, t.InstantStr):
        raise InstantError(str(value))

    length = len(value.split("-"))

    if isinstance(value, t.ISOCalendarStr):
        return DateUnit.isocalendar[-length]

    return DateUnit.isoformat[-length]


__all__ = ["parse_instant", "parse_period", "parse_unit"]
