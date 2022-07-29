from __future__ import annotations

import calendar

from . import helpers
from .date_unit import DateUnit
from .instant_ import Instant


class Period(tuple):
    """Toolbox to handle date intervals.

    A :class:`.Period` is a triple (``unit``, ``start``, ``size``).

    Attributes:
        unit (:obj:`str`):
            Either ``year``, ``month``, ``day`` or ``eternity``.
        start (:obj:`.Instant`):
            The "instant" the :obj:`.Period` starts at.
        size (:obj:`int`):
            The amount of ``unit``, starting at ``start``, at least ``1``.

    Args:
        (tuple(tuple(str, .Instant, int))):
            The ``unit``, ``start``, and ``size``, accordingly.

    Examples:
        >>> instant = Instant((2021, 9, 1))
        >>> period = Period((DateUnit.YEAR, instant, 3))

        >>> repr(Period)
        "<class 'openfisca_core.periods.period_.Period'>"

        >>> repr(period)
        "Period((<DateUnit.YEAR: 'year'>, Instant((2021, 9, 1)), 3))"

        >>> str(period)
        'year:2021-09:3'

        >>> dict([period, instant])
        Traceback (most recent call last):
        ValueError: dictionary update sequence element #0 has length 3...

        >>> list(period)
        [<DateUnit.YEAR: 'year'>, Instant((2021, 9, 1)), 3]

        >>> period[0]
        <DateUnit.YEAR: 'year'>

        >>> period[0] in period
        True

        >>> len(period)
        3

        >>> period == Period((DateUnit.YEAR, instant, 3))
        True

        >>> period != Period((DateUnit.YEAR, instant, 3))
        False

        >>> period > Period((DateUnit.YEAR, instant, 3))
        False

        >>> period < Period((DateUnit.YEAR, instant, 3))
        False

        >>> period >= Period((DateUnit.YEAR, instant, 3))
        True

        >>> period <= Period((DateUnit.YEAR, instant, 3))
        True

        >>> period.date
        Traceback (most recent call last):
        AssertionError: "date" is undefined for a period of size > 1

        >>> Period((DateUnit.YEAR, instant, 1)).date
        datetime.date(2021, 9, 1)

        >>> period.days
        1096

        >>> period.size
        3

        >>> period.size_in_months
        36

        >>> period.size_in_days
        1096

        >>> period.start
        Instant((2021, 9, 1))

        >>> period.stop
        Instant((2024, 8, 31))

        >>> period.unit
        <DateUnit.YEAR: 'year'>

        >>> period.last_3_months
        Period((<DateUnit.MONTH: 'month'>, Instant((2021, 6, 1)), 3))

        >>> period.last_month
        Period((<DateUnit.MONTH: 'month'>, Instant((2021, 8, 1)), 1))

        >>> period.last_year
        Period((<DateUnit.YEAR: 'year'>, Instant((2020, 1, 1)), 1))

        >>> period.n_2
        Period((<DateUnit.YEAR: 'year'>, Instant((2019, 1, 1)), 1))

        >>> period.this_year
        Period((<DateUnit.YEAR: 'year'>, Instant((2021, 1, 1)), 1))

        >>> period.first_month
        Period((<DateUnit.MONTH: 'month'>, Instant((2021, 9, 1)), 1))

        >>> period.first_day
        Period((<DateUnit.DAY: 'day'>, Instant((2021, 9, 1)), 1))

    """

    def __repr__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, super(Period, self).__repr__())

    def __str__(self) -> str:
        unit, start_instant, size = self
        if unit == DateUnit.ETERNITY:
            return 'ETERNITY'
        year, month, day = start_instant

        # 1 year long period
        if (unit == DateUnit.MONTH and size == 12 or unit == DateUnit.YEAR and size == 1):
            if month == 1:
                # civil year starting from january
                return str(year)
            else:
                # rolling year
                return '{}:{}-{:02d}'.format(DateUnit.YEAR, year, month)
        # simple month
        if unit == DateUnit.MONTH and size == 1:
            return '{}-{:02d}'.format(year, month)
        # several civil years
        if unit == DateUnit.YEAR and month == 1:
            return '{}:{}:{}'.format(unit, year, size)

        if unit == DateUnit.DAY:
            if size == 1:
                return '{}-{:02d}-{:02d}'.format(year, month, day)
            else:
                return '{}:{}-{:02d}-{:02d}:{}'.format(unit, year, month, day, size)

        # complex period
        return '{}:{}-{:02d}:{}'.format(unit, year, month, size)

    @property
    def date(self):
        assert self.size == 1, '"date" is undefined for a period of size > 1: {}'.format(self)
        return self.start.date

    @property
    def days(self):
        """Count the number of days in period."""
        return (self.stop.date - self.start.date).days + 1

    def intersection(self, start, stop):
        if start is None and stop is None:
            return self
        period_start = self[1]
        period_stop = self.stop
        if start is None:
            start = period_start
        if stop is None:
            stop = period_stop
        if stop < period_start or period_stop < start:
            return None
        intersection_start = max(period_start, start)
        intersection_stop = min(period_stop, stop)
        if intersection_start == period_start and intersection_stop == period_stop:
            return self
        if intersection_start.day == 1 and intersection_start.month == 1 \
                and intersection_stop.day == 31 and intersection_stop.month == 12:
            return self.__class__((
                DateUnit.YEAR,
                intersection_start,
                intersection_stop.year - intersection_start.year + 1,
                ))
        if intersection_start.day == 1 and intersection_stop.day == calendar.monthrange(intersection_stop.year,
                intersection_stop.month)[1]:
            return self.__class__((
                DateUnit.MONTH,
                intersection_start,
                (
                    (intersection_stop.year - intersection_start.year) * 12
                    + intersection_stop.month
                    - intersection_start.month
                    + 1
                    ),
                ))
        return self.__class__((
            DateUnit.DAY,
            intersection_start,
            (intersection_stop.date - intersection_start.date).days + 1,
            ))

    def get_subperiods(self, unit):
        """Return the list of periods of unit ``unit`` contained in self.

        Examples:
            >>> period = Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1))
            >>> period.get_subperiods(DateUnit.MONTH)
            [Period((<DateUnit.MONTH: 'month'>, Instant((2021, 1, 1)), 1)),...2021, 12, 1)), 1))]

            >>> period = Period((DateUnit.YEAR, Instant((2021, 1, 1)), 2))
            >>> period.get_subperiods(DateUnit.YEAR)
            [Period((<DateUnit.YEAR: 'year'>, Instant((2021, 1, 1)), 1)),...((2022, 1, 1)), 1))]

        """

        if helpers.unit_weight(self.unit) < helpers.unit_weight(unit):
            raise ValueError('Cannot subdivide {0} into {1}'.format(self.unit, unit))

        if unit == DateUnit.YEAR:
            return [self.this_year.offset(i, DateUnit.YEAR) for i in range(self.size)]

        if unit == DateUnit.MONTH:
            return [self.first_month.offset(i, DateUnit.MONTH) for i in range(self.size_in_months)]

        if unit == DateUnit.DAY:
            return [self.first_day.offset(i, DateUnit.DAY) for i in range(self.size_in_days)]

    def offset(self, offset, unit = None):
        """Increment (or decrement) the given period with offset units.

        Examples:
            >>> Period((DateUnit.DAY, Instant((2021, 1, 1)), 365)).offset(1)
            Period((<DateUnit.DAY: 'day'>, Instant((2021, 1, 2)), 365))

            >>> Period((DateUnit.DAY, Instant((2021, 1, 1)), 365)).offset(1, DateUnit.DAY)
            Period((<DateUnit.DAY: 'day'>, Instant((2021, 1, 2)), 365))

            >>> Period((DateUnit.DAY, Instant((2021, 1, 1)), 365)).offset(1, DateUnit.MONTH)
            Period((<DateUnit.DAY: 'day'>, Instant((2021, 2, 1)), 365))

            >>> Period((DateUnit.DAY, Instant((2021, 1, 1)), 365)).offset(1, DateUnit.YEAR)
            Period((<DateUnit.DAY: 'day'>, Instant((2022, 1, 1)), 365))

            >>> Period((DateUnit.MONTH, Instant((2021, 1, 1)), 12)).offset(1)
            Period((<DateUnit.MONTH: 'month'>, Instant((2021, 2, 1)), 12))

            >>> Period((DateUnit.MONTH, Instant((2021, 1, 1)), 12)).offset(1, DateUnit.DAY)
            Period((<DateUnit.MONTH: 'month'>, Instant((2021, 1, 2)), 12))

            >>> Period((DateUnit.MONTH, Instant((2021, 1, 1)), 12)).offset(1, DateUnit.MONTH)
            Period((<DateUnit.MONTH: 'month'>, Instant((2021, 2, 1)), 12))

            >>> Period((DateUnit.MONTH, Instant((2021, 1, 1)), 12)).offset(1, DateUnit.YEAR)
            Period((<DateUnit.MONTH: 'month'>, Instant((2022, 1, 1)), 12))

            >>> Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1)).offset(1)
            Period((<DateUnit.YEAR: 'year'>, Instant((2022, 1, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1)).offset(1, DateUnit.DAY)
            Period((<DateUnit.YEAR: 'year'>, Instant((2021, 1, 2)), 1))

            >>> Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1)).offset(1, DateUnit.MONTH)
            Period((<DateUnit.YEAR: 'year'>, Instant((2021, 2, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2021, 1, 1)), 1)).offset(1, DateUnit.YEAR)
            Period((<DateUnit.YEAR: 'year'>, Instant((2022, 1, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2011, 2, 28)), 1)).offset(1)
            Period((<DateUnit.DAY: 'day'>, Instant((2011, 3, 1)), 1))

            >>> Period((DateUnit.MONTH, Instant((2011, 2, 28)), 1)).offset(1)
            Period((<DateUnit.MONTH: 'month'>, Instant((2011, 3, 28)), 1))

            >>> Period((DateUnit.YEAR, Instant((2011, 2, 28)), 1)).offset(1)
            Period((<DateUnit.YEAR: 'year'>, Instant((2012, 2, 28)), 1))

            >>> Period((DateUnit.DAY, Instant((2011, 3, 1)), 1)).offset(-1)
            Period((<DateUnit.DAY: 'day'>, Instant((2011, 2, 28)), 1))

            >>> Period((DateUnit.MONTH, Instant((2011, 3, 1)), 1)).offset(-1)
            Period((<DateUnit.MONTH: 'month'>, Instant((2011, 2, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2011, 3, 1)), 1)).offset(-1)
            Period((<DateUnit.YEAR: 'year'>, Instant((2010, 3, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 1, 30)), 1)).offset(3)
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 2)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 1, 30)), 1)).offset(3)
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 4, 30)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 30)), 1)).offset(3)
            Period((<DateUnit.YEAR: 'year'>, Instant((2017, 1, 30)), 1))

            >>> Period((DateUnit.DAY, Instant((2021, 1, 1)), 365)).offset(-3)
            Period((<DateUnit.DAY: 'day'>, Instant((2020, 12, 29)), 365))

            >>> Period((DateUnit.MONTH, Instant((2021, 1, 1)), 12)).offset(-3)
            Period((<DateUnit.MONTH: 'month'>, Instant((2020, 10, 1)), 12))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 1)), 1)).offset(-3)
            Period((<DateUnit.YEAR: 'year'>, Instant((2011, 1, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 1)).offset("first-of", DateUnit.MONTH)
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 1)).offset("first-of", DateUnit.YEAR)
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 4)).offset("first-of", DateUnit.MONTH)
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 1)), 4))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 4)).offset("first-of", DateUnit.YEAR)
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 1, 1)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset("first-of")
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 1)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset("first-of", DateUnit.MONTH)
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 1)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset("first-of", DateUnit.YEAR)
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset("first-of")
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 1)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset("first-of", DateUnit.MONTH)
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 1)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset("first-of", DateUnit.YEAR)
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 1, 1)), 4))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 30)), 1)).offset("first-of")
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 30)), 1)).offset("first-of", DateUnit.MONTH)
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 30)), 1)).offset("first-of", DateUnit.YEAR)
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset("first-of")
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset("first-of", DateUnit.MONTH)
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 2, 1)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset("first-of", DateUnit.YEAR)
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 1)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 1)).offset("last-of", DateUnit.MONTH)
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 28)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 1)).offset("last-of", DateUnit.YEAR)
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 12, 31)), 1))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 4)).offset("last-of", DateUnit.MONTH)
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 2, 28)), 4))

            >>> Period((DateUnit.DAY, Instant((2014, 2, 3)), 4)).offset("last-of", DateUnit.YEAR)
            Period((<DateUnit.DAY: 'day'>, Instant((2014, 12, 31)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset("last-of")
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 28)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset("last-of", DateUnit.MONTH)
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 28)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 1)).offset("last-of", DateUnit.YEAR)
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 12, 31)), 1))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset("last-of")
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 28)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset("last-of", DateUnit.MONTH)
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 2, 28)), 4))

            >>> Period((DateUnit.MONTH, Instant((2014, 2, 3)), 4)).offset("last-of", DateUnit.YEAR)
            Period((<DateUnit.MONTH: 'month'>, Instant((2014, 12, 31)), 4))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset("last-of")
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 12, 31)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 1, 1)), 1)).offset("last-of", DateUnit.MONTH)
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 1, 31)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset("last-of", DateUnit.YEAR)
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 12, 31)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset("last-of")
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 12, 31)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset("last-of", DateUnit.MONTH)
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 2, 28)), 1))

            >>> Period((DateUnit.YEAR, Instant((2014, 2, 3)), 1)).offset("last-of", DateUnit.YEAR)
            Period((<DateUnit.YEAR: 'year'>, Instant((2014, 12, 31)), 1))

        """

        return self.__class__((self[0], self[1].offset(offset, self[0] if unit is None else unit), self[2]))

    def contains(self, other: Period) -> bool:
        """Returns ``True`` if the period contains ``other``.

        For instance, ``period(2015)`` contains ``period(2015-01)``.

        """

        return self.start <= other.start and self.stop >= other.stop

    @property
    def size(self):
        """Return the size of the period."""

        return self[2]

    @property
    def size_in_months(self):
        """Return the size of the period in months."""

        if (self[0] == DateUnit.MONTH):
            return self[2]
        if(self[0] == DateUnit.YEAR):
            return self[2] * 12
        raise ValueError("Cannot calculate number of months in {0}".format(self[0]))

    @property
    def size_in_days(self):
        """Return the size of the period in days."""

        unit, instant, length = self

        if unit == DateUnit.DAY:
            return length
        if unit in [DateUnit.MONTH, DateUnit.YEAR]:
            last_day = self.start.offset(length, unit).offset(-1, DateUnit.DAY)
            return (last_day.date - self.start.date).days + 1

        raise ValueError("Cannot calculate number of days in {0}".format(unit))

    @property
    def start(self) -> Instant:
        """Return the first day of the period as an Instant instance."""

        return self[1]

    @property
    def stop(self) -> Instant:
        """Return the last day of the period as an Instant instance.

        Examples:
            >>> Period((DateUnit.YEAR, Instant((2022, 1, 1)), 1)).stop
            Instant((2022, 12, 31))

            >>> Period((DateUnit.MONTH, Instant((2022, 1, 1)), 12)).stop
            Instant((2022, 12, 31))

            >>> Period((DateUnit.DAY, Instant((2022, 1, 1)), 365)).stop
            Instant((2022, 12, 31))

            >>> Period((DateUnit.YEAR, Instant((2012, 2, 29)), 1)).stop
            Instant((2013, 2, 28))

            >>> Period((DateUnit.MONTH, Instant((2012, 2, 29)), 1)).stop
            Instant((2012, 3, 28))

            >>> Period((DateUnit.DAY, Instant((2012, 2, 29)), 1)).stop
            Instant((2012, 2, 29))

            >>> Period((DateUnit.YEAR, Instant((2012, 2, 29)), 2)).stop
            Instant((2014, 2, 28))

            >>> Period((DateUnit.MONTH, Instant((2012, 2, 29)), 2)).stop
            Instant((2012, 4, 28))

            >>> Period((DateUnit.DAY, Instant((2012, 2, 29)), 2)).stop
            Instant((2012, 3, 1))

        """

        unit, start_instant, size = self
        year, month, day = start_instant
        if unit == DateUnit.ETERNITY:
            return Instant((float("inf"), float("inf"), float("inf")))
        if unit == DateUnit.DAY:
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
            if unit == DateUnit.MONTH:
                month += size
                while month > 12:
                    year += 1
                    month -= 12
            else:
                assert unit == DateUnit.YEAR, 'Invalid unit: {} of type {}'.format(unit, type(unit))
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
    def unit(self):
        return self[0]

    # Reference periods

    @property
    def last_3_months(self):
        return self.first_month.start.period(DateUnit.MONTH, 3).offset(-3)

    @property
    def last_month(self):
        return self.first_month.offset(-1)

    @property
    def last_year(self):
        return self.start.offset("first-of", DateUnit.YEAR).period(DateUnit.YEAR).offset(-1)

    @property
    def n_2(self):
        return self.start.offset("first-of", DateUnit.YEAR).period(DateUnit.YEAR).offset(-2)

    @property
    def this_year(self):
        return self.start.offset("first-of", DateUnit.YEAR).period(DateUnit.YEAR)

    @property
    def first_month(self):
        return self.start.offset("first-of", DateUnit.MONTH).period(DateUnit.MONTH)

    @property
    def first_day(self):
        return self.start.period(DateUnit.DAY)
