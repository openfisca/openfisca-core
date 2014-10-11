# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Toolbox to handle date intervals

A period is a triple (unit, start, stop), where unit is either "month" or "year" and where start & stop format depend
from unit.

Since a period is a triple it can be used as a dictionary key.
"""


import calendar
import collections
import datetime
import re

from . import conv


N_ = lambda message: message
# Note: weak references are not used, because Python 2.7 can't create weak reference to 'datetime.date' objects.
date_by_instant_cache = {}
date_str_by_instant_cache = {}
year_or_month_or_day_re = re.compile(ur'(18|19|20)\d{2}(-(0?[1-9]|1[0-2])(-([0-2]?\d|3[0-1]))?)?$')


class PeriodMixin(object):
    period = None

    @property
    def period_date(self):
        return date(self.period)

    @property
    def period_date_str(self):
        return date_str(self.period)

    @property
    def period_start_date(self):
        return start_date(self.period)

    @property
    def period_start_date_str(self):
        return start_date_str(self.period)

    @property
    def period_start_instant(self):
        return start_instant(self.period)

    @property
    def period_stop_date(self):
        return stop_date(self.period)

    @property
    def period_stop_date_str(self):
        return stop_date_str(self.period)

    @property
    def period_stop_instant(self):
        return stop_instant(self.period)

    @property
    def period_unit(self):
        return unit(self.period)


def date(period):
    if period is None:
        return None
    assert next_instant(period[0], period[1]) > period[2], \
        '"date" is undefined for a period with several instants: {}'.format(period)
    return start_date(period)


def date_str(period):
    if period is None:
        return None
    assert next_instant(period[0], period[1]) > period[2], \
        '"date_str" is undefined for a period with several instants: {}'.format(period)
    return start_date_str(period)


def input_to_period_tuple(value, state = None):
    """Convert an input string to a period tuple.

    .. note:: This function doesn't return a period, but a tuple that allows to construct a period.

    >>> input_to_period_tuple(u'2014')
    ((u'year', 2014), None)
    >>> input_to_period_tuple(u'2014:2015')
    ((u'year', 2014, 2015), None)
    >>> input_to_period_tuple(u'2014-2')
    ((u'month', (2014, 2)), None)
    >>> input_to_period_tuple(u'2014-3:2015-02')
    ((u'month', (2014, 3), (2015, 2)), None)
    >>> input_to_period_tuple(u'2014-2-3')
    ((u'day', (2014, 2, 3)), None)
    >>> input_to_period_tuple(u'2014-3-4:2015-03-03')
    ((u'day', (2014, 3, 4), (2015, 3, 3)), None)

    >>> input_to_period_tuple(u'year:2014')
    ((u'year', u'2014'), None)
    >>> input_to_period_tuple(u'year:2014:2015')
    ((u'year', u'2014', u'2015'), None)
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
        split_stop = tuple(
            clean_fragment
            for clean_fragment in (
                fragment.strip()
                for fragment in split_value[1].split(u'-')
                )
            if clean_fragment
            )
        if len(split_start) == len(split_stop) == 1:
            start_stop_couple, error = conv.struct(
                (
                    conv.pipe(
                        conv.input_to_strict_int,
                        conv.test_greater_or_equal(0),
                        ),
                    conv.pipe(
                        conv.input_to_strict_int,
                        conv.test_greater_or_equal(0),
                        ),
                    ),
                )((split_start[0], split_stop[0]), state = state)
            if error is None:
                return (u'year', start_stop_couple[0], start_stop_couple[1]), None
        elif len(split_start) == len(split_stop) == 2:
            start_stop_couple, error = conv.struct(
                (
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
                    ),
                )((split_start, split_stop), state = state)
            if error is None:
                return (u'month', start_stop_couple[0], start_stop_couple[1]), None
        elif len(split_start) == len(split_stop) == 3:
            start_stop_couple, error = conv.struct(
                (
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
                    ),
                )((split_start, split_stop), state = state)
            if error is None:
                return (u'day', start_stop_couple[0], start_stop_couple[1]), None
    return split_value, None


