# -*- coding: utf-8 -*-


"""Toolbox to handle date intervals

A period is a triple (unit, start, size), where unit is either "month" or "year", where start format is a
(year, month, day) triple, and where size is an integer > 1.

Since a period is a triple it can be used as a dictionary key.
"""
import calendar
import datetime
import re
from os import linesep


DAY = 'day'
MONTH = 'month'
YEAR = 'year'
ETERNITY = 'eternity'

INSTANT_PATTERN = re.compile(r'^\d{4}(?:-\d{1,2}){0,2}$')  # matches '2015', '2015-01', '2015-01-01'


def N_(message):
    return message


date_by_instant_cache = {}
str_by_instant_cache = {}
year_or_month_or_day_re = re.compile(r'(18|19|20)\d{2}(-(0?[1-9]|1[0-2])(-([0-2]?\d|3[0-1]))?)?$')


class Instant(tuple):
    def __repr__(self):
        """Transform instant to to its Python representation as a string.

        >>> repr(instant(2014))
        'Instant((2014, 1, 1))'
        >>> repr(instant('2014-2'))
        'Instant((2014, 2, 1))'
        >>> repr(instant('2014-2-3'))
        'Instant((2014, 2, 3))'
        """
        return '{}({})'.format(self.__class__.__name__, super(Instant, self).__repr__())

    def __str__(self):
        """Transform instant to a string.

        >>> str(instant(2014))
        '2014-01-01'
        >>> str(instant('2014-2'))
        '2014-02-01'
        >>> str(instant('2014-2-3'))
        '2014-02-03'

        """
        instant_str = str_by_instant_cache.get(self)
        if instant_str is None:
            str_by_instant_cache[self] = instant_str = self.date.isoformat()
        return instant_str

    @property
    def date(self):
        """Convert instant to a date.

        >>> instant(2014).date
        datetime.date(2014, 1, 1)
        >>> instant('2014-2').date
        datetime.date(2014, 2, 1)
        >>> instant('2014-2-3').date
        datetime.date(2014, 2, 3)
        """
        instant_date = date_by_instant_cache.get(self)
        if instant_date is None:
            date_by_instant_cache[self] = instant_date = datetime.date(*self)
        return instant_date

    @property
    def day(self):
        """Extract day from instant.

        >>> instant(2014).day
        1
        >>> instant('2014-2').day
        1
        >>> instant('2014-2-3').day
        3
        """
        return self[2]

    @property
    def month(self):
        """Extract month from instant.

        >>> instant(2014).month
        1
        >>> instant('2014-2').month
        2
        >>> instant('2014-2-3').month
        2
        """
        return self[1]

    def period(self, unit, size = 1):
        """Create a new period starting at instant.

        >>> instant(2014).period('month')
        Period(('month', Instant((2014, 1, 1)), 1))
        >>> instant('2014-2').period('year', 2)
        Period(('year', Instant((2014, 2, 1)), 2))
        >>> instant('2014-2-3').period('day', size = 2)
        Period(('day', Instant((2014, 2, 3)), 2))
        """
        assert unit in (DAY, MONTH, YEAR), 'Invalid unit: {} of type {}'.format(unit, type(unit))
        assert isinstance(size, int) and size >= 1, 'Invalid size: {} of type {}'.format(size, type(size))
        return Period((unit, self, size))

    def offset(self, offset, unit):
        """Increment (or decrement) the given instant with offset units.

        >>> instant(2014).offset(1, 'day')
        Instant((2014, 1, 2))
        >>> instant(2014).offset(1, 'month')
        Instant((2014, 2, 1))
        >>> instant(2014).offset(1, 'year')
        Instant((2015, 1, 1))

        >>> instant('2014-1-31').offset(1, 'day')
        Instant((2014, 2, 1))
        >>> instant('2014-1-31').offset(1, 'month')
        Instant((2014, 2, 28))
        >>> instant('2014-1-31').offset(1, 'year')
        Instant((2015, 1, 31))

        >>> instant('2011-2-28').offset(1, 'day')
        Instant((2011, 3, 1))
        >>> instant('2011-2-28').offset(1, 'month')
        Instant((2011, 3, 28))
        >>> instant('2012-2-29').offset(1, 'year')
        Instant((2013, 2, 28))

        >>> instant(2014).offset(-1, 'day')
        Instant((2013, 12, 31))
        >>> instant(2014).offset(-1, 'month')
        Instant((2013, 12, 1))
        >>> instant(2014).offset(-1, 'year')
        Instant((2013, 1, 1))

        >>> instant('2011-3-1').offset(-1, 'day')
        Instant((2011, 2, 28))
        >>> instant('2011-3-31').offset(-1, 'month')
        Instant((2011, 2, 28))
        >>> instant('2012-2-29').offset(-1, 'year')
        Instant((2011, 2, 28))

        >>> instant('2014-1-30').offset(3, 'day')
        Instant((2014, 2, 2))
        >>> instant('2014-10-2').offset(3, 'month')
        Instant((2015, 1, 2))
        >>> instant('2014-1-1').offset(3, 'year')
        Instant((2017, 1, 1))

        >>> instant(2014).offset(-3, 'day')
        Instant((2013, 12, 29))
        >>> instant(2014).offset(-3, 'month')
        Instant((2013, 10, 1))
        >>> instant(2014).offset(-3, 'year')
        Instant((2011, 1, 1))

        >>> instant(2014).offset('first-of', 'month')
        Instant((2014, 1, 1))
        >>> instant('2014-2').offset('first-of', 'month')
        Instant((2014, 2, 1))
        >>> instant('2014-2-3').offset('first-of', 'month')
        Instant((2014, 2, 1))

        >>> instant(2014).offset('first-of', 'year')
        Instant((2014, 1, 1))
        >>> instant('2014-2').offset('first-of', 'year')
        Instant((2014, 1, 1))
        >>> instant('2014-2-3').offset('first-of', 'year')
        Instant((2014, 1, 1))

        >>> instant(2014).offset('last-of', 'month')
        Instant((2014, 1, 31))
        >>> instant('2014-2').offset('last-of', 'month')
        Instant((2014, 2, 28))
        >>> instant('2012-2-3').offset('last-of', 'month')
        Instant((2012, 2, 29))

        >>> instant(2014).offset('last-of', 'year')
        Instant((2014, 12, 31))
        >>> instant('2014-2').offset('last-of', 'year')
        Instant((2014, 12, 31))
        >>> instant('2014-2-3').offset('last-of', 'year')
        Instant((2014, 12, 31))
        """
        year, month, day = self
        assert unit in (DAY, MONTH, YEAR), 'Invalid unit: {} of type {}'.format(unit, type(unit))
        if offset == 'first-of':
            if unit == MONTH:
                day = 1
            elif unit == YEAR:
                month = 1
                day = 1
        elif offset == 'last-of':
            if unit == MONTH:
                day = calendar.monthrange(year, month)[1]
            elif unit == YEAR:
                month = 12
                day = 31
        else:
            assert isinstance(offset, int), 'Invalid offset: {} of type {}'.format(offset, type(offset))
            if unit == DAY:
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
            elif unit == MONTH:
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
            elif unit == YEAR:
                year += offset
                # Handle february month of leap year.
                month_last_day = calendar.monthrange(year, month)[1]
                if day > month_last_day:
                    day = month_last_day

        return self.__class__((year, month, day))

    @property
    def year(self):
        """Extract year from instant.

        >>> instant(2014).year
        2014
        >>> instant('2014-2').year
        2014
        >>> instant('2014-2-3').year
        2014
        """
        return self[0]


