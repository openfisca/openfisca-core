# -*- coding: utf-8 -*-


"""Toolbox to handle date intervals

A period is a triple (unit, start, size), where unit is either "month" or "year", where start format is a
(year, month, day) triple, and where size is an integer > 1.

Since a period is a triple it can be used as a dictionary key.
"""


import calendar
import collections
import datetime
import re

from . import conv


MONTH = u'month'
YEAR = u'year'
ETERNITY = u'eternity'


def N_(message):
    return message


# Note: weak references are not used, because Python 2.7 can't create weak reference to 'datetime.date' objects.
date_by_instant_cache = {}
str_by_instant_cache = {}
year_or_month_or_day_re = re.compile(ur'(18|19|20)\d{2}(-(0?[1-9]|1[0-2])(-([0-2]?\d|3[0-1]))?)?$')


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

        >>> unicode(instant(2014))
        u'2014-01-01'
        >>> unicode(instant('2014-2'))
        u'2014-02-01'
        >>> unicode(instant('2014-2-3'))
        u'2014-02-03'
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
        Period((u'month', Instant((2014, 1, 1)), 1))
        >>> instant('2014-2').period('year', 2)
        Period((u'year', Instant((2014, 2, 1)), 2))
        >>> instant('2014-2-3').period('day', size = 2)
        Period((u'day', Instant((2014, 2, 3)), 2))
        """
        assert unit in (u'day', u'month', u'year'), 'Invalid unit: {} of type {}'.format(unit, type(unit))
        assert isinstance(size, int) and size >= 1, 'Invalid size: {} of type {}'.format(size, type(size))
        return Period((unicode(unit), self, size))

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
            if unit == u'month':
                day = 1
            else:
                assert unit == u'year', 'Invalid unit: {} of type {}'.format(unit, type(unit))
                month = 1
                day = 1
        elif offset == 'last-of':
            if unit == u'month':
                day = calendar.monthrange(year, month)[1]
            else:
                assert unit == u'year', 'Invalid unit: {} of type {}'.format(unit, type(unit))
                month = 12
                day = 31
        else:
            assert isinstance(offset, int), 'Invalid offset: {} of type {}'.format(offset, type(offset))
            if unit == u'day':
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
            elif unit == u'month':
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
                assert unit == u'year', 'Invalid unit: {} of type {}'.format(unit, type(unit))
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
        "Period((u'year', Instant((2014, 1, 1)), 1))"
        >>> repr(period('month', '2014-2'))
        "Period((u'month', Instant((2014, 2, 1)), 1))"
        >>> repr(period('day', '2014-2-3'))
        "Period((u'day', Instant((2014, 2, 3)), 1))"
        """
        return '{}({})'.format(self.__class__.__name__, super(Period, self).__repr__())

    def __str__(self):
        """Transform period to a string.

        >>> unicode(period(YEAR, 2014))
        u'2014'

        >>> unicode(period(YEAR, '2014-2'))
        u'year:2014-02'
        >>> unicode(period(MONTH, '2014-2'))
        u'2014-02'

        >>> unicode(period(YEAR, 2012, size = 2))
        u'year:2012:2'
        >>> unicode(period(MONTH, 2012, size = 2))
        u'month:2012-01:2'
        >>> unicode(period(MONTH, 2012, size = 12))
        u'2012'

        >>> unicode(period(YEAR, '2012-3', size = 2))
        u'year:2012-03:2'
        >>> unicode(period(MONTH, '2012-3', size = 2))
        u'month:2012-03:2'
        >>> unicode(period(MONTH, '2012-3', size = 12))
        u'year:2012-03'
        """

        unit, start_instant, size = self
        start_instant = start_instant[:2]  # we always ignore the day, 1 by construction
        year, month = start_instant

        # 1 year long period
        if (unit == MONTH and size == 12 or unit == YEAR and size == 1):
            if month == 1:
                # civil year starting from january
                return unicode(year)
            else:
                # rolling year
                return u'{}:{}-{:02d}'.format(YEAR, year, month)
        # simple month
        if unit == MONTH and size == 1:
            return u'{}-{:02d}'.format(year, month)
        # several civil years
        if unit == YEAR and month == 1:
            return u'{}:{}:{}'.format(unit, year, size)

        # complex period
        return u'{}:{}-{:02d}:{}'.format(unit, year, month, size)

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
                u'year',
                intersection_start,
                intersection_stop.year - intersection_start.year + 1,
                ))
        if intersection_start.day == 1 and intersection_stop.day == calendar.monthrange(intersection_stop.year,
                intersection_stop.month)[1]:
            return self.__class__((
                u'month',
                intersection_start,
                ((intersection_stop.year - intersection_start.year) * 12 + intersection_stop.month -
                    intersection_start.month + 1),
                ))
        return self.__class__((
            u'day',
            intersection_start,
            (intersection_stop.date - intersection_start.date).days + 1,
            ))

    def offset(self, offset, unit = None):
        """Increment (or decrement) the given period with offset units.

        >>> period('day', 2014).offset(1)
        Period((u'day', Instant((2014, 1, 2)), 365))
        >>> period('day', 2014).offset(1, 'day')
        Period((u'day', Instant((2014, 1, 2)), 365))
        >>> period('day', 2014).offset(1, 'month')
        Period((u'day', Instant((2014, 2, 1)), 365))
        >>> period('day', 2014).offset(1, 'year')
        Period((u'day', Instant((2015, 1, 1)), 365))

        >>> period('month', 2014).offset(1)
        Period((u'month', Instant((2014, 2, 1)), 12))
        >>> period('month', 2014).offset(1, 'day')
        Period((u'month', Instant((2014, 1, 2)), 12))
        >>> period('month', 2014).offset(1, 'month')
        Period((u'month', Instant((2014, 2, 1)), 12))
        >>> period('month', 2014).offset(1, 'year')
        Period((u'month', Instant((2015, 1, 1)), 12))

        >>> period('year', 2014).offset(1)
        Period((u'year', Instant((2015, 1, 1)), 1))
        >>> period('year', 2014).offset(1, 'day')
        Period((u'year', Instant((2014, 1, 2)), 1))
        >>> period('year', 2014).offset(1, 'month')
        Period((u'year', Instant((2014, 2, 1)), 1))
        >>> period('year', 2014).offset(1, 'year')
        Period((u'year', Instant((2015, 1, 1)), 1))

        >>> period('day', '2011-2-28').offset(1)
        Period((u'day', Instant((2011, 3, 1)), 1))
        >>> period('month', '2011-2-28').offset(1)
        Period((u'month', Instant((2011, 3, 28)), 1))
        >>> period('year', '2011-2-28').offset(1)
        Period((u'year', Instant((2012, 2, 28)), 1))

        >>> period('day', '2011-3-1').offset(-1)
        Period((u'day', Instant((2011, 2, 28)), 1))
        >>> period('month', '2011-3-1').offset(-1)
        Period((u'month', Instant((2011, 2, 1)), 1))
        >>> period('year', '2011-3-1').offset(-1)
        Period((u'year', Instant((2010, 3, 1)), 1))

        >>> period('day', '2014-1-30').offset(3)
        Period((u'day', Instant((2014, 2, 2)), 1))
        >>> period('month', '2014-1-30').offset(3)
        Period((u'month', Instant((2014, 4, 30)), 1))
        >>> period('year', '2014-1-30').offset(3)
        Period((u'year', Instant((2017, 1, 30)), 1))

        >>> period('day', 2014).offset(-3)
        Period((u'day', Instant((2013, 12, 29)), 365))
        >>> period('month', 2014).offset(-3)
        Period((u'month', Instant((2013, 10, 1)), 12))
        >>> period('year', 2014).offset(-3)
        Period((u'year', Instant((2011, 1, 1)), 1))

        >>> period('day', '2014-2-3').offset('first-of', 'month')
        Period((u'day', Instant((2014, 2, 1)), 1))
        >>> period('day', '2014-2-3').offset('first-of', 'year')
        Period((u'day', Instant((2014, 1, 1)), 1))

        >>> period('day', '2014-2-3', 4).offset('first-of', 'month')
        Period((u'day', Instant((2014, 2, 1)), 4))
        >>> period('day', '2014-2-3', 4).offset('first-of', 'year')
        Period((u'day', Instant((2014, 1, 1)), 4))

        >>> period('month', '2014-2-3').offset('first-of')
        Period((u'month', Instant((2014, 2, 1)), 1))
        >>> period('month', '2014-2-3').offset('first-of', 'month')
        Period((u'month', Instant((2014, 2, 1)), 1))
        >>> period('month', '2014-2-3').offset('first-of', 'year')
        Period((u'month', Instant((2014, 1, 1)), 1))

        >>> period('month', '2014-2-3', 4).offset('first-of')
        Period((u'month', Instant((2014, 2, 1)), 4))
        >>> period('month', '2014-2-3', 4).offset('first-of', 'month')
        Period((u'month', Instant((2014, 2, 1)), 4))
        >>> period('month', '2014-2-3', 4).offset('first-of', 'year')
        Period((u'month', Instant((2014, 1, 1)), 4))

        >>> period('year', 2014).offset('first-of')
        Period((u'year', Instant((2014, 1, 1)), 1))
        >>> period('year', 2014).offset('first-of', 'month')
        Period((u'year', Instant((2014, 1, 1)), 1))
        >>> period('year', 2014).offset('first-of', 'year')
        Period((u'year', Instant((2014, 1, 1)), 1))

        >>> period('year', '2014-2-3').offset('first-of')
        Period((u'year', Instant((2014, 1, 1)), 1))
        >>> period('year', '2014-2-3').offset('first-of', 'month')
        Period((u'year', Instant((2014, 2, 1)), 1))
        >>> period('year', '2014-2-3').offset('first-of', 'year')
        Period((u'year', Instant((2014, 1, 1)), 1))

        >>> period('day', '2014-2-3').offset('last-of', 'month')
        Period((u'day', Instant((2014, 2, 28)), 1))
        >>> period('day', '2014-2-3').offset('last-of', 'year')
        Period((u'day', Instant((2014, 12, 31)), 1))

        >>> period('day', '2014-2-3', 4).offset('last-of', 'month')
        Period((u'day', Instant((2014, 2, 28)), 4))
        >>> period('day', '2014-2-3', 4).offset('last-of', 'year')
        Period((u'day', Instant((2014, 12, 31)), 4))

        >>> period('month', '2014-2-3').offset('last-of')
        Period((u'month', Instant((2014, 2, 28)), 1))
        >>> period('month', '2014-2-3').offset('last-of', 'month')
        Period((u'month', Instant((2014, 2, 28)), 1))
        >>> period('month', '2014-2-3').offset('last-of', 'year')
        Period((u'month', Instant((2014, 12, 31)), 1))

        >>> period('month', '2014-2-3', 4).offset('last-of')
        Period((u'month', Instant((2014, 2, 28)), 4))
        >>> period('month', '2014-2-3', 4).offset('last-of', 'month')
        Period((u'month', Instant((2014, 2, 28)), 4))
        >>> period('month', '2014-2-3', 4).offset('last-of', 'year')
        Period((u'month', Instant((2014, 12, 31)), 4))

        >>> period('year', 2014).offset('last-of')
        Period((u'year', Instant((2014, 12, 31)), 1))
        >>> period('year', 2014).offset('last-of', 'month')
        Period((u'year', Instant((2014, 1, 31)), 1))
        >>> period('year', 2014).offset('last-of', 'year')
        Period((u'year', Instant((2014, 12, 31)), 1))

        >>> period('year', '2014-2-3').offset('last-of')
        Period((u'year', Instant((2014, 12, 31)), 1))
        >>> period('year', '2014-2-3').offset('last-of', 'month')
        Period((u'year', Instant((2014, 2, 28)), 1))
        >>> period('year', '2014-2-3').offset('last-of', 'year')
        Period((u'year', Instant((2014, 12, 31)), 1))
        """
        return self.__class__((self[0], self[1].offset(offset, self[0] if unit is None else unit), self[2]))

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
        if unit == u'day':
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
            if unit == u'month':
                month += size
                while month > 12:
                    year += 1
                    month -= 12
            else:
                assert unit == u'year', 'Invalid unit: {} of type {}'.format(unit, type(unit))
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
        return collections.OrderedDict((
            ('unit', self[0]),
            ('start', unicode(self[1])),
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
    >>> instant(u'2014')
    Instant((2014, 1, 1))
    >>> instant(u'2014-02')
    Instant((2014, 2, 1))
    >>> instant(u'2014-3-2')
    Instant((2014, 3, 2))
    >>> instant(instant(u'2014-3-2'))
    Instant((2014, 3, 2))
    >>> instant(period('month', u'2014-3-2'))
    Instant((2014, 3, 2))

    >>> instant(None)
    """
    if instant is None:
        return None
    if isinstance(instant, basestring):
        instant = Instant(
            int(fragment)
            for fragment in instant.split(u'-', 2)[:3]
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

    >>> period(u'2014')
    Period((YEAR, Instant((2014, 1, 1)), 1))
    >>> period(u'year:2014')
    Period((YEAR, Instant((2014, 1, 1)), 1))

    >>> period(u'2014-2')
    Period((MONTH, Instant((2014, 2, 1)), 1))
    >>> period(u'2014-02')
    Period((MONTH, Instant((2014, 2, 1)), 1))
    >>> period(u'month:2014-2')
    Period((MONTH, Instant((2014, 2, 1)), 1))

    >>> period(u'year:2014-2')
    Period((YEAR, Instant((2014, 2, 1)), 1))
    """

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
        raise ValueError(u"Invalid period {}".format(value).encode('utf-8'))

    # check the type
    if isinstance(value, int):
        return Period((YEAR, Instant((value, 1, 1)), 1))
    if isinstance(value, Period):
        return value
    if not isinstance(value, basestring):
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


def compare_period_size(a, b):
    unit_a, start_a, size_a = a
    unit_b, start_b, size_b = b

    if (unit_a is ETERNITY) or (unit_b is ETERNITY):
        raise ValueError('ETERNITY cannot be compared to another period.')

    if unit_a != unit_b:
        unit_weights = {
            u'day': 1,
            u'month': 2,
            u'year': 3,
            }

        return cmp(unit_weights[unit_a], unit_weights[unit_b])

    return cmp(size_a, size_b)


def compare_period_start(a, b):
    unit_a, start_a, size_a = a
    unit_b, start_b, size_b = b

    return cmp(start_a, start_b)


# Level-1 converters


def input_to_period_tuple(value, state = None):
    """Convert an input string to a period tuple.

    .. note:: This function doesn't return a period, but a tuple that allows to construct a period.

    >>> input_to_period_tuple(u'2014')
    ((u'year', 2014), None)
    >>> input_to_period_tuple(u'2014:2')
    ((u'year', 2014, 2), None)
    >>> input_to_period_tuple(u'2014-2')
    ((u'month', (2014, 2)), None)
    >>> input_to_period_tuple(u'2014-3:12')
    ((u'month', (2014, 3), 12), None)
    >>> input_to_period_tuple(u'2014-2-3')
    ((u'day', (2014, 2, 3)), None)
    >>> input_to_period_tuple(u'2014-3-4:2')
    ((u'day', (2014, 3, 4), 2), None)

    >>> input_to_period_tuple(u'year:2014')
    ((u'year', u'2014'), None)
    >>> input_to_period_tuple(u'year:2014:2')
    ((u'year', u'2014', u'2'), None)
    >>> input_to_period_tuple(u'year:2014-2:2')
    ((u'year', u'2014-2', u'2'), None)
    """
    if value is None:
        return value, None
    if state is None:
        state = conv.default_state
    split_value = tuple(
        clean_fragment
        for clean_fragment in (
            fragment.strip()
            for fragment in value.split(u':')
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
                for fragment in split_value[0].split(u'-')
                )
            if clean_fragment
            )
        if len(split_value) == 1:
            return conv.pipe(
                conv.input_to_strict_int,
                conv.test_greater_or_equal(0),
                conv.function(lambda year: (u'year', year)),
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
                conv.function(lambda month_tuple: (u'month', month_tuple)),
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
                conv.function(lambda day_tuple: (u'day', day_tuple)),
                )(split_value, state = state)
        return split_value, state._(u'Instant string contains too much "-" for a year, a month or a day')
    if len(split_value) == 2:
        split_start = tuple(
            clean_fragment
            for clean_fragment in (
                fragment.strip()
                for fragment in split_value[0].split(u'-')
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
                    return (u'year', start, size), None
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
                    return (u'month', start, size), None
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
                    return (u'day', start, size), None
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

    if isinstance(value, basestring):
        if year_or_month_or_day_re.match(value) is None:
            return value, state._(u'Invalid date string')
        instant = tuple(
            int(fragment)
            for fragment in value.split(u'-', 2)
            )
    elif isinstance(value, datetime.date):
        instant = (value.year, value.month, value.day)
    elif isinstance(value, int):
        instant = (value,)
    elif isinstance(value, list):
        if not (1 <= len(value) <= 3):
            return value, state._(u'Invalid size for date list')
        instant = tuple(value)
    else:
        if not isinstance(value, tuple):
            return value, state._(u'Invalid type')
        if not (1 <= len(value) <= 3):
            return value, state._(u'Invalid size for date tuple')
        instant = value

    return instant, None
