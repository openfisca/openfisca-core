from __future__ import annotations

from typing import Any

import datetime

import pendulum
from pendulum.datetime import Date
from pendulum.parsing import ParserError

from ._config import INSTANT_PATTERN
from ._errors import InstantFormatError, InstantValueError, PeriodFormatError
from ._units import DAY, ETERNITY, MONTH, UNIT_WEIGHTS, YEAR
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
        >>> build_period(Period(("year", Instant((2021, 1, 1)), 1)))
        Period(('year', Instant((2021, 1, 1)), 1))

        >>> build_period(Instant((2021, 1, 1)))
        Period(('day', Instant((2021, 1, 1)), 1))

        >>> build_period("eternity")
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
        return Period((DAY, value, 1))

    if value == "ETERNITY" or value == ETERNITY:
        return Period(("eternity", Instant.build(datetime.date.min), 1))

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

    components = value.split(":")

    # Left-most component must be a valid unit
    unit = components[0]

    if unit not in (DAY, MONTH, YEAR):
        raise PeriodFormatError(value)

    # Middle component must be a valid iso period
    base_period = parse_period(components[1])

    if not base_period:
        raise PeriodFormatError(value)

    # Periods like year:2015-03 have a size of 1
    if len(components) == 2:
        size = 1

    # If provided, make sure the size is an integer
    elif len(components) == 3:
        try:
            size = int(components[2])

        except ValueError:
            raise PeriodFormatError(value)

    # If there are more than 2 ":" in the string, the period is invalid
    else:
        raise PeriodFormatError(value)

    # Reject ambiguous periods such as month:2014
    if UNIT_WEIGHTS[base_period.unit] > UNIT_WEIGHTS[unit]:
        raise PeriodFormatError(value)

    return Period((unit, base_period.start, size))


def key_period_size(period: Period) -> str:
    """Define a key in order to sort periods by length.

    It uses two aspects: first, ``unit``, then, ``size``.

    Args:
        period: An :mod:`.openfisca_core` :obj:`.Period`.

    Returns:
        :obj:`str`: A string.

    Examples:
        >>> instant = Instant((2021, 9, 14))

        >>> period = Period(("day", instant, 1))
        >>> key_period_size(period)
        '100_1'

        >>> period = Period(("year", instant, 3))
        >>> key_period_size(period)
        '300_3'

    """

    unit, _start, size = period

    return f"{UNIT_WEIGHTS[unit]}_{size}"


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
        Period(('year', Instant((2022, 1, 1)), 1))

        >>> parse_period("2022-02")
        Period(('month', Instant((2022, 2, 1)), 1))

        >>> parse_period("2022-02-13")
        Period(('day', Instant((2022, 2, 13)), 1))

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

    unit = UNIT_MAPPING[len(value.split("-"))]
    start = Instant((date.year, date.month, date.day))
    return Period((unit, start, 1))
