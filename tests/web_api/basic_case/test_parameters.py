# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from http.client import OK, NOT_FOUND
import json
from nose.tools import assert_equal
from . import subject

# /parameters

parameters_response = subject.get('/parameters')


def test_return_code():
    assert_equal(parameters_response.status_code, OK)


def test_response_data():
    parameters = json.loads(parameters_response.data.decode('utf-8'))
    assert_equal(
        parameters['taxes.income_tax_rate'],
        {'description': 'Income tax rate'}
        )


# /parameter/<id>

def test_error_code_non_existing_parameter():
    response = subject.get('/parameter/non.existing.parameter')
    assert_equal(response.status_code, NOT_FOUND)


def test_return_code_existing_parameter():
    response = subject.get('/parameter/taxes.income_tax_rate')
    assert_equal(response.status_code, OK)


def test_parameter_values():
    response = subject.get('/parameter/taxes.income_tax_rate')
    parameter = json.loads(response.data.decode('utf-8'))
    assert_equal(
        parameter,
        {
            'id': 'taxes.income_tax_rate',
            'description': 'Income tax rate',
            'values': {'2015-01-01': 0.15, '2014-01-01': 0.14, '2013-01-01': 0.13, '2012-01-01': 0.16}
            }
        )


def test_parameter_node():
    response = subject.get('/parameter/benefits')
    assert_equal(response.status_code, OK)
    parameter = json.loads(response.data)
    assert_equal(
        parameter,
        {
            u'id': u'benefits',
            u'description': None,
            u'children': {
                u'housing_allowance': {u'description': u'Housing allowance amount (as a fraction of the rent)', u'id': 'benefits.housing_allowance'},
                u'basic_income': {u'description': u'Amount of the basic income', u'id': 'benefits.basic_income'}
                }
            }
        )


def test_stopped_parameter_values():
    response = subject.get('/parameter/benefits.housing_allowance')
    parameter = json.loads(response.data.decode('utf-8'))
    assert_equal(
        parameter,
        {
            'id': 'benefits.housing_allowance',
            'description': 'Housing allowance amount (as a fraction of the rent)',
            'values': {'2016-12-01': None, '2010-01-01': 0.25}
            }
        )


def test_bareme():
    response = subject.get('/parameter/taxes.social_security_contribution')
    parameter = json.loads(response.data.decode('utf-8'))
    assert_equal(
        parameter,
        {
            'id': 'taxes.social_security_contribution',
            'description': 'Social security contribution tax scale',
            'brackets': {
                '2013-01-01': {"0.0": 0.03, "12000.0": 0.10},
                '2014-01-01': {"0.0": 0.03, "12100.0": 0.10},
                '2015-01-01': {"0.0": 0.04, "12200.0": 0.12},
                '2016-01-01': {"0.0": 0.04, "12300.0": 0.12},
                '2017-01-01': {"0.0": 0.02, "6000.0": 0.06, "12400.0": 0.12},
                }
            }
        )


def check_code(route, code):
    response = subject.get(route)
    assert_equal(response.status_code, code)


def test_routes_robustness():
    expected_codes = {
        '/parameters/': OK,
        '/parameter': NOT_FOUND,
        '/parameter/': NOT_FOUND,
        '/parameter/with-ÜNı©ød€': NOT_FOUND,
        '/parameter/with%20url%20encoding': NOT_FOUND,
        '/parameter/taxes.income_tax_rate/': OK,
        '/parameter/taxes.income_tax_rate/too-much-nesting': NOT_FOUND,
        '/parameter//taxes.income_tax_rate/': NOT_FOUND,
        }

    for route, code in expected_codes.items():
        yield check_code, route, code


def test_parameter_encoding():
    parameter_response = subject.get('/parameter/general.age_of_retirement')
    assert_equal(parameter_response.status_code, OK)
