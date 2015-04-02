# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
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


def test_updated_legislation_items():
    def check_updated_legislation_items(description, items, start_instant, stop_instant, value, expected_items):
        new_items = reforms.updated_legislation_items(items, start_instant, stop_instant, value)
        assert_equal(map(dict, new_items), expected_items)

    # yield(
    #     check_updated_legislation_items,
    #     u'Insert a new item before the first existing item',
    #     [
    #         {
    #             "start": "2012-01-01",
    #             "stop": "2013-12-31",
    #             "value": 0.0,
    #             },
    #         ],
    #     periods.period('year', 2010).start,
    #     periods.period('year', 2010).stop,
    #     1,
    #     [
    #         {
    #             "start": "2010-01-01",
    #             "stop": "2010-12-31",
    #             "value": 1.0,
    #             },
    #         {
    #             "start": "2012-01-01",
    #             "stop": "2013-12-31",
    #             "value": 0.0,
    #             },
    #         ],
    #     )
    # yield(
    #     check_updated_legislation_items,
    #     u'Insert a new item after the last existing item',
    #     [
    #         {
    #             "start": "2012-01-01",
    #             "stop": "2013-12-31",
    #             "value": 0.0,
    #             },
    #         ],
    #     periods.period('year', 2014).start,
    #     periods.period('year', 2014).stop,
    #     1,
    #     [
    #         {
    #             "start": "2012-01-01",
    #             "stop": "2013-12-31",
    #             "value": 0.0,
    #             },
    #         {
    #             "start": "2014-01-01",
    #             "stop": "2014-12-31",
    #             "value": 1.0,
    #             },
    #         ],
    #     )
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
        periods.period('year', 2013).start,
        periods.period('year', 2013).stop,
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
        periods.period('year', 2011).start,
        periods.period('year', 2011).stop,
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
