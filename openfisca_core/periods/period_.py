from __future__ import annotations

from typing import Optional, Sequence, Tuple, Union

import calendar
import datetime

from ._errors import DateUnitValueError
from ._units import DAY, ETERNITY, MONTH, UNIT_WEIGHTS, YEAR
from .instant_ import Instant


class Period(Tuple[str, Instant, int]):
    """Toolbox to handle date intervals.

    A ``Period`` is a triple (``unit``, ``start``, ``size``).

    Attributes:
        unit (str):
            Either ``year``, ``month``, ``day`` or ``eternity``.
        start (:obj:`.Instant`):
            The "instant" the :obj:`.Period` starts at.
        size (int):
            The amount of ``unit``, starting at ``start``, at least ``1``.

    Args:
        tuple(str, .Instant, int))):
            The ``unit``, ``start``, and ``size``, accordingly.

    Examples:
        >>> instant = Instant((2021, 9, 1))
        >>> period = Period((YEAR, instant, 3))

        ``Periods`` are represented as a ``tuple`` containing the ``unit``,
        an ``Instant`` and the ``size``:

        >>> repr(period)
        "Period(('year', Instant((2021, 9, 1)), 3))"

        Their user-friendly representation is as a date in the
        ISO format, prefixed with the ``unit`` and suffixed with its ``size``:

        >>> str(period)
        'year:2021-09:3'

        However, you won't be able to use them as hashmaps keys. Because they
        contain a nested data structure, they're not hashable:

        >>> dict([period, (2021, 9, 13)])
        Traceback (most recent call last):
        ValueError: dictionary update sequence element #0 has length 3...

        All the rest of the ``tuple`` protocols are inherited as well:

        >>> period[0]
        'year'

        >>> period[0] in period
        True

        >>> len(period)
        3

        >>> period == Period(("year", instant, 3))
        True

        >>> period > Period(("year", instant, 3))
        False

        >>> unit, (year, month, day), size = period

    Since a period is a triple it can be used as a dictionary key.

    """

    def __repr__(self) -> str:
        return f"{Period.__name__}({super(Period, self).__repr__()})"

    def __str__(self) -> str:
        """Transform period to a string.

        Returns:
            str: A string representation of the period.

        Examples:
            >>> str(Period(("year", Instant((2021, 1, 1)), 1)))
            '2021'

            >>> str(Period(("year", Instant((2021, 2, 1)), 1)))
            'year:2021-02'

            >>> str(Period(("month", Instant((2021, 2, 1)), 1)))
            '2021-02'

            >>> str(Period(("year", Instant((2021, 1, 1)), 2)))
            'year:2021:2'

            >>> str(Period(("month", Instant((2021, 1, 1)), 2)))
            'month:2021-01:2'

            >>> str(Period(("month", Instant((2021, 1, 1)), 12)))
            '2021'

            >>> str(Period(("year", Instant((2021, 3, 1)), 2)))
            'year:2021-03:2'

            >>> str(Period(("month", Instant((2021, 3, 1)), 2)))
            'month:2021-03:2'

            >>> str(Period(("month", Instant((2021, 3, 1)), 12)))
            'year:2021-03'

        """

        unit, start_instant, size = self

        if unit == ETERNITY:
            return "ETERNITY"

        year, month, day = start_instant

        # 1 year long period
        if unit == MONTH and size == 12 or unit == YEAR and size == 1:
            if month == 1:
                # civil year starting from january
                return str(year)

            else:
                # rolling year
                return f"{YEAR}:{year}-{month:02d}"

        # simple month
        if unit == MONTH and size == 1:
            return f"{year}-{month:02d}"

        # several civil years
        if unit == YEAR and month == 1:
            return f"{unit}:{year}:{size}"

        if unit == DAY:
            if size == 1:
                return f"{year}-{month:02d}-{day:02d}"

            else:
                return f"{unit}:{year}-{month:02d}-{day:02d}:{size}"

        # complex period
        return f"{unit}:{year}-{month:02d}:{size}"

    def __contains__(self, other: object) -> bool:
        """Checks if a ``period`` contains another one.

        Args:
            other (object): The other ``Period``.

        Returns:
            True if ``other`` is contained, otherwise False.

        Example:
            >>> period = Period((YEAR, Instant((2021, 1, 1)), 1))
            >>> sub_period = Period((MONTH, Instant((2021, 1, 1)), 3))

            >>> sub_period in period
            True

        """

        if isinstance(other, Period):
            return self.start <= other.start and self.stop >= other.stop

        return super().__contains__(other)

    @property
    def unit(self) -> str:
        """The ``unit`` of the ``Period``.

        Returns:
            An int.

        Example:
            >>> instant = Instant((2021, 10, 1))
            >>> period = Period((YEAR, instant, 3))
            >>> period.unit
            'year'

        """

        return self[0]

    @property
    def days(self) -> int:
        """Count the number of days in period.

        Returns:
            An int.

        Examples:
            >>> instant = Instant((2021, 10, 1))
            >>> period = Period((YEAR, instant, 3))
            >>> period.size_in_days
            1096

            >>> period = Period((MONTH, instant, 3))
            >>> period.size_in_days
            92

        """

        return (self.stop.date() - self.start.date()).days + 1

    @property
    def size(self) -> int:
        """The ``size`` of the ``Period``.

        Returns:
            An int.

        Example:
            >>> instant = Instant((2021, 10, 1))
            >>> period = Period((YEAR, instant, 3))
            >>> period.size
            3

        """

        return self[2]

    @property
    def size_in_months(self) -> int:
        """The ``size`` of the ``Period`` in months.

        Returns:
            An int.

        Raises:
            ValueError: If the period's unit is not a month or a year.

        Examples:
            >>> instant = Instant((2021, 10, 1))
            >>> period = Period((YEAR, instant, 3))
            >>> period.size_in_months
            36

            >>> period = Period((DAY, instant, 3))
            >>> period.size_in_months
            Traceback (most recent call last):
            ValueError: Cannot calculate number of months in day.

        """

        if self[0] == MONTH:
            return self[2]

        if self[0] == YEAR:
            return self[2] * 12

        raise ValueError(f"Cannot calculate number of months in {self[0]}.")

    @property
    def size_in_days(self) -> int:
        """The ``size`` of the ``Period`` in days.

        Returns:
            An int.

        Raises:
            ValueError: If the period's unit is not a day, a month or a year.

        Examples:
            >>> instant = Instant((2019, 10, 1))
            >>> period = Period((YEAR, instant, 3))
            >>> period.size_in_days
            1096

            >>> period = Period((MONTH, instant, 3))
            >>> period.size_in_days
            92

        """

        unit, instant, length = self

        if unit == DAY:
            return length

        if unit in [MONTH, YEAR]:
            last_day = self.start.offset(length, unit).offset(-1, DAY)
            return (last_day.date() - self.start.date()).days + 1

        raise ValueError(f"Cannot calculate number of days in {unit}")

    @property
    def start(self) -> Instant:
        """The ``Instant`` at which the ``Period`` starts.

        Returns:
            An Instant.

        Example:
            >>> instant = Instant((2021, 10, 1))
            >>> period = Period((YEAR, instant, 3))
            >>> period.start
            Instant((2021, 10, 1))

        """

        return self[1]

    @property
    def stop(self) -> Instant:
        """Last day of the ``Period`` as an ``Instant``.

        Returns:
            An Instant.

        Raises:
            DateUnitValueError: If the period's unit isn't day, month or year.

        Examples:
            >>> Period(("year", Instant((2012, 2, 29)), 1)).stop
            Instant((2013, 2, 28))

            >>> Period(("month", Instant((2012, 2, 29)), 1)).stop
            Instant((2012, 3, 28))

            >>> Period(("day", Instant((2012, 2, 29)), 1)).stop
            Instant((2012, 2, 29))

        """

        unit, start_instant, size = self
        year, month, day = start_instant

        if unit == ETERNITY:
            return Instant((1, 1, 1))

        if unit == 'day':
            if size > 1:
                day += size - 1
                month_last_day = calendar.monthrange(year, month)[1]

                while day > month_last_day:
                    month += 1

                    if month == 13:
                        year += 1
                        month = 1

                    day -= month_last_day
                    month_last_day = calendar.monthrange(year, month)[1]

        else:
            if unit == "month":
                month += size
                while month > 12:
                    year += 1
                    month -= 12
            else:
                if not unit == "year":
                    raise DateUnitValueError(unit)

                year += size
            day -= 1

            if day < 1:
                month -= 1

                if month == 0:
                    year -= 1
                    month = 12

                day += calendar.monthrange(year, month)[1]

            else:
                month_last_day = calendar.monthrange(year, month)[1]

                if day > month_last_day:
                    month += 1

                    if month == 13:
                        year += 1
                        month = 1

                    day -= month_last_day

        return Instant((year, month, day))

    @property
    def last_month(self) -> Period:
        """Last month of the ``Period``.

        Returns:
            A Period.

        """

        return self.first_month.offset(-1)

    @property
    def last_3_months(self) -> Period:
        """Last 3 months of the ``Period``.

        Returns:
            A Period.

        """

        start: Instant = self.first_month.start
        return Period((MONTH, start, 3)).offset(-3)

    @property
    def last_year(self) -> Period:
        """Last year of the ``Period``."""
        start: Instant = self.start.offset("first-of", YEAR)
        return Period((YEAR, start, 1)).offset(-1)

    @property
    def n_2(self) -> Period:
        """Last 2 years of the ``Period``.

        Returns:
            A Period.

        """

        start: Instant = self.start.offset("first-of", YEAR)
        return Period((YEAR, start, 1)).offset(-2)

    @property
    def this_year(self) -> Period:
        """A new year ``Period`` starting at the beginning of the year.

        Returns:
            A Period.

        """

        start: Instant = self.start.offset("first-of", YEAR)
        return Period((YEAR, start, 1))

    @property
    def first_month(self) -> Period:
        """A new month ``Period`` starting at the first of the month.

        Returns:
            A Period.

        """

        start: Instant = self.start.offset("first-of", MONTH)
        return Period((MONTH, start, 1))

    @property
    def first_day(self) -> Period:
        """A new day ``Period``.

        Returns:
            A Period.

        """
        return Period((DAY, self.start, 1))

    def date(self) -> datetime.date:
        """The date representation of the ``period``'s' start date.

        Returns:
            A datetime.date.

        Raises:
            ValueError: If the period's size is greater than 1.

        Examples:
            >>> instant = Instant((2021, 10, 1))
            >>> period = Period((YEAR, instant, 1))
            >>> period.date()
            datetime.date(2021, 10, 1)

            >>> period = Period((YEAR, instant, 3))
            >>> period.date()
            Traceback (most recent call last):
            ValueError: 'date' undefined for period size > 1: year:2021-10:3.

        """

        if self.size > 1:
            raise ValueError(f"'date' undefined for period size > 1: {self}.")

        return self.start.date()

    def offset(
            self,
            offset: Union[str, int],
            unit: Optional[str] = None,
            ) -> Period:
        """Increment (or decrement) the given period with offset units.

        Args:
            offset (str | int): How much of ``unit`` to offset.
            unit (str): What to offset.

        Returns:
            Period: A new one.

        Examples:
            >>> Period(("day", Instant((2014, 2, 3)), 1)).offset("first-of", "month")
            Period(('day', Instant((2014, 2, 1)), 1))

            >>> Period(("month", Instant((2014, 2, 3)), 4)).offset("last-of", "month")
            Period(('month', Instant((2014, 2, 28)), 4))

            >>> Period(("day", Instant((2021, 1, 1)), 365)).offset(-3)
            Period(('day', Instant((2020, 12, 29)), 365))

            >>> Period(("day", Instant((2021, 1, 1)), 365)).offset(1, "year")
            Period(('day', Instant((2022, 1, 1)), 365))

        """

        start = self[1].offset(offset, self[0] if unit is None else unit)

        return Period((self[0], start, self[2]))

    def subperiods(self, unit: str) -> Sequence[Period]:
        """Return the list of all the periods of unit ``unit``.

        Args:
            unit: A string representing period's ``unit``.

        Returns:
            A list of periods.

        Raises:
            DateUnitValueError: If the ``unit`` is not a valid date unit.
            ValueError: If the period's unit is smaller than the given unit.

        Examples:
            >>> period = Period((YEAR, Instant((2021, 1, 1)), 1))
            >>> period.subperiods(MONTH)
            [Period(('month', Instant((2021, 1, 1)), 1)),...2021, 12, 1)), 1))]

            >>> period = Period((YEAR, Instant((2021, 1, 1)), 2))
            >>> period.subperiods(YEAR)
            [Period(('year', Instant((2021, 1, 1)), 1)),...((2022, 1, 1)), 1))]

        """

        if UNIT_WEIGHTS[self.unit] < UNIT_WEIGHTS[unit]:
            raise ValueError(f"Cannot subdivide {self.unit} into {unit}")

        if unit == YEAR:
            return [self.this_year.offset(i, YEAR) for i in range(self.size)]

        if unit == MONTH:
            return [self.first_month.offset(i, MONTH) for i in range(self.size_in_months)]

        if unit == DAY:
            return [self.first_day.offset(i, DAY) for i in range(self.size_in_days)]

        raise DateUnitValueError(unit)