class Period(tuple):
    def __repr__(self):
        """Transform period to to its Python representation as a string.

        >>> repr(period('year', 2014))
        "Period(('year', Instant((2014, 1, 1)), 1))"
        >>> repr(period('month', '2014-2'))
        "Period(('month', Instant((2014, 2, 1)), 1))"
        >>> repr(period('day', '2014-2-3'))
        "Period(('day', Instant((2014, 2, 3)), 1))"
        """
        return '{}({})'.format(self.__class__.__name__, super(Period, self).__repr__())

    def __str__(self):
        """Transform period to a string.

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
        if unit == ETERNITY:
            return 'ETERNITY'
        year, month, day = start_instant

        # 1 year long period
        if (unit == MONTH and size == 12 or unit == YEAR and size == 1):
            if month == 1:
                # civil year starting from january
                return str(year)
            else:
                # rolling year
                return '{}:{}-{:02d}'.format(YEAR, year, month)
        # simple month
        if unit == MONTH and size == 1:
            return '{}-{:02d}'.format(year, month)
        # several civil years
        if unit == YEAR and month == 1:
            return '{}:{}:{}'.format(unit, year, size)

        if unit == DAY:
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
        """Count the number of days in period.

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
                'year',
                intersection_start,
                intersection_stop.year - intersection_start.year + 1,
                ))
        if intersection_start.day == 1 and intersection_stop.day == calendar.monthrange(intersection_stop.year,
                intersection_stop.month)[1]:
            return self.__class__((
                'month',
                intersection_start,
                (
                    (intersection_stop.year - intersection_start.year) * 12
                    + intersection_stop.month
                    - intersection_start.month
                    + 1
                    ),
                ))
        return self.__class__((
            'day',
            intersection_start,
            (intersection_stop.date - intersection_start.date).days + 1,
            ))

    def get_subperiods(self, unit):
        """
            Return the list of all the periods of unit ``unit`` contained in self.

            Examples:

            >>> period('2017').get_subperiods(MONTH)
            >>> [period('2017-01'), period('2017-02'), ... period('2017-12')]

            >>> period('year:2014:2').get_subperiods(YEAR)
            >>> [period('2014'), period('2015')]
        """
        if unit_weight(self.unit) < unit_weight(unit):
            raise ValueError('Cannot subdivide {0} into {1}'.format(self.unit, unit))

        if unit == YEAR:
            return [self.this_year.offset(i, YEAR) for i in range(self.size)]

        if unit == MONTH:
            return [self.first_month.offset(i, MONTH) for i in range(self.size_in_months)]

        if unit == DAY:
            return [self.first_day.offset(i, DAY) for i in range(self.size_in_days)]

    def offset(self, offset, unit = None):
        """Increment (or decrement) the given period with offset units.

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
        return self.__class__((self[0], self[1].offset(offset, self[0] if unit is None else unit), self[2]))

    def contains(self, other):
        """
            Returns ``True`` if the period contains ``other``. For instance, ``period(2015)`` contains ``period(2015-01)``
        """
        if not isinstance(other, Period):
            other = period(other)
        return self.start <= other.start and self.stop >= other.stop

    @property
    def size(self):
        """Return the size of the period.

        >>> period('month', '2012-2-29', 4).size
        4
        """
        return self[2]

    @property
    def size_in_months(self):
        """Return the size of the period in months.

        >>> period('month', '2012-2-29', 4).size_in_months
        4
        >>> period('year', '2012', 1).size_in_months
        12
        """
        if (self[0] == MONTH):
            return self[2]
        if(self[0] == YEAR):
            return self[2] * 12
        raise ValueError("Cannot calculate number of months in {0}".format(self[0]))

    @property
    def size_in_days(self):
        """Return the size of the period in days.

        >>> period('month', '2012-2-29', 4).size_in_days
        28
        >>> period('year', '2012', 1).size_in_days
        366
        """
        unit, instant, length = self

        if unit == DAY:
            return length
        if unit in [MONTH, YEAR]:
            last_day = self.start.offset(length, unit).offset(-1, DAY)
            return (last_day.date - self.start.date).days + 1

        raise ValueError("Cannot calculate number of days in {0}".format(unit))

    @property
    def start(self):
        """Return the first day of the period as an Instant instance.

        >>> period('month', '2012-2-29', 4).start
        Instant((2012, 2, 29))
        """
        return self[1]

    @property
    def stop(self):
        """Return the last day of the period as an Instant instance.

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
        if unit == ETERNITY:
            return Instant((float("inf"), float("inf"), float("inf")))
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
            if unit == 'month':
                month += size
                while month > 12:
                    year += 1
                    month -= 12
            else:
                assert unit == 'year', 'Invalid unit: {} of type {}'.format(unit, type(unit))
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
        return self.first_month.start.period('month', 3).offset(-3)

    @property
    def last_month(self):
        return self.first_month.offset(-1)

    @property
    def last_year(self):
        return self.start.offset('first-of', 'year').period('year').offset(-1)

    @property
    def n_2(self):
        return self.start.offset('first-of', 'year').period('year').offset(-2)

    @property
    def this_year(self):
        return self.start.offset('first-of', 'year').period('year')

    @property
    def first_month(self):
        return self.start.offset('first-of', 'month').period('month')

    @property
    def first_day(self):
        return self.start.period('day')


