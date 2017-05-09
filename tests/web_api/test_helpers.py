from collections import OrderedDict
from nose.tools import assert_equal

from openfisca_web_api.loader.parameters import build_values, get_value


def test_build_values():
    values = [
        OrderedDict([('start', u'2017-01-01'), ('value', 0.02)]),
        OrderedDict([('start', u'2015-01-01'), ('value', 0.04)]),
        OrderedDict([('start', u'2013-01-01'), ('value', 0.03)])
        ]

    values_json = {
        '2017-01-01': 0.02,
        '2015-01-01': 0.04,
        '2013-01-01': 0.03,
        }
    assert_equal(build_values(values), values_json)


def test_build_values_with_stop_date():
    values = [
        OrderedDict([('start', u'2018-01-01')]),
        OrderedDict([('start', u'2017-01-01'), ('stop', u'2017-12-31'), ('value', 0.02)]),
        OrderedDict([('start', u'2015-01-01'), ('stop', u'2016-12-31'), ('value', 0.04)]),
        OrderedDict([('start', u'2013-01-01'), ('stop', u'2014-12-31'), ('value', 0.03)])
        ]

    values_json = {
        '2018-01-01': None,
        '2017-01-01': 0.02,
        '2015-01-01': 0.04,
        '2013-01-01': 0.03,
        }

    assert_equal(build_values(values), values_json)


def test_get_value():
    values = {u'2013-01-01': 0.03, u'2017-01-01': 0.02, u'2015-01-01': 0.04}

    assert_equal(get_value(u'2013-01-01', values), 0.03)
    assert_equal(get_value(u'2014-01-01', values), 0.03)
    assert_equal(get_value(u'2015-02-01', values), 0.04)
    assert_equal(get_value(u'2016-12-31', values), 0.04)
    assert_equal(get_value(u'2017-01-01', values), 0.02)
    assert_equal(get_value(u'2018-01-01', values), 0.02)


def test_get_value_with_none():
    values = {u'2015-01-01': 0.04, u'2017-01-01': None}

    assert_equal(get_value(u'2016-12-31', values), 0.04)
    assert_equal(get_value(u'2017-01-01', values), None)
    assert_equal(get_value(u'2011-01-01', values), None)
