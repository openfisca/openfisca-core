import pendulum

from . import config
from .date_unit import DateUnit


class Instant(tuple):
    """An instant in time (year, month, day).

    An :class:`.Instant` represents the most atomic and indivisible
    legislation's date unit.

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
        Date(2021, 9, 13)

        >>> year, month, day = instant

    """

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __str__(self):
        instant_str = config.str_by_instant_cache.get(self)

        if instant_str is None:
            config.str_by_instant_cache[self] = instant_str = self.date.isoformat()

        return instant_str

    @property
    def date(self):
        instant_date = config.date_by_instant_cache.get(self)

        if instant_date is None:
            config.date_by_instant_cache[self] = instant_date = pendulum.date(*self)

        return instant_date

    @property
    def day(self):
        return self[2]

    @property
    def month(self):
        return self[1]

    def offset(self, offset, unit):
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

        year, month, day = self

        assert unit in (
            DateUnit.isoformat + DateUnit.isocalendar
        ), f"Invalid unit: {unit} of type {type(unit)}"

        if offset == "first-of":
            if unit == DateUnit.YEAR:
                return self.__class__((year, 1, 1))

            elif unit == DateUnit.MONTH:
                return self.__class__((year, month, 1))

            elif unit == DateUnit.WEEK:
                date = self.date
                date = date.start_of("week")
                return self.__class__((date.year, date.month, date.day))

        elif offset == "last-of":
            if unit == DateUnit.YEAR:
                return self.__class__((year, 12, 31))

            elif unit == DateUnit.MONTH:
                date = self.date
                date = date.end_of("month")
                return self.__class__((date.year, date.month, date.day))

            elif unit == DateUnit.WEEK:
                date = self.date
                date = date.end_of("week")
                return self.__class__((date.year, date.month, date.day))

        else:
            assert isinstance(
                offset, int
            ), f"Invalid offset: {offset} of type {type(offset)}"

            if unit == DateUnit.YEAR:
                date = self.date
                date = date.add(years=offset)
                return self.__class__((date.year, date.month, date.day))

            elif unit == DateUnit.MONTH:
                date = self.date
                date = date.add(months=offset)
                return self.__class__((date.year, date.month, date.day))

            elif unit == DateUnit.WEEK:
                date = self.date
                date = date.add(weeks=offset)
                return self.__class__((date.year, date.month, date.day))

            elif unit in (DateUnit.DAY, DateUnit.WEEKDAY):
                date = self.date
                date = date.add(days=offset)
                return self.__class__((date.year, date.month, date.day))

    @property
    def year(self):
        return self[0]
