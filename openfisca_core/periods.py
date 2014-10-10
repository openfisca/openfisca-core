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
date_by_step_cache = {}
date_str_by_step_cache = {}
year_or_month_or_day_re = re.compile(ur'(18|19|20)\d{2}(-(0[1-9]|1[0-2])(-([0-2]\d|3[0-1]))?)?$')


class PeriodMixin(object):
    period = None

    @property
    def date(self):
        return date(self.period)

    @property
    def date_str(self):
        return date_str(self.period)

    @property
    def period_start(self):
        return start(self.period)

    @property
    def period_start_date(self):
        return start_date(self.period)

    @property
    def period_start_date_str(self):
        return start_date_str(self.period)

    @property
    def period_stop(self):
        return stop(self.period)

    @property
    def period_stop_date(self):
        return stop_date(self.period)

    @property
    def period_stop_date_str(self):
        return stop_date_str(self.period)

    @property
    def period_unit(self):
        return unit(self.period)


def date(period):
    if period is None:
        return None
    assert next_step(period[0], period[1]) > period[2], \
        '"date" is undefined for a period with several steps: {}'.format(period)
    return start_date(period)


def date_str(period):
    if period is None:
        return None
    assert next_step(period[0], period[1]) > period[2], \
        '"date_str" is undefined for a period with several steps: {}'.format(period)
    return start_date_str(period)


def iter(period):
    if period is not None:
        for step in iter_steps(*period):
            yield step


def iter_steps(unit, start, stop):
    step = start
    while step <= stop:
        yield step
        year, month, day = step
        if unit == u'month':
            month += 1
            if month == 13:
                month = 1
                year += 1
        else:
            assert unit == u'year', unit
            year += 1
        step = (year, month, day)


def json(period):
    if period is None:
        return None
    return collections.OrderedDict((
        ('unit', unit(period)),
        ('start', start_date_str(period)),
        ('stop', stop_date_str(period)),
        ))


def make_json_or_python_to_date(min_date = None, max_date = None):
    if min_date is None and max_date is None:
        test_range = conv.noop
    elif min_date is None:
        test_range = conv.test_less_or_equal(max_date)
    elif max_date is None:
        test_range = conv.test_greater_or_equal(min_date)
    else:
        test_range = conv.test_between(min_date, max_date),
    return conv.pipe(
        conv.condition(
            conv.test_isinstance(datetime.date),
            conv.noop,
            conv.condition(
                conv.test_isinstance(basestring),
                conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.test(year_or_month_or_day_re.match, error = N_(u'Invalid date')),
                    conv.function(lambda date: u'-'.join((date.split(u'-') + [u'01', u'01'])[:3])),
                    conv.iso8601_input_to_date,
                    ),
                conv.condition(
                    conv.test_isinstance(int),
                    conv.pipe(
                        conv.test_between(1870, 2099),
                        conv.function(lambda year: datetime.date(year, 1, 1)),
                        ),
                    conv.pipe(
                        conv.test_isinstance((list, tuple)),
                        conv.uniform_sequence(conv.test_isinstance(int)),
                        conv.test(lambda date_tuple: 1 <= len(date_tuple) <= 3, error = N_(u'Invalid date tuple')),
                        conv.function(lambda date_tuple:
                            u'-'.join((tuple(unicode(fragment) for fragment in date_tuple) + (u'01', u'01'))[:3])),
                        conv.iso8601_input_to_date,
                        ),
                    ),
                ),
            ),
        conv.test_between(datetime.date(1870, 1, 1), datetime.date(2099, 12, 31)),
        test_range,
        )


def make_json_or_python_to_period(min_date = None, max_date = None):
    return conv.condition(
        conv.test_isinstance((list, tuple)),
        conv.pipe(
            conv.struct(
                (
                    # unit
                    conv.pipe(
                        conv.test_isinstance(basestring),
                        conv.input_to_slug,
                        conv.test_in((u'month', u'year')),
                        conv.not_none,
                        ),
                    # start
                    conv.pipe(
                        make_json_or_python_to_date(min_date, max_date),
                        conv.not_none,
                        ),
                    # stop
                    make_json_or_python_to_date(min_date, max_date),
                    ),
                ),
            conv.function(lambda value: period(*value)),
            ),
        conv.pipe(
            conv.test_isinstance(dict),
            conv.struct(
                dict(
                    start = conv.pipe(
                        make_json_or_python_to_date(min_date, max_date),
                        conv.not_none,
                        ),
                    stop = make_json_or_python_to_date(min_date, max_date),
                    unit = conv.pipe(
                        conv.test_isinstance(basestring),
                        conv.input_to_slug,
                        conv.test_in((u'month', u'year')),
                        conv.not_none,
                        ),
                    ),
                ),
            conv.function(lambda value: period(value['unit'], value['start'], value['stop'])),
            ),
        )


def next_step(unit, step):
    year, month, day = step
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
    elif len(start) == 2:
        start = (start[0], start[1], 1)

    if stop is None:
        stop = datetime.date(*next_step(unit, start)) - datetime.timedelta(days = 1)
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

    return (unit, start, stop)


def previous_step(unit, step):
    year, month, day = step
    if unit == u'month':
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    else:
        assert unit == u'year', unit
        year -= 1
    return (year, month, day)


def start(period):
    if period is None:
        return None
    return period[1]


def start_date(period):
    if period is None:
        return None
    return step_date(period[1])


def start_date_str(period):
    if period is None:
        return None
    return step_date_str(period[1])


def step_date(step):
    if step is None:
        return None
    step_date = date_by_step_cache.get(step)
    if step_date is None:
        date_by_step_cache[step] = step_date = datetime.date(*step)
    return step_date


def step_date_str(step):
    if step is None:
        return None
    step_date_str = date_str_by_step_cache.get(step)
    if step_date_str is None:
        date_str_by_step_cache[step] = step_date_str = step_date(step).isoformat()
    return step_date_str


def step_next_day(step):
    if step is None:
        return None
    year, month, day = step
    day += 1
    if day > calendar.monthrange(year, month)[1]:
        month += 1
        if month == 13:
            year += 1
            month = 1
        day = 1
    return (year, month, day)


def step_previous_day(step):
    if step is None:
        return None
    year, month, day = step
    day -= 1
    if day <= 0:
        month -= 1
        if month == 0:
            year -= 1
            month = 12
        day = calendar.monthrange(year, month)[1]
    return (year, month, day)


def stop(period):
    if period is None:
        return None
    return period[2]


def stop_date(period):
    if period is None:
        return None
    return step_date(period[2])


def stop_date_str(period):
    if period is None:
        return None
    return step_date_str(period[2])


def unit(period):
    if period is None:
        return None
    return period[0]
