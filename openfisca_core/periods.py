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
start_date_by_period_cache = {}
start_date_str_by_period_cache = {}
stop_date_by_period_cache = {}
stop_date_str_by_period_cache = {}
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
    assert period[1] == period[2], '"date" is undefined for a period with several steps: {}'.format(period)
    return start_date(period)


def date_str(period):
    if period is None:
        return None
    assert period[1] == period[2], '"date_str" is undefined for a period with several steps: {}'.format(period)
    return start_date_str(period)


def iter(period):
    if period is not None:
        for step in iter_steps(*period):
            yield step


def iter_steps(unit, start, stop):
    step = start
    while step <= stop:
        yield step
        if unit == u'month':
            year, month = step
            month += 1
            if month == 13:
                month = 1
                year += 1
            step = (year, month)
        else:
            assert unit == u'year', unit
            step += 1


def json(period):
    if period is None:
        return None
    return collections.OrderedDict((
        ('unit', unit(period)),
        ('start', start_date_str(period)),
        ('stop', stop_date_str(period)),
        ))


def make_json_or_python_to_date_str(min_date = None, max_date = None):
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
                conv.test_isinstance(int),
                conv.pipe(
                    conv.test_between(1870, 2099),
                    conv.function(lambda year: datetime.date(year, 1, 1)),
                    ),
                conv.pipe(
                    conv.test_isinstance(basestring),
                    conv.test(year_or_month_or_day_re.match, error = N_(u'Invalid date')),
                    conv.function(lambda date: u'-'.join((date.split(u'-') + [u'01', u'01'])[:3])),
                    conv.iso8601_input_to_date,
                    ),
                ),
            ),
        conv.test_between(datetime.date(1870, 1, 1), datetime.date(2099, 12, 31)),
        test_range,
        conv.date_to_iso8601_str,
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
                        make_json_or_python_to_date_str(min_date, max_date),
                        conv.not_none,
                        ),
                    # stop
                    make_json_or_python_to_date_str(min_date, max_date),
                    ),
                ),
            conv.function(lambda value: period(*value)),
            ),
        conv.pipe(
            conv.test_isinstance(dict),
            conv.struct(
                dict(
                    start = conv.pipe(
                        make_json_or_python_to_date_str(min_date, max_date),
                        conv.not_none,
                        ),
                    stop = make_json_or_python_to_date_str(min_date, max_date),
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
    if unit == u'month':
        year, month = step
        month += 1
        if month == 13:
            month = 1
            year += 1
        return (year, month)
    assert unit == u'year', unit
    return step + 1


def period(unit, start, stop = None):
    start = step(unit, start)
    if stop is None:
        stop = start
    else:
        stop = step(unit, stop)
    return (unit, start, stop)


def period_from_date_str(unit, start_date_str, stop_date_str = None):
    if stop_date_str is None:
        stop_date_str = start_date_str
    return (unit, step_from_date_str(unit, start_date_str), step_from_date_str(unit, stop_date_str))


def period_from_step(unit, start, stop = None):
    if stop is None:
        stop = start
    return (unit, start, stop)


def previous_step(unit, step):
    if unit == u'month':
        year, month = step
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        return (year, month)
    assert unit == u'year', unit
    return step - 1


def start(period):
    if period is None:
        return None
    return period[1]


def start_date(period):
    if period is None:
        return None
    start_date = start_date_by_period_cache.get(period)
    if start_date is None:
        unit = period[0]
        start = period[1]
        if unit == u'month':
            start_date = datetime.date(start[0], start[1], 1)
        else:
            assert unit == u'year', unit
            start_date = datetime.date(start, 1, 1)
        start_date_by_period_cache[period] = start_date
    return start_date


def start_date_str(period):
    if period is None:
        return None
    start_date_str = start_date_str_by_period_cache.get(period)
    if start_date_str is None:
        start_date_str_by_period_cache[period] = start_date_str = start_date(period).isoformat()
    return start_date_str


def step(unit, step):
    if step is None:
        return None
    if isinstance(step, datetime.date):
        step = step.isoformat()
    elif isinstance(step, int):
        step = unicode(step)
    else:
        assert isinstance(step, basestring)
    return step_from_date_str(unit, step)


def step_from_date_str(unit, date_str):
    if date_str is None:
        return None
    if unit == u'month':
        return tuple(
            int(fragment)
            for fragment in date_str.split(u'-', 2)[:2]
            )
    assert unit == u'year', unit
    return int(date_str.split(u'-', 1)[0])


def stop(period):
    if period is None:
        return None
    return period[2]


def stop_date(period):
    if period is None:
        return None
    stop_date = stop_date_by_period_cache.get(period)
    if stop_date is None:
        unit = period[0]
        stop = period[2]
        if unit == u'month':
            stop_date = datetime.date(stop[0], stop[1], calendar.monthrange(stop[0], stop[1])[1])
        else:
            assert unit == u'year', unit
            stop_date = datetime.date(stop, 12, 31)
        stop_date_by_period_cache[period] = stop_date
    return stop_date


def stop_date_str(period):
    if period is None:
        return None
    stop_date_str = stop_date_str_by_period_cache.get(period)
    if stop_date_str is None:
        stop_date_str_by_period_cache[period] = stop_date_str = stop_date(period).isoformat()
    return stop_date_str


def unit(period):
    if period is None:
        return None
    return period[0]