def instant(instant):
    """Return a new instant, aka a triple of integers (year, month, day).

    >>> instant(2014)
    Instant((2014, 1, 1))
    >>> instant('2014')
    Instant((2014, 1, 1))
    >>> instant('2014-02')
    Instant((2014, 2, 1))
    >>> instant('2014-3-2')
    Instant((2014, 3, 2))
    >>> instant(instant('2014-3-2'))
    Instant((2014, 3, 2))
    >>> instant(period('month', '2014-3-2'))
    Instant((2014, 3, 2))

    >>> instant(None)
    """
    if instant is None:
        return None
    if isinstance(instant, Instant):
        return instant
    if isinstance(instant, str):
        if not INSTANT_PATTERN.match(instant):
            raise ValueError("'{}' is not a valid instant. Instants are described using the 'YYYY-MM-DD' format, for instance '2015-06-15'.".format(instant).encode('utf-8'))
        instant = Instant(
            int(fragment)
            for fragment in instant.split('-', 2)[:3]
            )
    elif isinstance(instant, datetime.date):
        instant = Instant((instant.year, instant.month, instant.day))
    elif isinstance(instant, int):
        instant = (instant,)
    elif isinstance(instant, list):
        assert 1 <= len(instant) <= 3
        instant = tuple(instant)
    elif isinstance(instant, Period):
        instant = instant.start
    else:
        assert isinstance(instant, tuple), instant
        assert 1 <= len(instant) <= 3
    if len(instant) == 1:
        return Instant((instant[0], 1, 1))
    if len(instant) == 2:
        return Instant((instant[0], instant[1], 1))
    return Instant(instant)


