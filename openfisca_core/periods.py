# -*- coding: utf-8 -*-


"""Toolbox to handle date intervals

A period is a triple (unit, start, size), where unit is either "month" or "year", where start format is a
(year, month, day) triple, and where size is an integer > 1.

Since a period is a triple it can be used as a dictionary key.
"""

from __future__ import unicode_literals, print_function, division, absolute_import
from builtins import str

import calendar
import collections
import datetime
import re
from os import linesep

from openfisca_core import conv
from openfisca_core.commons import basestring_type, to_unicode


MONTH = 'month'
YEAR = 'year'
ETERNITY = 'eternity'

INSTANT_PATTERN = re.compile('^\d{4}(?:-\d{1,2}){0,2}$')  # matches '2015', '2015-01', '2015-01'


def N_(message):
    return message


# Note: weak references are not used, because Python 2.7 can't create weak reference to 'datetime.date' objects.
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

        >>> to_unicode(instant(2014))
        '2014-01-01'
        >>> to_unicode(instant('2014-2'))
        '2014-02-01'
        >>> to_unicode(instant('2014-2-3'))
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
        assert unit in ('day', 'month', 'year'), 'Invalid unit: {} of type {}'.format(unit, type(unit))
        assert isinstance(size, int) and size >= 1, 'Invalid size: {} of type {}'.format(size, type(size))
        return Period((to_unicode(unit), self, size))

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
        if offset == 'first-of':
            if unit == 'month':
                day = 1
            else:
                assert unit == 'year', 'Invalid unit: {} of type {}'.format(unit, type(unit))
                month = 1
                day = 1
        elif offset == 'last-of':
            if unit == 'month':
                day = calendar.monthrange(year, month)[1]
            else:
                assert unit == 'year', 'Invalid unit: {} of type {}'.format(unit, type(unit))
                month = 12
                day = 31
        else:
            assert isinstance(offset, int), 'Invalid offset: {} of type {}'.format(offset, type(offset))
            if unit == 'day':
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
            elif unit == 'month':
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
            else:
                assert unit == 'year', 'Invalid unit: {} of type {}'.format(unit, type(unit))
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

        >>> to_unicode(period(YEAR, 2014))
        '2014'

        >>> to_unicode(period(YEAR, '2014-2'))
        'year:2014-02'
        >>> to_unicode(period(MONTH, '2014-2'))
        '2014-02'

        >>> to_unicode(period(YEAR, 2012, size = 2))
        'year:2012:2'
        >>> to_unicode(period(MONTH, 2012, size = 2))
        'month:2012-01:2'
        >>> to_unicode(period(MONTH, 2012, size = 12))
        '2012'

        >>> to_unicode(period(YEAR, '2012-3', size = 2))
        'year:2012-03:2'
        >>> to_unicode(period(MONTH, '2012-3', size = 2))
        'month:2012-03:2'
        >>> to_unicode(period(MONTH, '2012-3', size = 12))
        'year:2012-03'
        """

        unit, start_instant, size = self
        if unit == ETERNITY:
            return 'ETERNITY'
        start_instant = start_instant[:2]  # we always ignore the day, 1 by construction
        year, month = start_instant

        # 1 year long period
        if (unit == MONTH and size == 12 or unit == YEAR and size == 1):
            if month == 1:
                # civil year starting from january
                return to_unicode(year)
            else:
                # rolling year
                return '{}:{}-{:02d}'.format(YEAR, year, month)
        # simple month
        if unit == MONTH and size == 1:
            return '{}-{:02d}'.format(year, month)
        # several civil years
        if unit == YEAR and month == 1:
            return '{}:{}:{}'.format(unit, year, size)

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
        if self.unit == MONTH and unit == YEAR:
            raise ValueError('Cannot subdivise months into years')
        if self.unit == YEAR and unit == YEAR:
            return [self.this_year.offset(i, YEAR) for i in range(self.size)]

        return [self.first_month.offset(i, MONTH) for i in range(self.size_in_months)]

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
        else:
            return self[2] * 12

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

    def to_json_dict(self):
        if not isinstance(self[1], str):
            self[1] = to_unicode(self[1])
        return collections.OrderedDict((
            ('unit', self[0]),
            ('start', self[1]),
            ('size', self[2]),
            ))

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
    if isinstance(instant, basestring_type):
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
                return None
            else:
                return Period((MONTH, Instant((date.year, date.month, 1)), 1))
        else:
            return Period((YEAR, Instant((date.year, date.month, 1)), 1))

    def raise_error(value):
        message = linesep.join([
            "Expected a period (eg. '2017', '2017-01', ...); got: '{}'.".format(value),
            "Learn more about legal period formats in OpenFisca:",
            "<http://openfisca.org/doc/periodsinstants.html#api>."
            ]).encode('utf-8')
        raise ValueError(message)

    if value == 'ETERNITY' or value == ETERNITY:
        return Period(('eternity', instant(datetime.date.min), float("inf")))

    # check the type
    if isinstance(value, int):
        return Period((YEAR, Instant((value, 1, 1)), 1))
    if not isinstance(value, basestring_type):
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
    if unit not in (MONTH, YEAR):
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
    if base_period.unit == YEAR and unit == MONTH:
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

    unit_weights = {
        MONTH: 1,
        YEAR: 2,
        ETERNITY: 3,
        }

    unit, start, size = period

    return '{}_{}'.format(unit_weights[unit], size)


# Level-1 converters


def input_to_period_tuple(value, state = None):
    """Convert an input string to a period tuple.

    .. note:: This function doesn't return a period, but a tuple that allows to construct a period.

    >>> input_to_period_tuple('2014')
    (('year', 2014), None)
    >>> input_to_period_tuple('2014:2')
    (('year', 2014, 2), None)
    >>> input_to_period_tuple('2014-2')
    (('month', (2014, 2)), None)
    >>> input_to_period_tuple('2014-3:12')
    (('month', (2014, 3), 12), None)
    >>> input_to_period_tuple('2014-2-3')
    (('day', (2014, 2, 3)), None)
    >>> input_to_period_tuple('2014-3-4:2')
    (('day', (2014, 3, 4), 2), None)

    >>> input_to_period_tuple('year:2014')
    (('year', '2014'), None)
    >>> input_to_period_tuple('year:2014:2')
    (('year', '2014', '2'), None)
    >>> input_to_period_tuple('year:2014-2:2')
    (('year', '2014-2', '2'), None)
    """
    if value is None:
        return value, None
    if state is None:
        state = conv.default_state
    split_value = tuple(
        clean_fragment
        for clean_fragment in (
            fragment.strip()
            for fragment in value.split(':')
            )
        if clean_fragment
        )
    if not split_value:
        return None, None
    if len(split_value) == 1:
        split_value = tuple(
            clean_fragment
            for clean_fragment in (
                fragment.strip()
                for fragment in split_value[0].split('-')
                )
            if clean_fragment
            )
        if len(split_value) == 1:
            return conv.pipe(
                conv.input_to_strict_int,
                conv.test_greater_or_equal(0),
                conv.function(lambda year: ('year', year)),
                )(split_value[0], state = state)
        if len(split_value) == 2:
            return conv.pipe(
                conv.struct(
                    (
                        conv.pipe(
                            conv.input_to_strict_int,
                            conv.test_greater_or_equal(0),
                            ),
                        conv.pipe(
                            conv.input_to_strict_int,
                            conv.test_between(1, 12),
                            ),
                        ),
                    ),
                conv.function(lambda month_tuple: ('month', month_tuple)),
                )(split_value, state = state)
        if len(split_value) == 3:
            return conv.pipe(
                conv.struct(
                    (
                        conv.pipe(
                            conv.input_to_strict_int,
                            conv.test_greater_or_equal(0),
                            ),
                        conv.pipe(
                            conv.input_to_strict_int,
                            conv.test_between(1, 12),
                            ),
                        conv.pipe(
                            conv.input_to_strict_int,
                            conv.test_between(1, 31),
                            ),
                        ),
                    ),
                conv.function(lambda day_tuple: ('day', day_tuple)),
                )(split_value, state = state)
        return split_value, state._('Instant string contains too much "-" for a year, a month or a day')
    if len(split_value) == 2:
        split_start = tuple(
            clean_fragment
            for clean_fragment in (
                fragment.strip()
                for fragment in split_value[0].split('-')
                )
            if clean_fragment
            )
        size, error = conv.input_to_int(split_value[1], state = state)
        if error is None:
            if len(split_start) == 1:
                start, error = conv.pipe(
                    conv.input_to_strict_int,
                    conv.test_greater_or_equal(0),
                    )(split_start[0], state = state)
                if error is None:
                    return ('year', start, size), None
            elif len(split_start) == 2:
                start, error = conv.struct(
                    (
                        conv.pipe(
                            conv.input_to_strict_int,
                            conv.test_greater_or_equal(0),
                            ),
                        conv.pipe(
                            conv.input_to_strict_int,
                            conv.test_between(1, 12),
                            ),
                        ),
                    )(split_start, state = state)
                if error is None:
                    return ('month', start, size), None
            elif len(split_start) == 3:
                start, error = conv.struct(
                    (
                        conv.pipe(
                            conv.input_to_strict_int,
                            conv.test_greater_or_equal(0),
                            ),
                        conv.pipe(
                            conv.input_to_strict_int,
                            conv.test_between(1, 12),
                            ),
                        conv.pipe(
                            conv.input_to_strict_int,
                            conv.test_between(1, 31),
                            ),
                        ),
                    )(split_start, state = state)
                if error is None:
                    return ('day', start, size), None
    return split_value, None


def json_or_python_to_instant_tuple(value, state = None):
    """Convert a JSON or Python object to an instant tuple.

    .. note:: This function doesn't return an instant, but a tuple that allows to construct an instant.

    >>> json_or_python_to_instant_tuple('2014')
    ((2014,), None)
    >>> json_or_python_to_instant_tuple('2014-2')
    ((2014, 2), None)
    >>> json_or_python_to_instant_tuple('2014-2-3')
    ((2014, 2, 3), None)
    >>> json_or_python_to_instant_tuple(datetime.date(2014, 2, 3))
    ((2014, 2, 3), None)
    >>> json_or_python_to_instant_tuple([2014])
    ((2014,), None)
    >>> json_or_python_to_instant_tuple([2014, 2])
    ((2014, 2), None)
    >>> json_or_python_to_instant_tuple([2014, 2, 3])
    ((2014, 2, 3), None)
    >>> json_or_python_to_instant_tuple(2014)
    ((2014,), None)
    >>> json_or_python_to_instant_tuple((2014,))
    ((2014,), None)
    >>> json_or_python_to_instant_tuple((2014, 2))
    ((2014, 2), None)
    >>> json_or_python_to_instant_tuple((2014, 2, 3))
    ((2014, 2, 3), None)
    """
    if value is None:
        return value, None
    if state is None:
        state = conv.default_state

    if isinstance(value, basestring_type):
        if year_or_month_or_day_re.match(value) is None:
            return value, state._('Invalid date string')
        instant = tuple(
            int(fragment)
            for fragment in value.split('-', 2)
            )
    elif isinstance(value, datetime.date):
        instant = (value.year, value.month, value.day)
    elif isinstance(value, int):
        instant = (value,)
    elif isinstance(value, list):
        if not (1 <= len(value) <= 3):
            return value, state._('Invalid size for date list')
        instant = tuple(value)
    else:
        if not isinstance(value, tuple):
            return value, state._('Invalid type')
        if not (1 <= len(value) <= 3):
            return value, state._('Invalid size for date tuple')
        instant = value

    return instant, None
