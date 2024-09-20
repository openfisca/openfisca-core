from typing import Optional

import re

import pendulum

from . import types as t
from ._errors import ParserError
from .date_unit import DateUnit
from .instant_ import Instant
from .period_ import Period

invalid_week = re.compile(r".*(W[1-9]|W[1-9]-[0-9]|W[0-5][0-9]-0)$")


def _parse_period(value: str) -> Optional[t.Period]:
    """Parses ISO format/calendar periods.

    Such as "2012" or "2015-03".

    Examples:
        >>> _parse_period("2022")
        Period((<DateUnit.YEAR: 'year'>, Instant((2022, 1, 1)), 1))

        >>> _parse_period("2022-02")
        Period((<DateUnit.MONTH: 'month'>, Instant((2022, 2, 1)), 1))

        >>> _parse_period("2022-W02-7")
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

    unit = _parse_unit(value)
    date = pendulum.parse(value, exact=True)

    if not isinstance(date, pendulum.Date):
        raise ValueError

    instant = Instant((date.year, date.month, date.day))

    return Period((unit, instant, 1))


def _parse_unit(value: str) -> t.DateUnit:
    """Determine the date unit of a date string.

    Args:
        value (str): The date string to parse.

    Returns:
        A DateUnit.

    Raises:
        ValueError when no DateUnit can be determined.

    Examples:
        >>> _parse_unit("2022")
        <DateUnit.YEAR: 'year'>

        >>> _parse_unit("2022-W03-01")
        <DateUnit.WEEKDAY: 'weekday'>

    """
    length = len(value.split("-"))
    isweek = value.find("W") != -1

    if length == 1:
        return DateUnit.YEAR

    if length == 2:
        if isweek:
            return DateUnit.WEEK

        return DateUnit.MONTH

    if length == 3:
        if isweek:
            return DateUnit.WEEKDAY

        return DateUnit.DAY

    else:
        raise ValueError


__all__ = ["_parse_period", "_parse_unit"]