def instant_date(instant):
    if instant is None:
        return None
    instant_date = date_by_instant_cache.get(instant)
    if instant_date is None:
        date_by_instant_cache[instant] = instant_date = datetime.date(*instant)
    return instant_date


def period(value):
    """Return a new period, aka a triple (unit, start_instant, size).

    >>> period('2014')
    Period((YEAR, Instant((2014, 1, 1)), 1))
    >>> period('year:2014')
    Period((YEAR, Instant((2014, 1, 1)), 1))

    >>> period('2014-2')
    Period((MONTH, Instant((2014, 2, 1)), 1))
    >>> period('2014-02')
    Period((MONTH, Instant((2014, 2, 1)), 1))
    >>> period('month:2014-2')
    Period((MONTH, Instant((2014, 2, 1)), 1))

    >>> period('year:2014-2')
    Period((YEAR, Instant((2014, 2, 1)), 1))
    """
    if isinstance(value, Period):
        return value

    if isinstance(value, Instant):
        return Period((DAY, value, 1))

    def parse_simple_period(value):
        """
        Parses simple periods respecting the ISO format, such as 2012 or 2015-03
        """
        try:
            date = datetime.datetime.strptime(value, '%Y')
        except ValueError:
            try:
                date = datetime.datetime.strptime(value, '%Y-%m')
            except ValueError:
                try:
                    date = datetime.datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    return None
                else:
                    return Period((DAY, Instant((date.year, date.month, date.day)), 1))
            else:
                return Period((MONTH, Instant((date.year, date.month, 1)), 1))
        else:
            return Period((YEAR, Instant((date.year, date.month, 1)), 1))

    def raise_error(value):
        message = linesep.join([
            "Expected a period (eg. '2017', '2017-01', '2017-01-01', ...); got: '{}'.".format(value),
            "Learn more about legal period formats in OpenFisca:",
            "<https://openfisca.org/doc/coding-the-legislation/35_periods.html#periods-in-simulations>."
            ]).encode('utf-8')
        raise ValueError(message)

    if value == 'ETERNITY' or value == ETERNITY:
        return Period(('eternity', instant(datetime.date.min), float("inf")))

    # check the type
    if isinstance(value, int):
        return Period((YEAR, Instant((value, 1, 1)), 1))
    if not isinstance(value, str):
        raise_error(value)

    # try to parse as a simple period
    period = parse_simple_period(value)
    if period is not None:
        return period

    # complex period must have a ':' in their strings
    if ":" not in value:
        raise_error(value)

    components = value.split(':')

    # left-most component must be a valid unit
    unit = components[0]
    if unit not in (DAY, MONTH, YEAR):
        raise_error(value)

    # middle component must be a valid iso period
    base_period = parse_simple_period(components[1])
    if not base_period:
        raise_error(value)

    # period like year:2015-03 have a size of 1
    if len(components) == 2:
        size = 1
    # if provided, make sure the size is an integer
    elif len(components) == 3:
        try:
            size = int(components[2])
        except ValueError:
            raise_error(value)
    # if there is more than 2 ":" in the string, the period is invalid
    else:
        raise_error(value)

    # reject ambiguous period such as month:2014
    if unit_weight(base_period.unit) > unit_weight(unit):
        raise_error(value)

    return Period((unit, base_period.start, size))


def key_period_size(period):
    """
    Defines a key in order to sort periods by length. It uses two aspects : first unit then size

    :param period: an OpenFisca period
    :return: a string

    >>> key_period_size(period('2014'))
    '2_1'
    >>> key_period_size(period('2013'))
    '2_1'
    >>> key_period_size(period('2014-01'))
    '1_1'

    """

    unit, start, size = period

    return '{}_{}'.format(unit_weight(unit), size)


def unit_weights():
    return {
        DAY: 100,
        MONTH: 200,
        YEAR: 300,
        ETERNITY: 400,
        }


def unit_weight(unit):
    return unit_weights()[unit]
