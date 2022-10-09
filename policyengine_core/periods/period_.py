from __future__ import annotations

import calendar
from datetime import datetime
from typing import List

from policyengine_core import periods
from policyengine_core.periods import config, helpers
from policyengine_core.periods.instant_ import Instant


class Period(tuple):
    """
    Toolbox to handle date intervals.

    A period is a triple (unit, start, size), where unit is either "month" or "year", where start format is a
    (year, month, day) triple, and where size is an integer > 1.

    Since a period is a triple it can be used as a dictionary key.
    """

    def __repr__(self) -> str:
        """
        Transform period to to its Python representation as a string.

        >>> repr(period('year', 2014))
        "Period(('year', Instant((2014, 1, 1)), 1))"
        >>> repr(period('month', '2014-2'))
        "Period(('month', Instant((2014, 2, 1)), 1))"
        >>> repr(period('day', '2014-2-3'))
        "Period(('day', Instant((2014, 2, 3)), 1))"
        """
        return "{}({})".format(
            self.__class__.__name__, super(Period, self).__repr__()
        )

    def __str__(self) -> str:
        """
        Transform period to a string.

        >>> str(period(YEAR, 2014))
        '2014'

        >>> str(period(YEAR, '2014-2'))
        'year:2014-02'
        >>> str(period(MONTH, '2014-2'))
        '2014-02'

        >>> str(period(YEAR, 2012, size = 2))
        'year:2012:2'
        >>> str(period(MONTH, 2012, size = 2))
        'month:2012-01:2'
        >>> str(period(MONTH, 2012, size = 12))
        '2012'

        >>> str(period(YEAR, '2012-3', size = 2))
        'year:2012-03:2'
        >>> str(period(MONTH, '2012-3', size = 2))
        'month:2012-03:2'
        >>> str(period(MONTH, '2012-3', size = 12))
        'year:2012-03'
        """

        unit, start_instant, size = self
        if unit == config.ETERNITY:
            return "ETERNITY"
        year, month, day = start_instant

        # 1 year long period
        if (
            unit == config.MONTH
            and size == 12
            or unit == config.YEAR
            and size == 1
        ):
            if month == 1:
                # civil year starting from january
                return str(year)
            else:
                # rolling year
                return "{}:{}-{:02d}".format(config.YEAR, year, month)
        # simple month
        if unit == config.MONTH and size == 1:
            return "{}-{:02d}".format(year, month)
        # several civil years
        if unit == config.YEAR and month == 1:
            return "{}:{}:{}".format(unit, year, size)

        if unit == config.DAY:
            if size == 1:
                return "{}-{:02d}-{:02d}".format(year, month, day)
            else:
                return "{}:{}-{:02d}-{:02d}:{}".format(
                    unit, year, month, day, size
                )

        # complex period
        return "{}:{}-{:02d}:{}".format(unit, year, month, size)

    @property
    def date(self) -> datetime.date:
        assert (
            self.size == 1
        ), '"date" is undefined for a period of size > 1: {}'.format(self)
        return self.start.date

    @property
    def days(self) -> int:
        """
        Count the number of days in period.

        >>> period('day', 2014).days
        365
        >>> period('month', 2014).days
        365
        >>> period('year', 2014).days
        365

        >>> period('day', '2014-2').days
        28
        >>> period('month', '2014-2').days
        28
        >>> period('year', '2014-2').days
        365

        >>> period('day', '2014-2-3').days
        1
        >>> period('month', '2014-2-3').days
        28
        >>> period('year', '2014-2-3').days
        365
        """
        return (self.stop.date - self.start.date).days + 1

    def intersection(self, start: Instant, stop: Instant):
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
        if (
            intersection_start == period_start
            and intersection_stop == period_stop
        ):
            return self
        if (
            intersection_start.day == 1
            and intersection_start.month == 1
            and intersection_stop.day == 31
            and intersection_stop.month == 12
        ):
            return self.__class__(
                (
                    "year",
                    intersection_start,
                    intersection_stop.year - intersection_start.year + 1,
                )
            )
        if (
            intersection_start.day == 1
            and intersection_stop.day
            == calendar.monthrange(
                intersection_stop.year, intersection_stop.month
            )[1]
        ):
            return self.__class__(
                (
                    "month",
                    intersection_start,
                    (
                        (intersection_stop.year - intersection_start.year) * 12
                        + intersection_stop.month
                        - intersection_start.month
                        + 1
                    ),
                )
            )
        return self.__class__(
            (
                "day",
                intersection_start,
                (intersection_stop.date - intersection_start.date).days + 1,
            )
        )

    def get_subperiods(self, unit: str) -> List["Period"]:
        """
        Return the list of all the periods of unit ``unit`` contained in self.

        Examples:

        >>> period('2017').get_subperiods(MONTH)
        >>> [period('2017-01'), period('2017-02'), ... period('2017-12')]

        >>> period('year:2014:2').get_subperiods(YEAR)
        >>> [period('2014'), period('2015')]
        """
        if helpers.unit_weight(self.unit) < helpers.unit_weight(unit):
            raise ValueError(
                "Cannot subdivide {0} into {1}".format(self.unit, unit)
            )

        if unit == config.YEAR:
            return [
                self.this_year.offset(i, config.YEAR) for i in range(self.size)
            ]

        if unit == config.MONTH:
            return [
                self.first_month.offset(i, config.MONTH)
                for i in range(self.size_in_months)
            ]

        if unit == config.DAY:
            return [
                self.first_day.offset(i, config.DAY)
                for i in range(self.size_in_days)
            ]

    def offset(self, offset: int, unit: str = None) -> "Period":
        """
        Increment (or decrement) the given period with offset units.

        >>> period('day', 2014).offset(1)
        Period(('day', Instant((2014, 1, 2)), 365))
        >>> period('day', 2014).offset(1, 'day')
        Period(('day', Instant((2014, 1, 2)), 365))
        >>> period('day', 2014).offset(1, 'month')
        Period(('day', Instant((2014, 2, 1)), 365))
        >>> period('day', 2014).offset(1, 'year')
        Period(('day', Instant((2015, 1, 1)), 365))

        >>> period('month', 2014).offset(1)
        Period(('month', Instant((2014, 2, 1)), 12))
        >>> period('month', 2014).offset(1, 'day')
        Period(('month', Instant((2014, 1, 2)), 12))
        >>> period('month', 2014).offset(1, 'month')
        Period(('month', Instant((2014, 2, 1)), 12))
        >>> period('month', 2014).offset(1, 'year')
        Period(('month', Instant((2015, 1, 1)), 12))

        >>> period('year', 2014).offset(1)
        Period(('year', Instant((2015, 1, 1)), 1))
        >>> period('year', 2014).offset(1, 'day')
        Period(('year', Instant((2014, 1, 2)), 1))
        >>> period('year', 2014).offset(1, 'month')
        Period(('year', Instant((2014, 2, 1)), 1))
        >>> period('year', 2014).offset(1, 'year')
        Period(('year', Instant((2015, 1, 1)), 1))

        >>> period('day', '2011-2-28').offset(1)
        Period(('day', Instant((2011, 3, 1)), 1))
        >>> period('month', '2011-2-28').offset(1)
        Period(('month', Instant((2011, 3, 28)), 1))
        >>> period('year', '2011-2-28').offset(1)
        Period(('year', Instant((2012, 2, 28)), 1))

        >>> period('day', '2011-3-1').offset(-1)
        Period(('day', Instant((2011, 2, 28)), 1))
        >>> period('month', '2011-3-1').offset(-1)
        Period(('month', Instant((2011, 2, 1)), 1))
        >>> period('year', '2011-3-1').offset(-1)
        Period(('year', Instant((2010, 3, 1)), 1))

        >>> period('day', '2014-1-30').offset(3)
        Period(('day', Instant((2014, 2, 2)), 1))
        >>> period('month', '2014-1-30').offset(3)
        Period(('month', Instant((2014, 4, 30)), 1))
        >>> period('year', '2014-1-30').offset(3)
        Period(('year', Instant((2017, 1, 30)), 1))

        >>> period('day', 2014).offset(-3)
        Period(('day', Instant((2013, 12, 29)), 365))
        >>> period('month', 2014).offset(-3)
        Period(('month', Instant((2013, 10, 1)), 12))
        >>> period('year', 2014).offset(-3)
        Period(('year', Instant((2011, 1, 1)), 1))

        >>> period('day', '2014-2-3').offset('first-of', 'month')
        Period(('day', Instant((2014, 2, 1)), 1))
        >>> period('day', '2014-2-3').offset('first-of', 'year')
        Period(('day', Instant((2014, 1, 1)), 1))

        >>> period('day', '2014-2-3', 4).offset('first-of', 'month')
        Period(('day', Instant((2014, 2, 1)), 4))
        >>> period('day', '2014-2-3', 4).offset('first-of', 'year')
        Period(('day', Instant((2014, 1, 1)), 4))

        >>> period('month', '2014-2-3').offset('first-of')
        Period(('month', Instant((2014, 2, 1)), 1))
        >>> period('month', '2014-2-3').offset('first-of', 'month')
        Period(('month', Instant((2014, 2, 1)), 1))
        >>> period('month', '2014-2-3').offset('first-of', 'year')
        Period(('month', Instant((2014, 1, 1)), 1))

        >>> period('month', '2014-2-3', 4).offset('first-of')
        Period(('month', Instant((2014, 2, 1)), 4))
        >>> period('month', '2014-2-3', 4).offset('first-of', 'month')
        Period(('month', Instant((2014, 2, 1)), 4))
        >>> period('month', '2014-2-3', 4).offset('first-of', 'year')
        Period(('month', Instant((2014, 1, 1)), 4))

        >>> period('year', 2014).offset('first-of')
        Period(('year', Instant((2014, 1, 1)), 1))
        >>> period('year', 2014).offset('first-of', 'month')
        Period(('year', Instant((2014, 1, 1)), 1))
        >>> period('year', 2014).offset('first-of', 'year')
        Period(('year', Instant((2014, 1, 1)), 1))

        >>> period('year', '2014-2-3').offset('first-of')
        Period(('year', Instant((2014, 1, 1)), 1))
        >>> period('year', '2014-2-3').offset('first-of', 'month')
        Period(('year', Instant((2014, 2, 1)), 1))
        >>> period('year', '2014-2-3').offset('first-of', 'year')
        Period(('year', Instant((2014, 1, 1)), 1))

        >>> period('day', '2014-2-3').offset('last-of', 'month')
        Period(('day', Instant((2014, 2, 28)), 1))
        >>> period('day', '2014-2-3').offset('last-of', 'year')
        Period(('day', Instant((2014, 12, 31)), 1))

        >>> period('day', '2014-2-3', 4).offset('last-of', 'month')
        Period(('day', Instant((2014, 2, 28)), 4))
        >>> period('day', '2014-2-3', 4).offset('last-of', 'year')
        Period(('day', Instant((2014, 12, 31)), 4))

        >>> period('month', '2014-2-3').offset('last-of')
        Period(('month', Instant((2014, 2, 28)), 1))
        >>> period('month', '2014-2-3').offset('last-of', 'month')
        Period(('month', Instant((2014, 2, 28)), 1))
        >>> period('month', '2014-2-3').offset('last-of', 'year')
        Period(('month', Instant((2014, 12, 31)), 1))

        >>> period('month', '2014-2-3', 4).offset('last-of')
        Period(('month', Instant((2014, 2, 28)), 4))
        >>> period('month', '2014-2-3', 4).offset('last-of', 'month')
        Period(('month', Instant((2014, 2, 28)), 4))
        >>> period('month', '2014-2-3', 4).offset('last-of', 'year')
        Period(('month', Instant((2014, 12, 31)), 4))

        >>> period('year', 2014).offset('last-of')
        Period(('year', Instant((2014, 12, 31)), 1))
        >>> period('year', 2014).offset('last-of', 'month')
        Period(('year', Instant((2014, 1, 31)), 1))
        >>> period('year', 2014).offset('last-of', 'year')
        Period(('year', Instant((2014, 12, 31)), 1))

        >>> period('year', '2014-2-3').offset('last-of')
        Period(('year', Instant((2014, 12, 31)), 1))
        >>> period('year', '2014-2-3').offset('last-of', 'month')
        Period(('year', Instant((2014, 2, 28)), 1))
        >>> period('year', '2014-2-3').offset('last-of', 'year')
        Period(('year', Instant((2014, 12, 31)), 1))
        """
        return self.__class__(
            (
                self[0],
                self[1].offset(offset, self[0] if unit is None else unit),
                self[2],
            )
        )

    def contains(self, other: Period) -> bool:
        """
        Returns ``True`` if the period contains ``other``. For instance, ``period(2015)`` contains ``period(2015-01)``
        """
        return self.start <= other.start and self.stop >= other.stop

    @property
    def size(self) -> int:
        """
        Return the size of the period.

        >>> period('month', '2012-2-29', 4).size
        4
        """
        return self[2]

    @property
    def size_in_months(self) -> int:
        """
        Return the size of the period in months.

        >>> period('month', '2012-2-29', 4).size_in_months
        4
        >>> period('year', '2012', 1).size_in_months
        12
        """
        if self[0] == config.MONTH:
            return self[2]
        if self[0] == config.YEAR:
            return self[2] * 12
        raise ValueError(
            "Cannot calculate number of months in {0}".format(self[0])
        )

    @property
    def size_in_days(self) -> int:
        """
        Return the size of the period in days.

        >>> period('month', '2012-2-29', 4).size_in_days
        28
        >>> period('year', '2012', 1).size_in_days
        366
        """
        unit, instant, length = self

        if unit == config.DAY:
            return length
        if unit in [config.MONTH, config.YEAR]:
            last_day = self.start.offset(length, unit).offset(-1, config.DAY)
            return (last_day.date - self.start.date).days + 1

        raise ValueError("Cannot calculate number of days in {0}".format(unit))

    @property
    def start(self) -> periods.Instant:
        """
        Return the first day of the period as an Instant instance.

        >>> period('month', '2012-2-29', 4).start
        Instant((2012, 2, 29))
        """
        return self[1]

    @property
    def stop(self) -> periods.Instant:
        """
        Return the last day of the period as an Instant instance.

        >>> period('year', 2014).stop
        Instant((2014, 12, 31))
        >>> period('month', 2014).stop
        Instant((2014, 12, 31))
        >>> period('day', 2014).stop
        Instant((2014, 12, 31))

        >>> period('year', '2012-2-29').stop
        Instant((2013, 2, 28))
        >>> period('month', '2012-2-29').stop
        Instant((2012, 3, 28))
        >>> period('day', '2012-2-29').stop
        Instant((2012, 2, 29))

        >>> period('year', '2012-2-29', 2).stop
        Instant((2014, 2, 28))
        >>> period('month', '2012-2-29', 2).stop
        Instant((2012, 4, 28))
        >>> period('day', '2012-2-29', 2).stop
        Instant((2012, 3, 1))
        """
        unit, start_instant, size = self
        year, month, day = start_instant
        if unit == config.ETERNITY:
            return periods.Instant((float("inf"), float("inf"), float("inf")))
        if unit == "day":
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
                assert unit == "year", "Invalid unit: {} of type {}".format(
                    unit, type(unit)
                )
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
        return periods.Instant((year, month, day))

    @property
    def unit(self) -> str:
        return self[0]

    # Reference periods

    @property
    def last_3_months(self) -> "Period":
        return self.first_month.start.period("month", 3).offset(-3)

    @property
    def last_month(self) -> "Period":
        return self.first_month.offset(-1)

    @property
    def last_year(self) -> "Period":
        return self.start.offset("first-of", "year").period("year").offset(-1)

    @property
    def n_2(self) -> "Period":
        return self.start.offset("first-of", "year").period("year").offset(-2)

    @property
    def this_year(self) -> "Period":
        return self.start.offset("first-of", "year").period("year")

    @property
    def first_month(self) -> "Period":
        return self.start.offset("first-of", "month").period("month")

    @property
    def first_day(self) -> "Period":
        return self.start.period("day")