def instant_date(instant):
    if instant is None:
        return None
    instant_date = date_by_instant_cache.get(instant)
    if instant_date is None:
        date_by_instant_cache[instant] = instant_date = datetime.date(*instant)
    return instant_date


def instant_date_str(instant):
    if instant is None:
        return None
    instant_date_str = date_str_by_instant_cache.get(instant)
    if instant_date_str is None:
        date_str_by_instant_cache[instant] = instant_date_str = instant_date(instant).isoformat()
    return instant_date_str


def iter(period):
    if period is not None:
        for instant in iter_instants(*period):
            yield instant


def iter_instants(unit, start, stop):
    instant = start
    while instant <= stop:
        yield instant
        year, month, day = instant
        if unit == u'day':
            day += 1
            if day > calendar.monthrange(year, month)[1]:
                month += 1
                if month == 13:
                    year += 1
                    month = 1
                day = 1
        elif unit == u'month':
            month += 1
            if month == 13:
                month = 1
                year += 1
        else:
            assert unit == u'year', unit
            year += 1
        instant = (year, month, day)


def json_dict(period):
    if period is None:
        return None
    return collections.OrderedDict((
        ('unit', unit(period)),
        ('start', start_date_str(period)),
        ('stop', stop_date_str(period)),
        ))


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


def json_str(period):
    """Transform a period to a JSON string.

    >>> json_str(period(u'year', 2014))
    u'2014'
    >>> json_str(period(u'month', 2014))
    u'month:2014'
    >>> json_str(period(u'day', 2014))
    u'day:2014'

    >>> json_str(period(u'year', '2014-2'))
    u'year:2014-02:2015-01'
    >>> json_str(period(u'month', '2014-2'))
    u'2014-02'
    >>> json_str(period(u'day', '2014-2'))
    u'day:2014-02'

    >>> json_str(period(u'year', '2014-3-2'))
    u'year:2014-03-02:2015-03-01'
    >>> json_str(period(u'month', '2014-3-2'))
    u'month:2014-03-02:2014-04-01'
    >>> json_str(period(u'day', '2014-3-2'))
    u'2014-03-02'

    >>> json_str(period(u'year', 2012, 2014))
    u'2012:2014'
    >>> json_str(period(u'month', 2012, 2014))
    u'month:2012:2014'
    >>> json_str(period(u'day', 2012, 2014))
    u'day:2012:2014'

    >>> json_str(period(u'year', '2012-3', '2014-2'))
    u'year:2012-03:2014-02'
    >>> json_str(period(u'month', '2012-3', '2014-2'))
    u'2012-03:2014-02'
    >>> json_str(period(u'day', '2012-3', '2014-2'))
    u'day:2012-03:2014-02'

    >>> json_str(period(u'year', '2012-3-3', '2014-3-2'))
    u'year:2012-03-03:2014-03-02'
    >>> json_str(period(u'month', '2012-3-3', '2014-3-2'))
    u'month:2012-03-03:2014-03-02'
    >>> json_str(period(u'day', '2012-3-3', '2014-3-2'))
    u'2012-03-03:2014-03-02'
    """
    if period is None:
        return None
    unit, start_instant, stop_instant = period
    if start_instant[2] == 1 and stop_instant[2] == calendar.monthrange(stop_instant[0], stop_instant[1])[1]:
        if start_instant[1] == 1 and stop_instant[1] == 12:
            start_instant = start_instant[:1]
            stop_instant = stop_instant[:1]
        else:
            start_instant = start_instant[:2]
            stop_instant = stop_instant[:2]
    if unit == u'day' and len(start_instant) == len(stop_instant) == 3 \
            or unit == u'month' and len(start_instant) == len(stop_instant) == 2 \
            or unit == u'year' and len(start_instant) == len(stop_instant) == 1:
        unit = None
    start_str = u'-'.join(
        unicode(fragment) if index == 0 else u'{:02d}'.format(fragment)
        for index, fragment in enumerate(start_instant)
        )
    stop_str = None if start_instant == stop_instant else u'-'.join(
        unicode(fragment) if index == 0 else u'{:02d}'.format(fragment)
        for index, fragment in enumerate(stop_instant)
        )
    return u':'.join(
        fragment
        for fragment in (unit, start_str, stop_str)
        if fragment is not None
        )


