import os

from nose.tools import assert_equal

from openfisca_core.parameters import load_file
from openfisca_web_api_preview.loader.parameters import transform_values_history, get_value


dir_path = os.path.dirname(__file__)


def test_transform_values_history():
    file_path = os.path.join(dir_path, 'test_helpers.yaml')
    parameter = load_file(name='dummy_name', file_path=file_path)

    values = {
        '2017-01-01': 0.02,
        '2015-01-01': 0.04,
        '2013-01-01': 0.03,
        }
    assert_equal(transform_values_history(parameter), values)


def test_transform_values_history_with_stop_date():
    file_path = os.path.join(dir_path, 'test_helpers_with_stop_date.yaml')
    parameter = load_file(name='dummy_name', file_path=file_path)

    values = {
        '2018-01-01': None,
        '2017-01-01': 0.02,
        '2015-01-01': 0.04,
        '2013-01-01': 0.03,
        }

    assert_equal(transform_values_history(parameter), values)


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
