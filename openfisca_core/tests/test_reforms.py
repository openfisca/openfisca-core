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


import datetime

from nose.tools import assert_equal, assert_is

from .. import periods, reforms


def test_find_item_at_date():
    items = [
        {
            "start": "2012-01-01",
            "stop": "2013-12-31",
            "value": 0.0,
            },
        ]
    legislation_period = periods.period('year', 2006, 2014)
    assert_is(reforms.find_item_at_date(items, datetime.date(2010, 5, 21)), None)
    assert_is(
        reforms.find_item_at_date(items, datetime.date(2005, 12, 31), nearest_in_period = legislation_period),
        None,
        )
    assert_equal(
        reforms.find_item_at_date(items, datetime.date(2006, 1, 1), nearest_in_period = legislation_period)['value'],
        0,
        )
    assert_equal(
        reforms.find_item_at_date(items, datetime.date(2010, 5, 21), nearest_in_period = legislation_period)['value'],
        0,
        )
    assert_equal(
        reforms.find_item_at_date(items, datetime.date(2014, 12, 31), nearest_in_period = legislation_period)['value'],
        0,
        )
    assert_is(
        reforms.find_item_at_date(items, datetime.date(2015, 1, 1), nearest_in_period = legislation_period),
        None,
        )
    assert_equal(reforms.find_item_at_date(items, datetime.date(2012, 1, 1))['value'], 0)
    assert_equal(reforms.find_item_at_date(items, datetime.date(2012, 5, 21))['value'], 0)
    assert_equal(reforms.find_item_at_date(items, datetime.date(2013, 12, 31))['value'], 0)
    assert_is(reforms.find_item_at_date(items, datetime.date(2014, 8, 11)), None)


def test_updated_legislation_items():
    def check_updated_legislation_items(description, items, period, value, expected_items):
        new_items = reforms.updated_legislation_items(items, period, value)
        assert_equal(new_items, expected_items)

    yield(
        check_updated_legislation_items,
        u'Insert a new item before the first existing item',
        [
            {
                "start": "2012-01-01",
                "stop": "2013-12-31",
                "value": 0.0,
                },
            ],
        periods.period('year', 2010),
        1,
        [
            {
                "start": "2010-01-01",
                "stop": "2010-12-31",
                "value": 1.0,
                },
            {
                "start": "2012-01-01",
                "stop": "2013-12-31",
                "value": 0.0,
                },
            ],
        )
    yield(
        check_updated_legislation_items,
        u'Insert a new item after the last existing item',
        [
            {
                "start": "2012-01-01",
                "stop": "2013-12-31",
                "value": 0.0,
                },
            ],
        periods.period('year', 2014),
        1,
        [
            {
                "start": "2012-01-01",
                "stop": "2013-12-31",
                "value": 0.0,
                },
            {
                "start": "2014-01-01",
                "stop": "2014-12-31",
                "value": 1.0,
                },
            ],
        )
    yield(
        check_updated_legislation_items,
        u'Replace an item by a new item',
        [
            {
                "start": "2013-01-01",
                "stop": "2013-12-31",
                "value": 0.0,
                },
            ],
        periods.period('year', 2013),
        1,
        [
            {
                "start": "2013-01-01",
                "stop": "2013-12-31",
                "value": 1.0,
                },
            ],
        )
    yield(
        check_updated_legislation_items,
        u'Insert a new item in the middle of an existing item',
        [
            {
                "start": "2010-01-01",
                "stop": "2013-12-31",
                "value": 0.0,
                },
            ],
        periods.period('year', 2011),
        1,
        [
            {
                "start": "2010-01-01",
                "stop": "2010-12-31",
                "value": 0.0,
                },
            {
                "start": "2011-01-01",
                "stop": "2011-12-31",
                "value": 1.0,
                },
            {
                "start": "2012-01-01",
                "stop": "2013-12-31",
                "value": 0.0,
                },
            ],
        )
