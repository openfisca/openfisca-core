from __future__ import annotations

import re

import pendulum

from . import types as t
from ._errors import ParserError
from .date_unit import DateUnit
from .instant_ import Instant
from .period_ import Period

invalid_week = re.compile(r".*(W[1-9]|W[1-9]-[0-9]|W[0-5][0-9]-0)$")


def parse_period(value: str) -> None | t.Period:
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

    # If it's a complex period, next!
    if len(value.split(":")) != 1:
        return None

    # Check for a non-empty string.
    if len(value) == 0:
        raise AttributeError

    # If it's negative, next!
    if value[0] == "-":
        raise ValueError

    # If it's an invalid week, next!
    if invalid_week.match(value):
        raise ParserError

    unit = parse_unit(value)
    date = pendulum.parse(value, exact=True)

    if not isinstance(date, pendulum.Date):
        raise TypeError

    instant = Instant((date.year, date.month, date.day))

    return Period((unit, instant, 1))


def parse_unit(value: str) -> t.DateUnit:
    """Determine the date unit of a date string.

    Args:
        value (str): The date string to parse.

    Returns:
        A DateUnit.

    Raises:
        ValueError when no DateUnit can be determined.

    Examples:
        >>> parse_unit("2022")
        <DateUnit.YEAR: 'year'>

        >>> parse_unit("2022-W03-01")
        <DateUnit.WEEKDAY: 'weekday'>

    """

    format_y, format_ym, format_ymd = 1, 2, 3
    length = len(value.split("-"))
    isweek = value.find("W") != -1

    if length == format_y:
        return DateUnit.YEAR

    if length == format_ym:
        if isweek:
            return DateUnit.WEEK

        return DateUnit.MONTH

    if length == format_ymd:
        if isweek:
            return DateUnit.WEEKDAY

        return DateUnit.DAY

    raise ValueError


__all__ = ["parse_period", "parse_unit"]
