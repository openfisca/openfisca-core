from __future__ import annotations

from typing import Sequence

import pendulum
from pendulum.datetime import Date
from pendulum.parsing import ParserError

from ._iso_format import ISOFormat


def fromint(value: int) -> ISOFormat | None:
    """Parse an int respecting the ISO format.

    Args:
        value: The integer to parse.

    Returns:
        An ISOFormat object if ``value`` is valid.
        None otherwise.

    Examples:
        >>> fromint(1)
        ISOFormat(year=1, month=1, day=1, unit=4, shape=1)

        >>> fromint(2023)
        ISOFormat(year=2023, month=1, day=1, unit=4, shape=1)

        >>> fromint(-1)

        >>> fromint("2023")

        >>> fromint(20231231)

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


def fromstr(value: str) -> ISOFormat | None:
    """Parse strings respecting the ISO format.

    Args:
        value: A string such as such as "2012" or "2015-03".

    Returns:
        An ISOFormat object if ``value`` is valid.
        None if ``value`` is not valid.

    Examples:
        >>> fromstr("2022")
        ISOFormat(year=2022, month=1, day=1, unit=4, shape=1)

        >>> fromstr("2022-02")
        ISOFormat(year=2022, month=2, day=1, unit=2, shape=2)

        >>> fromstr("2022-02-13")
        ISOFormat(year=2022, month=2, day=13, unit=1, shape=3)

        >>> fromstr(1000)

        >>> fromstr("ETERNITY")

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
    unit = pow(2, 3 - shape)

    # We build the corresponding ISOFormat object
    return ISOFormat(date.year, date.month, date.day, unit, shape)


def fromseq(value: Sequence[int]) -> ISOFormat | None:
    """Parse a sequence of ints respecting the ISO format.

    Args:
        value: A sequence of ints such as [2012, 3, 13].

    Returns:
        An ISOFormat object if ``value`` is valid.
        None if ``value`` is not valid.

    Examples:
        >>> fromseq([2022])
        ISOFormat(year=2022, month=1, day=1, unit=4, shape=1)

        >>> fromseq([2022, 1])
        ISOFormat(year=2022, month=1, day=1, unit=2, shape=2)

        >>> fromseq([2022, 1, 1])
        ISOFormat(year=2022, month=1, day=1, unit=1, shape=3)

        >>> fromseq([-2022, 1, 1])

        >>> fromseq([2022, 13, 1])

        >>> fromseq([2022, 1, 32])

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
    unit = pow(2, 3 - shape)

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
    return ISOFormat(date.year, date.month, date.day, unit, shape)