def make_json_or_python_to_period(min_date = None, max_date = None):
    """Return a converter that creates a period from a JSON or Python object.

    >>> make_json_or_python_to_period()(u'2014')
    ((u'year', (2014, 1, 1), (2014, 12, 31)), None)
    >>> make_json_or_python_to_period()(u'2014:2015')
    ((u'year', (2014, 1, 1), (2015, 12, 31)), None)
    >>> make_json_or_python_to_period()(u'2014-2')
    ((u'month', (2014, 2, 1), (2014, 2, 28)), None)
    >>> make_json_or_python_to_period()(u'2014-2:2015-03')
    ((u'month', (2014, 2, 1), (2015, 3, 31)), None)
    >>> make_json_or_python_to_period()(u'2014-2-3')
    ((u'day', (2014, 2, 3), (2014, 2, 3)), None)
    >>> make_json_or_python_to_period()(u'2014-2-3:2015-04-05')
    ((u'day', (2014, 2, 3), (2015, 4, 5)), None)

    >>> make_json_or_python_to_period()(u'year:2014')
    ((u'year', (2014, 1, 1), (2014, 12, 31)), None)
    >>> make_json_or_python_to_period()(u'month:2014')
    ((u'month', (2014, 1, 1), (2014, 12, 31)), None)
    >>> make_json_or_python_to_period()(u'day:2014')
    ((u'day', (2014, 1, 1), (2014, 12, 31)), None)

    >>> make_json_or_python_to_period()(u'year:2014-2')
    ((u'year', (2014, 2, 1), (2015, 1, 31)), None)
    >>> make_json_or_python_to_period()(u'month:2014-2')
    ((u'month', (2014, 2, 1), (2014, 2, 28)), None)
    >>> make_json_or_python_to_period()(u'day:2014-2')
    ((u'day', (2014, 2, 1), (2014, 2, 28)), None)

    >>> make_json_or_python_to_period()(u'year:2014-2-3')
    ((u'year', (2014, 2, 3), (2015, 2, 2)), None)
    >>> make_json_or_python_to_period()(u'month:2014-2-3')
    ((u'month', (2014, 2, 3), (2014, 3, 2)), None)
    >>> make_json_or_python_to_period()(u'day:2014-2-3')
    ((u'day', (2014, 2, 3), (2014, 2, 3)), None)

    >>> make_json_or_python_to_period()(u'year:2014-2-3:2015')
    ((u'year', (2014, 2, 3), (2015, 12, 31)), None)
    >>> make_json_or_python_to_period()(u'month:2014-2-3:2015')
    ((u'month', (2014, 2, 3), (2015, 12, 31)), None)
    >>> make_json_or_python_to_period()(u'day:2014-2-3:2015')
    ((u'day', (2014, 2, 3), (2015, 12, 31)), None)

    >>> make_json_or_python_to_period()(u'year:2014-2-3:2015-02')
    ((u'year', (2014, 2, 3), (2015, 2, 28)), None)
    >>> make_json_or_python_to_period()(u'month:2014-2-3:2015-02')
    ((u'month', (2014, 2, 3), (2015, 2, 28)), None)
    >>> make_json_or_python_to_period()(u'day:2014-2-3:2015-02')
    ((u'day', (2014, 2, 3), (2015, 2, 28)), None)

    >>> make_json_or_python_to_period()(u'year:2014-2-3:2015-02-03')
    ((u'year', (2014, 2, 3), (2015, 2, 3)), None)
    >>> make_json_or_python_to_period()(u'month:2014-2-3:2015-02-03')
    ((u'month', (2014, 2, 3), (2015, 2, 3)), None)
    >>> make_json_or_python_to_period()(u'day:2014-2-3:2015-02-03')
    ((u'day', (2014, 2, 3), (2015, 2, 3)), None)
    """
    min_instant = (1870, 1, 1) if min_date is None else (min_date.year, min_date.month, min_date.day)
    max_instant = (2099, 12, 31) if max_date is None else (max_date.year, max_date.month, max_date.day)

    return conv.pipe(
        conv.condition(
            conv.test_isinstance(basestring),
            input_to_period_tuple,
            conv.condition(
                conv.test_isinstance(int),
                conv.pipe(
                    conv.test_greater_or_equal(0),
                    conv.function(lambda year: (u'year', year)),
                    ),
                ),
            ),
        conv.condition(
            conv.test_isinstance(dict),
            conv.pipe(
                conv.struct(
                    dict(
                        start = conv.pipe(
                            json_or_python_to_instant_tuple,
                            conv.not_none,
                            ),
                        stop =json_or_python_to_instant_tuple,
                        unit = conv.pipe(
                            conv.test_isinstance(basestring),
                            conv.input_to_slug,
                            conv.test_in((u'day', u'month', u'year')),
                            conv.not_none,
                            ),
                        ),
                    ),
                conv.function(lambda value: period(value['unit'], value['start'], value['stop'])),
                ),
            conv.pipe(
                conv.test_isinstance((list, tuple)),
                conv.test(lambda period_tuple: 2 <= len(period_tuple) <= 3, error = N_(u'Invalid period tuple')),
                conv.function(lambda period_tuple: (tuple(period_tuple) + (None,))[:3]),
                conv.struct(
                    (
                        # unit
                        conv.pipe(
                            conv.test_isinstance(basestring),
                            conv.input_to_slug,
                            conv.test_in((u'day', u'month', u'year')),
                            conv.not_none,
                            ),
                        # start
                        conv.pipe(
                            json_or_python_to_instant_tuple,
                            conv.not_none,
                            ),
                        # stop
                        json_or_python_to_instant_tuple,
                        ),
                    ),
                conv.function(lambda value: period(*value)),
                ),
            ),
        conv.struct(
            (
                # unit
                conv.noop,
                # start
                conv.test_between(min_instant, max_instant),
                # stop
                conv.test_between(min_instant, max_instant),
                ),
            ),
        )


