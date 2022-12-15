from __future__ import annotations

import pendulum
from pendulum import Date
from pendulum.exceptions import ParserError

from .._config import UNIT_MAPPING
from ..domain._instant import Instant
from ..domain._period import Period


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
