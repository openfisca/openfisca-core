# -*- coding: utf-8 -*-

from httplib import OK, NOT_FOUND
import json
from nose.tools import assert_equal
from . import subject

# /parameters

parameters_response = subject.get('/parameters')


def test_return_code():
    assert_equal(parameters_response.status_code, OK)


def test_response_data():
    parameters = json.loads(parameters_response.data)
    assert_equal(
        parameters[u'taxes.income_tax_rate'],
        {u'description': u'Income tax rate'}
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
    parameter = json.loads(response.data)
    assert_equal(
        parameter,
        {
            u'id': u'taxes.income_tax_rate',
            u'description': u'Income tax rate',
            u'values': {u'2015-01-01': 0.15, u'2014-01-01': 0.14, u'2013-01-01': 0.13, u'2012-01-01': 0.16}
            }
        )


def test_stopped_parameter_values():
    response = subject.get('/parameter/benefits.housing_allowance')
    parameter = json.loads(response.data)
    assert_equal(
        parameter,
        {
            u'id': u'benefits.housing_allowance',
            u'description': u'Housing allowance amount (as a fraction of the rent)',
            u'values': {u'2016-12-01': None, u'2010-01-01': 0.25}
            }
        )


def test_bareme():
    response = subject.get('/parameter/taxes.social_security_contribution')
    parameter = json.loads(response.data)
    assert_equal(
        parameter,
        {
            u'id': u'taxes.social_security_contribution',
            u'description': u'Social security contribution tax scale',
            u'brackets': {
                u'2013-01-01': {"0.0": 0.03, "12000.0": 0.10},
                u'2014-01-01': {"0.0": 0.03, "12100.0": 0.10},
                u'2015-01-01': {"0.0": 0.04, "12200.0": 0.12},
                u'2016-01-01': {"0.0": 0.04, "12300.0": 0.12},
                u'2017-01-01': {"0.0": 0.02, "6000.0": 0.06, "12400.0": 0.12},
                }
            }
        )


# def test_stopped_bareme():
#     response = subject.get('/parameter/contribution_sociale.crds.activite.abattement')
#     parameter = json.loads(response.data)
#     assert_equal(
#         parameter,
#         {
#             u'id': u'contribution_sociale.crds.activite.abattement',
#             u'description': u"Abattement sur les revenus d\'activité, du chômage et des préretraites",
#             u'brackets': {
#                 "1998-01-01": {"0.0": 0.05},
#                 "2005-01-01": {"0.0": 0.03},
#                 "2011-01-01": {"0.0": 0.03, "4.0": 0},
#                 "2012-01-01": {"0.0": 0.0175, "4.0": 0},
#                 "2015-01-01": None,
#                 }
#             }
#         )


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

    for route, code in expected_codes.iteritems():
        yield check_code, route, code
