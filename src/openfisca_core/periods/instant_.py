import calendar
import datetime

from openfisca_core import periods
from openfisca_core.periods import config


class Instant(tuple):

    def __repr__(self):
        """
        Transform instant to to its Python representation as a string.

        >>> repr(instant(2014))
        'Instant((2014, 1, 1))'
        >>> repr(instant('2014-2'))
        'Instant((2014, 2, 1))'
        >>> repr(instant('2014-2-3'))
        'Instant((2014, 2, 3))'
        """
        return '{}({})'.format(self.__class__.__name__, super(Instant, self).__repr__())

    def __str__(self):
        """
        Transform instant to a string.

        >>> str(instant(2014))
        '2014-01-01'
        >>> str(instant('2014-2'))
        '2014-02-01'
        >>> str(instant('2014-2-3'))
        '2014-02-03'

        """
        instant_str = config.str_by_instant_cache.get(self)
        if instant_str is None:
            config.str_by_instant_cache[self] = instant_str = self.date.isoformat()
        return instant_str

    @property
    def date(self):
        """
        Convert instant to a date.

        >>> instant(2014).date
        datetime.date(2014, 1, 1)
        >>> instant('2014-2').date
        datetime.date(2014, 2, 1)
        >>> instant('2014-2-3').date
        datetime.date(2014, 2, 3)
        """
        instant_date = config.date_by_instant_cache.get(self)
        if instant_date is None:
            config.date_by_instant_cache[self] = instant_date = datetime.date(*self)
        return instant_date

    @property
    def day(self):
        """
        Extract day from instant.

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
        """
        Extract month from instant.

        >>> instant(2014).month
        1
        >>> instant('2014-2').month
        2
        >>> instant('2014-2-3').month
        2
        """
        return self[1]

    def period(self, unit, size = 1):
        """
        Create a new period starting at instant.

        >>> instant(2014).period('month')
        Period(('month', Instant((2014, 1, 1)), 1))
        >>> instant('2014-2').period('year', 2)
        Period(('year', Instant((2014, 2, 1)), 2))
        >>> instant('2014-2-3').period('day', size = 2)
        Period(('day', Instant((2014, 2, 3)), 2))
        """
        assert unit in (config.DAY, config.MONTH, config.YEAR), 'Invalid unit: {} of type {}'.format(unit, type(unit))
        assert isinstance(size, int) and size >= 1, 'Invalid size: {} of type {}'.format(size, type(size))
        return periods.Period((unit, self, size))

    def offset(self, offset, unit):
        """
        Increment (or decrement) the given instant with offset units.

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
        assert unit in (config.DAY, config.MONTH, config.YEAR), 'Invalid unit: {} of type {}'.format(unit, type(unit))
        if offset == 'first-of':
            if unit == config.MONTH:
                day = 1
            elif unit == config.YEAR:
                month = 1
                day = 1
        elif offset == 'last-of':
            if unit == config.MONTH:
                day = calendar.monthrange(year, month)[1]
            elif unit == config.YEAR:
                month = 12
                day = 31
        else:
            assert isinstance(offset, int), 'Invalid offset: {} of type {}'.format(offset, type(offset))
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
    def year(self):
        """
        Extract year from instant.

        >>> instant(2014).year
        2014
        >>> instant('2014-2').year
        2014
        >>> instant('2014-2-3').year
        2014
        """
        return self[0]