def next_day_instant(instant):
    if instant is None:
        return None
    year, month, day = instant
    day += 1
    if day > calendar.monthrange(year, month)[1]:
        month += 1
        if month == 13:
            year += 1
            month = 1
        day = 1
    return (year, month, day)


def next_instant(unit, instant):
    """Return the next instant for given unit..

    >>> next_instant('day', (2014, 1, 1))
    (2014, 1, 2)
    >>> next_instant('month', (2014, 1, 1))
    (2014, 2, 1)
    >>> next_instant('year', (2014, 1, 1))
    (2015, 1, 1)
    """
    if unit == u'day':
        return next_day_instant(instant)
    year, month, day = instant
    if unit == u'month':
        month += 1
        if month == 13:
            month = 1
            year += 1
    else:
        assert unit == u'year', unit
        year += 1
    return (year, month, day)


def period(unit, start, stop = None):
    """Return a new period, aka a triple (unit, start_instant, stop_instant).

    >>> period('year', 2014)
    (u'year', (2014, 1, 1), (2014, 12, 31))
    >>> period('month', 2014)
    (u'month', (2014, 1, 1), (2014, 12, 31))
    >>> period('day', 2014)
    (u'day', (2014, 1, 1), (2014, 12, 31))

    >>> period('year', u'2014')
    (u'year', (2014, 1, 1), (2014, 12, 31))
    >>> period('month', u'2014')
    (u'month', (2014, 1, 1), (2014, 12, 31))
    >>> period('day', u'2014')
    (u'day', (2014, 1, 1), (2014, 12, 31))

    >>> period('year', u'2014-02')
    (u'year', (2014, 2, 1), (2015, 1, 31))
    >>> period('month', u'2014-02')
    (u'month', (2014, 2, 1), (2014, 2, 28))
    >>> period('day', u'2014-02')
    (u'day', (2014, 2, 1), (2014, 2, 28))

    >>> period('year', u'2014-3-2')
    (u'year', (2014, 3, 2), (2015, 3, 1))
    >>> period('month', u'2014-3-2')
    (u'month', (2014, 3, 2), (2014, 4, 1))
    >>> period('day', u'2014-3-2')
    (u'day', (2014, 3, 2), (2014, 3, 2))
    """
    if isinstance(start, basestring):
        start = tuple(
            int(fragment)
            for fragment in start.split(u'-', 2)[:3]
            )
    elif isinstance(start, datetime.date):
        start = (start.year, start.month, start.day)
    elif isinstance(start, int):
        start = (start,)
    elif isinstance(start, list):
        assert 1 <= len(start) <= 3
        start = tuple(start)
    else:
        assert isinstance(start, tuple)
        assert 1 <= len(start) <= 3
    if len(start) == 1:
        start = (start[0], 1, 1)
        if stop is None:
            stop = (start[0], 12, 31)
    elif len(start) == 2:
        start = (start[0], start[1], 1)
        if stop is None:
            if unit == u'year':
                stop = datetime.date(*next_instant(unit, start)) - datetime.timedelta(days = 1)
            else:
                stop = (start[0], start[1], calendar.monthrange(start[0], start[1])[1])
    elif stop is None:
        stop = datetime.date(*next_instant(unit, start)) - datetime.timedelta(days = 1)

    if isinstance(stop, basestring):
        stop = tuple(
            int(fragment)
            for fragment in stop.split(u'-', 2)[:3]
            )
    elif isinstance(stop, datetime.date):
        stop = (stop.year, stop.month, stop.day)
    elif isinstance(stop, int):
        stop = (stop,)
    elif isinstance(stop, list):
        assert 1 <= len(stop) <= 3
        stop = tuple(stop)
    else:
        assert isinstance(stop, tuple)
        assert 1 <= len(stop) <= 3
    if len(stop) == 1:
        stop = (stop[0], 12, 31)
    elif len(stop) == 2:
        stop = (stop[0], stop[1], calendar.monthrange(stop[0], stop[1])[1])

    return (unicode(unit), start, stop)


