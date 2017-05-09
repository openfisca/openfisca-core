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
        parameters[u'impot.taux'],
        {u'description': u'Taux d\'impôt sur les salaires'}
        )


# /parameter/<id>

def test_error_code_non_existing_parameter():
    response = subject.get('/parameter/non.existing.parameter')
    assert_equal(response.status_code, NOT_FOUND)


def test_return_code_existing_parameter():
    response = subject.get('/parameter/impot.taux')
    assert_equal(response.status_code, OK)


def test_parameter_values():
    response = subject.get('/parameter/impot.taux')
    parameter = json.loads(response.data)
    assert_equal(
        parameter,
        {
            u'id': u'impot.taux',
            u'description': u'Taux d\'impôt sur les salaires',
            u'values': {u'2016-01-01': 0.35, u'2015-01-01': 0.32, u'1998-01-01': 0.3}
            }
        )


def test_stopped_parameter_values():
    response = subject.get('/parameter/impot.bouclier')
    parameter = json.loads(response.data)
    assert_equal(
        parameter,
        {
            u'id': u'impot.bouclier',
            u'description': u'Montant maximum de l\'impôt',
            u'values': {u'2012-01-01': None, u'2009-01-01': 0.6, u'2008-01-01': 0.5}
            }
        )


def test_bareme():
    response = subject.get('/parameter/contribution_sociale.salaire.bareme')
    parameter = json.loads(response.data)
    assert_equal(
        parameter,
        {
            u'id': u'contribution_sociale.salaire.bareme',
            u'description': u'Bareme progressif de contribution sociale sur les salaires',
            u'brackets': {
                u'2013-01-01': {"0.0": 0.03, "12000.0": 0.10},
                u'2014-01-01': {"0.0": 0.03, "12100.0": 0.10},
                u'2015-01-01': {"0.0": 0.04, "12200.0": 0.12},
                u'2016-01-01': {"0.0": 0.04, "12300.0": 0.12},
                u'2017-01-01': {"0.0": 0.02, "6000.0": 0.06, "12400.0": 0.12},
                }
            }
        )


def test_stopped_bareme():
    response = subject.get('/parameter/contribution_sociale.crds.activite.abattement')
    parameter = json.loads(response.data)
    assert_equal(
        parameter,
        {
            u'id': u'contribution_sociale.crds.activite.abattement',
            u'description': u"Abattement sur les revenus d\'activité, du chômage et des préretraites",
            u'brackets': {
                "1998-01-01": {"0.0": 0.05},
                "2005-01-01": {"0.0": 0.03},
                "2011-01-01": {"0.0": 0.03, "4.0": 0},
                "2012-01-01": {"0.0": 0.0175, "4.0": 0},
                "2015-01-01": None,
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
        '/parameter/impot.taux/': OK,
        '/parameter/impot.taux/too-much-nesting': NOT_FOUND,
        '/parameter//impot.taux/': NOT_FOUND,
        }

    for route, code in expected_codes.iteritems():
        yield check_code, route, code
