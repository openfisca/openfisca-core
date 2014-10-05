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
    if stop is None:
        stop = start
    return (unit, start, stop)


def period_from_anything(unit, start, stop = None):
    if isinstance(start, datetime.date):
        start = start.isoformat()
    elif isinstance(start, int):
        start = unicode(start)
    else:
        assert isinstance(start, basestring)
    if stop is None:
        stop = start
    elif isinstance(stop, datetime.date):
        stop = stop.isoformat()
    elif isinstance(stop, int):
        stop = unicode(stop)
    else:
        assert isinstance(stop, basestring)
    return (unit, step_from_date_str(unit, start), step_from_date_str(unit, stop))


def period_from_date_str(unit, start_date_str, stop_date_str = None):
    if stop_date_str is None:
        stop_date_str = start_date_str
    return (unit, step_from_date_str(unit, start_date_str), step_from_date_str(unit, stop_date_str))


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
    unit = period[0]
    start = period[1]
    if unit == u'month':
        return datetime.date(start[0], start[1], 1)
    assert unit == u'year', unit
    return datetime.date(start, 1, 1)


def start_date_str(period):
    if period is None:
        return None
    return start_date(period).isoformat()


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
    unit = period[0]
    stop = period[2]
    if unit == u'month':
        return datetime.date(stop[0], stop[1], calendar.monthrange(stop[0], stop[1])[1])
    assert unit == u'year', unit
    return datetime.date(stop, 12, 31)


def stop_date_str(period):
    if period is None:
        return None
    return stop_date(period).isoformat()


def unit(period):
    if period is None:
        return None
    return period[0]
