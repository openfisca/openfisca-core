from __future__ import annotations

from typing import Callable, NamedTuple

import calendar
import functools

import pendulum
from pendulum.datetime import Date

from ._dates import DateUnit
from ._errors import DateUnitValueError, OffsetTypeError

DAY, MONTH, YEAR, _ = tuple(DateUnit)


class Instant(NamedTuple):
    """An instant in time (``year``, ``month``, ``day``).

    An ``Instant`` represents the most atomic and indivisible
    legislation's date unit.

    Current implementation considers this unit to be a day, so
    ``instants`` can be thought of as "day dates".

    Examples:
        >>> instant = Instant(2021, 9, 13)

        ``Instants`` are represented as a ``tuple`` containing the date units:

        >>> repr(instant)
        'Instant(year=2021, month=9, day=13)'

        However, their user-friendly representation is as a date in the
        ISO format:

        >>> str(instant)
        '2021-09-13'

        Because ``Instants`` are ``tuples``, they are immutable, which allows
        us to use them as keys in hashmaps:

        >>> {instant: (2021, 9, 13)}
        {Instant(year=2021, month=9, day=13): (2021, 9, 13)}

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

    #: The year.
    year: int

    #: The month.
    month: int

    #: The day.
    day: int

    @functools.lru_cache(maxsize = None)
    def __str__(self) -> str:
        return self.date().isoformat()

    @functools.lru_cache(maxsize = None)
    def date(self) -> Date:
        """The date representation of the ``Instant``.

        Example:
            >>> instant = Instant(2021, 10, 1)
            >>> instant.date()
            Date(2021, 10, 1)

        Returns:
            A date.

        """

        return pendulum.date(*self)

    def add(self, unit: str, count: int) -> Date:
        """Add ``count`` ``unit``s to a ``date``.

        Args:
            unit: The unit to add.
            count: The number of units to add.

        Returns:
            A new Date.

        Examples:
            >>> instant = Instant(2021, 10, 1)
            >>> instant.add("months", 6)
            Date(2022, 4, 1)

        .. versionadded:: 39.0.0

        """

        fun: Callable[..., Date] = self.date().add

        new: Date = fun(**{unit: count})

        return new

    def offset(self, offset: str | int, unit: DateUnit) -> Instant:
        """Increments/decrements the given instant with offset units.

        Args:
            offset: How much of ``unit`` to offset.
            unit: What to offset.

        Returns:
            A new Instant.

        Raises:
            DateUnitValueError: When ``unit`` is not a date unit.
            OffsetTypeError: When ``offset`` is of type ``int``.

        Examples:
            >>> Instant(2020, 12, 31).offset("first-of", MONTH)
            Instant(year=2020, month=12, day=1)

            >>> Instant(2020, 1, 1).offset("last-of", YEAR)
            Instant(year=2020, month=12, day=31)

            >>> Instant(2020, 1, 1).offset(1, YEAR)
            Instant(year=2021, month=1, day=1)

            >>> Instant(2020, 1, 1).offset(-3, DAY)
            Instant(year=2019, month=12, day=29)

        """

        year, month, day = self

        if not isinstance(unit, DateUnit):
            raise DateUnitValueError(unit)

        if not unit & DateUnit.isoformat:
            raise DateUnitValueError(unit)

        if offset in {"first-of", "last-of"} and unit == DAY:
            return self

        if offset == "first-of" and unit == MONTH:
            return type(self)(year, month, 1)

        if offset == "first-of" and unit == YEAR:
            return type(self)(year, 1, 1)

        if offset == "last-of" and unit == MONTH:
            day = calendar.monthrange(year, month)[1]
            return type(self)(year, month, day)

        if offset == "last-of" and unit == YEAR:
            return type(self)(year, 12, 31)

        if not isinstance(offset, int):
            raise OffsetTypeError(offset)

        date = self.add(unit.plural, offset)

        return type(self)(date.year, date.month, date.day)
