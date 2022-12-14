from __future__ import annotations

from typing import Dict, Tuple, Union

from dateutil import relativedelta
import calendar
import datetime

from ._errors import DateUnitValueError, OffsetTypeError
from ._units import DAY, MONTH, YEAR


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

        >>> instant[0]
        2021

        >>> instant[0] in instant
        True

        >>> len(instant)
        3

        >>> instant == (2021, 9, 13)
        True

        >>> instant > (2020, 9, 13)
        True

        >>> year, month, day = instant

    """

    #: A cache with the ``datetime.date`` representation of the ``Instant``.
    _dates: Dict[Instant, datetime.date] = {}

    #: A cache with the ``str`` representation of the ``Instant``.
    _strings: Dict[Instant, str] = {}

    def __repr__(self) -> str:
        return f"{Instant.__name__}({super(Instant, self).__repr__()})"

    def __str__(self) -> str:
        try:
            return Instant._strings[self]

        except KeyError:
            Instant._strings = {self: self.date.isoformat(), **Instant._strings}

        return str(self)

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

    @property
    def date(self) -> datetime.date:
        """The date representation of the ``Instant``.

        Example:
            >>> instant = Instant((2021, 10, 1))
            >>> instant.date
            datetime.date(2021, 10, 1)

        Returns:
            A datetime.time.

        """

        try:
            return Instant._dates[self]

        except KeyError:
            Instant._dates = {self: datetime.date(*self), **Instant._dates}

        return self.date

    def offset(self, offset: Union[str, int], unit: str) -> Instant:
        """Increments/decrements the given instant with offset units.

        Args:
            offset (str | int): How much of ``unit`` to offset.
            unit (str): What to offset.

        Returns:
            Instant: A new one.

        Raises:
            DateUnitValueError: When ``unit`` is not a date unit.
            OffsetTypeError: When ``offset`` is of type ``int``.

        Examples:
            >>> Instant((2020, 12, 31)).offset("first-of", "month")
            Instant((2020, 12, 1))

            >>> Instant((2020, 1, 1)).offset("last-of", "year")
            Instant((2020, 12, 31))

            >>> Instant((2020, 1, 1)).offset(1, "year")
            Instant((2021, 1, 1))

            >>> Instant((2020, 1, 1)).offset(-3, "day")
            Instant((2019, 12, 29))

        """

        year, month, day = self

        if unit not in (DAY, MONTH, YEAR):
            raise DateUnitValueError(unit)

        if offset == "first-of" and unit == YEAR:
            return Instant((year, 1, 1))

        if offset == "first-of" and unit == MONTH:
            return Instant((year, month, 1))

        if offset == "last-of" and unit == YEAR:
            return Instant((year, 12, 31))

        if offset == "last-of" and unit == MONTH:
            return Instant((year, month, calendar.monthrange(year, month)[1]))

        if not isinstance(offset, int):
            raise OffsetTypeError(offset)

        if unit == YEAR:
            date = self.date + relativedelta.relativedelta(years = offset)
            return Instant((date.year, date.month, date.day))

        if unit == MONTH:
            date = self.date + relativedelta.relativedelta(months = offset)
            return Instant((date.year, date.month, date.day))

        if unit == DAY:
            date = self.date + relativedelta.relativedelta(days = offset)
            return Instant((date.year, date.month, date.day))

        return self
