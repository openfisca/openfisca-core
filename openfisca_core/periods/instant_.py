from __future__ import annotations

from typing import Any, Dict, Optional, Union

import calendar
import datetime

from openfisca_core import types

from . import _config, _funcs


class Instant(tuple):
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
    dates: Dict[Instant, datetime.date] = {}

    #: A cache with the ``str`` representation of the ``Instant``.
    strings: Dict[Instant, str] = {}

    def __repr__(self) -> str:
        return f"{Instant.__name__}({super(Instant, self).__repr__()})"

    def __str__(self) -> str:
        string = Instant.strings.get(self)

        if string is None:
            Instant.strings[self] = self.date.isoformat()

        return Instant.strings[self]

    @staticmethod
    def to_date(value: Any) -> Optional[datetime.date]:
        """Returns the date representation of an ``Instant``.

        Args:
            value (:any:):
                An ``instant-like`` object to get the date from.

        Returns:
            None: When ``value`` is None.
            datetime.date: Otherwise.

        Examples:
            >>> Instant.to_date(Instant((2021, 1, 1)))
            datetime.date(2021, 1, 1)

        """

        instant = _funcs.build_instant(value)

        if instant is None:
            return None

        return instant.date

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

        date = Instant.dates.get(self)

        if date is None:
            Instant.dates[self] = datetime.date(*self)

        return Instant.dates[self]

    def offset(self, offset: Union[str, int], unit: str) -> types.Instant:
        """Increments/decrements the given instant with offset units.

        Args:
            offset (str | int): How much of ``unit`` to offset.
            unit (str): What to offset.

        Returns:
            Instant: A new one.

        Raises:
            AssertionError: When ``unit`` is not a date unit.
            AssertionError: When ``offset`` is not either ``first-of``,
                ``last-of``, or any ``int``.

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

        assert unit in (_config.DAY, _config.MONTH, _config.YEAR), 'Invalid unit: {} of type {}'.format(unit, type(unit))

        if offset == 'first-of':
            if unit == _config.MONTH:
                day = 1

            elif unit == _config.YEAR:
                month = 1
                day = 1

        elif offset == 'last-of':
            if unit == _config.MONTH:
                day = calendar.monthrange(year, month)[1]

            elif unit == _config.YEAR:
                month = 12
                day = 31

        else:
            assert isinstance(offset, int), 'Invalid offset: {} of type {}'.format(offset, type(offset))

            if unit == _config.DAY:
                day += offset

                if offset < 0:
                    while day < 1:
                        month -= 1

                        if month == 0:
                            year -= 1
                            month = 12

                        day += calendar.monthrange(year, month)[1]

                elif offset > 0:
                    month_last_day = calendar.monthrange(year, month)[1]

                    while day > month_last_day:
                        month += 1

                        if month == 13:
                            year += 1
                            month = 1

                        day -= month_last_day
                        month_last_day = calendar.monthrange(year, month)[1]

            elif unit == _config.MONTH:
                month += offset

                if offset < 0:
                    while month < 1:
                        year -= 1
                        month += 12

                elif offset > 0:
                    while month > 12:
                        year += 1
                        month -= 12
                month_last_day = calendar.monthrange(year, month)[1]

                if day > month_last_day:
                    day = month_last_day

            elif unit == _config.YEAR:
                year += offset

                # Handle february month of leap year.
                month_last_day = calendar.monthrange(year, month)[1]

                if day > month_last_day:
                    day = month_last_day

        return Instant((year, month, day))
