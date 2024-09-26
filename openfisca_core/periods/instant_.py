from __future__ import annotations

import pendulum

from . import config, types as t
from .date_unit import DateUnit


class Instant(tuple[int, int, int]):
    """An instant in time (year, month, day).

    An :class:`.Instant` represents the most atomic and indivisible
    legislation's date unit.

    Current implementation considers this unit to be a day, so
    :obj:`instants <.Instant>` can be thought of as "day dates".

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
        Date(2021, 9, 13)

        >>> year, month, day = instant

    """

    __slots__ = ()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __str__(self) -> t.InstantStr:
        instant_str = config.str_by_instant_cache.get(self)

        if instant_str is None:
            instant_str = t.InstantStr(self.date.isoformat())
            config.str_by_instant_cache[self] = instant_str

        return instant_str

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Instant):
            return super().__lt__(other)
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if isinstance(other, Instant):
            return super().__le__(other)
        return NotImplemented

    @property
    def date(self) -> pendulum.Date:
        instant_date = config.date_by_instant_cache.get(self)

        if instant_date is None:
            instant_date = pendulum.date(*self)
            config.date_by_instant_cache[self] = instant_date

        return instant_date

    @property
    def day(self) -> int:
        return self[2]

    @property
    def month(self) -> int:
        return self[1]

    @property
    def year(self) -> int:
        return self[0]

    @property
    def is_eternal(self) -> bool:
        return self == self.eternity()

    def offset(self, offset: str | int, unit: t.DateUnit) -> t.Instant | None:
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
            >>> Instant((2020, 12, 31)).offset("first-of", DateUnit.MONTH)
            Instant((2020, 12, 1))

            >>> Instant((2020, 1, 1)).offset("last-of", DateUnit.YEAR)
            Instant((2020, 12, 31))

            >>> Instant((2020, 1, 1)).offset(1, DateUnit.YEAR)
            Instant((2021, 1, 1))

            >>> Instant((2020, 1, 1)).offset(-3, DateUnit.DAY)
            Instant((2019, 12, 29))

        """
        year, month, _ = self

        assert unit in (
            DateUnit.isoformat + DateUnit.isocalendar
        ), f"Invalid unit: {unit} of type {type(unit)}"

        if offset == "first-of":
            if unit == DateUnit.YEAR:
                return self.__class__((year, 1, 1))

            if unit == DateUnit.MONTH:
                return self.__class__((year, month, 1))

            if unit == DateUnit.WEEK:
                date = self.date
                date = date.start_of("week")
                return self.__class__((date.year, date.month, date.day))
            return None

        if offset == "last-of":
            if unit == DateUnit.YEAR:
                return self.__class__((year, 12, 31))

            if unit == DateUnit.MONTH:
                date = self.date
                date = date.end_of("month")
                return self.__class__((date.year, date.month, date.day))

            if unit == DateUnit.WEEK:
                date = self.date
                date = date.end_of("week")
                return self.__class__((date.year, date.month, date.day))
            return None

        assert isinstance(
            offset,
            int,
        ), f"Invalid offset: {offset} of type {type(offset)}"

        if unit == DateUnit.YEAR:
            date = self.date
            date = date.add(years=offset)
            return self.__class__((date.year, date.month, date.day))

        if unit == DateUnit.MONTH:
            date = self.date
            date = date.add(months=offset)
            return self.__class__((date.year, date.month, date.day))

        if unit == DateUnit.WEEK:
            date = self.date
            date = date.add(weeks=offset)
            return self.__class__((date.year, date.month, date.day))

        if unit in (DateUnit.DAY, DateUnit.WEEKDAY):
            date = self.date
            date = date.add(days=offset)
            return self.__class__((date.year, date.month, date.day))
        return None

    @classmethod
    def eternity(cls) -> t.Instant:
        """Return an eternity instant."""
        return cls((-1, -1, -1))


__all__ = ["Instant"]