def previous_day_instant(instant):
    if instant is None:
        return None
    year, month, day = instant
    day -= 1
    if day <= 0:
        month -= 1
        if month == 0:
            year -= 1
            month = 12
        day = calendar.monthrange(year, month)[1]
    return (year, month, day)


def previous_instant(unit, instant):
    """Return the previous instant for given unit..

    >>> previous_instant('day', (2014, 1, 1))
    (2013, 12, 31)
    >>> previous_instant('month', (2014, 1, 1))
    (2013, 12, 1)
    >>> previous_instant('year', (2014, 1, 1))
    (2013, 1, 1)
    """
    if unit == u'day':
        return previous_day_instant(instant)
    year, month, day = instant
    if unit == u'month':
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    else:
        assert unit == u'year', unit
        year -= 1
    return (year, month, day)


def start_date(period):
    if period is None:
        return None
    return instant_date(period[1])


def start_date_str(period):
    if period is None:
        return None
    return instant_date_str(period[1])


def start_instant(period):
    if period is None:
        return None
    return period[1]


def stop_date(period):
    if period is None:
        return None
    return instant_date(period[2])


def stop_date_str(period):
    if period is None:
        return None
    return instant_date_str(period[2])


def stop_instant(period):
    if period is None:
        return None
    return period[2]


def unit(period):
    if period is None:
        return None
    return period[0]
