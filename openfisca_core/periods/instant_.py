from __future__ import annotations

from typing import Any, Tuple

import calendar
import datetime
import functools

import inflect
import pendulum
from pendulum.datetime import Date

from ._config import INSTANT_PATTERN
from ._errors import (
    DateUnitValueError,
    InstantFormatError,
    InstantTypeError,
    InstantValueError,
    OffsetTypeError,
    )
from ._parsers import ISOFormat
from ._date_unit import DateUnit
from .typing import Add, Plural

DAY, MONTH, YEAR, _ = tuple(DateUnit)


class Instant(Tuple[int, int, int]):
    """An instant in time (``year``, ``month``, ``day``).

    An ``Instant`` represents the most atomic and indivisible
    legislation's date unit.

    Current implementation considers this unit to be a day, so
    ``instants`` can be thought of as "day dates".

    Args:
        (tuple(int, int, int)):
            The ``year``, ``month``, and ``day``, accordingly.

    Examples:
        >>> instant = Instant((2021, 9, 13))

        ``Instants`` are represented as a ``tuple`` containing the date units:

        >>> repr(instant)
        'Instant((2021, 9, 13))'

        However, their user-friendly representation is as a date in the
        ISO format:

        >>> str(instant)
        '2021-09-13'

        Because ``Instants`` are ``tuples``, they are immutable, which allows
        us to use them as keys in hashmaps:

        >>> dict([(instant, (2021, 9, 13))])
        {Instant((2021, 9, 13)): (2021, 9, 13)}

        All the rest of the ``tuple`` protocols are inherited as well:

        >>> instant.year
        2021

        >>> instant.year in instant
        True

        >>> len(instant)
        3

        >>> instant == (2021, 9, 13)
        True

        >>> instant > (2020, 9, 13)
        True

        >>> year, month, day = instant

    """

    plural: Plural = inflect.engine().plural

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"({super(type(self), self).__repr__()})"
            )

    @functools.lru_cache(maxsize = None)
    def __str__(self) -> str:
        return self.date().isoformat()

    @property
    def year(self) -> int:
        """The ``year`` of the ``Instant``.

        Example:
            >>> instant = Instant((2021, 10, 1))
            >>> instant.year
            2021

        Returns:
            An int.

        """

        return self[0]

    @property
    def month(self) -> int:
        """The ``month`` of the ``Instant``.

        Example:
            >>> instant = Instant((2021, 10, 1))
            >>> instant.month
            10

        Returns:
            An int.

        """

        return self[1]

    @property
    def day(self) -> int:
        """The ``day`` of the ``Instant``.

        Example:
            >>> instant = Instant((2021, 10, 1))
            >>> instant.day
            1

        Returns:
            An int.

        """

        return self[2]

    @functools.lru_cache(maxsize = None)
    def date(self) -> Date:
        """The date representation of the ``Instant``.

        Example:
            >>> instant = Instant((2021, 10, 1))
            >>> instant.date()
            Date(2021, 10, 1)

        Returns:
            A date.

        """

        return pendulum.date(*self)

    def offset(self, offset: str | int, unit: int) -> Instant:
        """Increments/decrements the given instant with offset units.

        Args:
            offset (str | int): How much of ``unit`` to offset.
            unit (int): What to offset.

        Returns:
            Instant: A new one.

        Raises:
            DateUnitValueError: When ``unit`` is not a date unit.
            OffsetTypeError: When ``offset`` is of type ``int``.

        Examples:
            >>> Instant((2020, 12, 31)).offset("first-of", MONTH)
            Instant((2020, 12, 1))

            >>> Instant((2020, 1, 1)).offset("last-of", YEAR)
            Instant((2020, 12, 31))

            >>> Instant((2020, 1, 1)).offset(1, YEAR)
            Instant((2021, 1, 1))

            >>> Instant((2020, 1, 1)).offset(-3, DAY)
            Instant((2019, 12, 29))

        """

        year, month, day = self

        if not unit & DateUnit.isoformat:
            raise DateUnitValueError(unit)

        if offset in {"first-of", "last-of"} and unit == DAY:
            return self

        if offset == "first-of" and unit == MONTH:
            return type(self)((year, month, 1))

        if offset == "first-of" and unit == YEAR:
            return type(self)((year, 1, 1))

        if offset == "last-of" and unit == MONTH:
            day = calendar.monthrange(year, month)[1]
            return type(self)((year, month, day))

        if offset == "last-of" and unit == YEAR:
            return type(self)((year, 12, 31))

        if not isinstance(offset, int):
            raise OffsetTypeError(offset)

        add: Add = self.date().add

        date = add(**{type(self).plural(str(unit)): offset})

        return type(self)((date.year, date.month, date.day))

    @classmethod
    def build(cls, value: Any) -> Instant:
        """Build a new instant, aka a triple of integers (year, month, day).

        Args:
            value (Any): An ``instant-like`` object.

        Returns:
            An Instant.

        Raises:
            InstantFormatError: When ``value`` is invalid, like "2021-32-13".
            InstantValueError: When the length of ``value`` is out of range.
            InstantTypeError: When ``value`` is None.

        Examples:
            >>> from openfisca_core import periods

            >>> Instant.build(datetime.date(2021, 9, 16))
            Instant((2021, 9, 16))

            >>> Instant.build(Instant((2021, 9, 16)))
            Instant((2021, 9, 16))

            >>> Instant.build("2021")
            Instant((2021, 1, 1))

            >>> Instant.build(2021)
            Instant((2021, 1, 1))

            >>> Instant.build((2021, 9))
            Instant((2021, 9, 1))

            >>> start = Instant((2021, 9, 16))
            >>> period = periods.period((YEAR, start, 1))

            >>> Instant.build(period)
            Traceback (most recent call last):
            TypeError: int() argument must be a string, a bytes-like object ...

            .. versionadded:: 39.0.0

        """

        instant: Tuple[int, ...] | ISOFormat | None

        if value is None or isinstance(value, DateUnit):
            raise InstantTypeError(value)

        if isinstance(value, Instant):
            return value

        if isinstance(value, str) and not INSTANT_PATTERN.match(value):
            raise InstantFormatError(value)

        if isinstance(value, str) and len(value.split("-")) > 3:
            raise InstantValueError(value)

        if isinstance(value, str):
            instant = ISOFormat.parse(value)

        elif isinstance(value, datetime.date):
            instant = value.year, value.month, value.day

        elif isinstance(value, int):
            instant = value, 1, 1

        elif isinstance(value, (dict, set)):
            raise InstantValueError(value)

        elif isinstance(value, (tuple, list)) and not 1 <= len(value) <= 3:
            raise InstantValueError(value)

        else:
            instant = tuple(int(value) for value in tuple(value))

        if instant is None:
            raise InstantFormatError(value)

        if len(instant) == 1:
            return cls((instant[0], 1, 1))

        if len(instant) == 2:
            return cls((instant[0], instant[1], 1))

        if len(instant) == 5:
            return cls(instant[1:-1])

        return cls(instant)
