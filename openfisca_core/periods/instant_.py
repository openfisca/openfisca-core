from __future__ import annotations

import calendar
import datetime

from . import config


class Instant(tuple):
    """An instant in time (year, month, day).

    An :class:`.Instant` represents the most atomic and indivisible
    legislation's time unit.

    Current implementation considers this unit to be a day, so
    :obj:`instants <.Instant>` can be thought of as "day dates".

    Args:
        (tuple(tuple(int, int, int))):
            The ``year``, ``month``, and ``day``, accordingly.

    Examples:
        >>> instant = Instant((2021, 9, 13))

        >>> repr(Instant)
        "<class 'openfisca_core.periods.instant_.Instant'>"

        >>> repr(instant)
        'Instant((2021, 9, 13))'

        >>> str(instant)
        '2021-09-13'

        >>> dict([(instant, (2021, 9, 13))])
        {Instant((2021, 9, 13)): (2021, 9, 13)}

        >>> list(instant)
        [2021, 9, 13]

        >>> instant[0]
        2021

        >>> instant[0] in instant
        True

        >>> len(instant)
        3

        >>> instant == (2021, 9, 13)
        True

        >>> instant != (2021, 9, 13)
        False

        >>> instant > (2020, 9, 13)
        True

        >>> instant < (2020, 9, 13)
        False

        >>> instant >= (2020, 9, 13)
        True

        >>> instant <= (2020, 9, 13)
        False

        >>> instant.year
        2021

        >>> instant.month
        9

        >>> instant.day
        13

        >>> instant.date
        datetime.date(2021, 9, 13)

        >>> year, month, day = instant

    """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __str__(self) -> str:
        instant_str = config.str_by_instant_cache.get(self)
        if instant_str is None:
            config.str_by_instant_cache[self] = instant_str = self.date.isoformat()
        return instant_str

    @property
    def date(self) -> datetime.date:
        instant_date = config.date_by_instant_cache.get(self)
        if instant_date is None:
            config.date_by_instant_cache[self] = instant_date = datetime.date(*self)
        return instant_date

    @property
    def day(self) -> int:
        return self[2]

    @property
    def month(self) -> int:
        return self[1]

    def offset(self, offset: int | str, unit: str) -> Instant:
        """Increments/decrements the given instant with offset units.

        Args:
            offset: How much of ``unit`` to offset.
            unit: What to offset

        Returns:
            :obj:`.Instant`: A new :obj:`.Instant` in time.

        Raises:
            :exc:`AssertionError`: When ``unit`` is not a date unit.
            :exc:`AssertionError`: When ``offset`` is not either ``first-of``,
            ``last-of``, or any :obj:`int`.

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
        assert unit in (
            config.DAY,
            config.MONTH,
            config.YEAR,
        ), "Invalid unit: {} of type {}".format(unit, type(unit))
        if offset == "first-of":
            if unit == config.MONTH:
                day = 1
            elif unit == config.YEAR:
                month = 1
                day = 1
        elif offset == "last-of":
            if unit == config.MONTH:
                day = calendar.monthrange(year, month)[1]
            elif unit == config.YEAR:
                month = 12
                day = 31
        else:
            assert isinstance(offset, int), "Invalid offset: {} of type {}".format(
                offset, type(offset)
            )
            if unit == config.DAY:
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
            elif unit == config.MONTH:
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
            elif unit == config.YEAR:
                year += offset
                # Handle february month of leap year.
                month_last_day = calendar.monthrange(year, month)[1]
                if day > month_last_day:
                    day = month_last_day

        return self.__class__((year, month, day))

    @property
    def year(self) -> int:
        return self[0]
