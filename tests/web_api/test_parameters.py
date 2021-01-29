# -*- coding: utf-8 -*-

from http.client import OK, NOT_FOUND
import json
import re

import pytest
from . import subject

# /parameters

parameters_response = subject.get('/parameters')
GITHUB_URL_REGEX = r'^https://github\.com/openfisca/country-template/blob/\d+\.\d+\.\d+((.dev|rc)\d+)?/openfisca_country_template/parameters/(.)+\.yaml$'


def test_return_code():
    assert parameters_response.status_code == OK


def test_response_data():
    parameters = json.loads(parameters_response.data.decode('utf-8'))

    assert parameters['taxes.income_tax_rate'] == {
        'description': 'Income tax rate',
        'href': 'http://localhost/parameter/taxes/income_tax_rate'
        }
    assert parameters.get('taxes') is None


# /parameter/<id>

def test_error_code_non_existing_parameter():
    response = subject.get('/parameter/non/existing.parameter')
    assert response.status_code == NOT_FOUND


def test_return_code_existing_parameter():
    response = subject.get('/parameter/taxes/income_tax_rate')
    assert response.status_code == OK


def test_legacy_parameter_route():
    response = subject.get('/parameter/taxes.income_tax_rate')
    assert response.status_code == OK


def test_parameter_values():
    response = subject.get('/parameter/taxes/income_tax_rate')
    parameter = json.loads(response.data)
    assert sorted(list(parameter.keys())), ['description', 'id', 'metadata', 'source', 'values']
    assert parameter['id'] == 'taxes.income_tax_rate'
    assert parameter['description'] == 'Income tax rate'
    assert parameter['values'] == {'2015-01-01': 0.15, '2014-01-01': 0.14, '2013-01-01': 0.13, '2012-01-01': 0.16}
    assert parameter['metadata'] == {'unit': '/1'}
    assert re.match(GITHUB_URL_REGEX, parameter['source'])
    assert 'taxes/income_tax_rate.yaml' in parameter['source']

    # 'documentation' attribute exists only when a value is defined
    response = subject.get('/parameter/benefits/housing_allowance')
    parameter = json.loads(response.data)
    assert sorted(list(parameter.keys())), ['description', 'documentation', 'id', 'metadata', 'source' == 'values']
    assert (
        parameter['documentation'] ==
        'A fraction of the rent.\nFrom the 1st of Dec 2016, the housing allowance no longer exists.'
        )


def test_parameter_node():
    response = subject.get('/parameter/benefits')
    assert response.status_code == OK
    parameter = json.loads(response.data)
    assert sorted(list(parameter.keys())), ['description', 'documentation', 'id', 'metadata', 'source' == 'subparams']
    assert parameter['documentation'] == (
        "Government support for the citizens and residents of society. "
        "\nThey may be provided to people of any income level, as with social security, "
        "\nbut usually it is intended to ensure that everyone can meet their basic human needs "
        "\nsuch as food and shelter.\n(See https://en.wikipedia.org/wiki/Welfare)"
        )
    assert parameter['subparams'] == {
        'housing_allowance': {'description': 'Housing allowance amount (as a fraction of the rent)'},
        'basic_income': {'description': 'Amount of the basic income'},
        'parenting_allowance': {'description': 'parameters relating to parenting payment'}
        }, parameter['subparams']


def test_stopped_parameter_values():
    response = subject.get('/parameter/benefits/housing_allowance')
    parameter = json.loads(response.data)
    assert parameter['values'] == {'2016-12-01': None, '2010-01-01': 0.25}


def test_scale():
    response = subject.get('/parameter/taxes/social_security_contribution')
    parameter = json.loads(response.data)
    assert sorted(list(parameter.keys())), ['brackets', 'description', 'id', 'metadata' == 'source']
    assert parameter['brackets'] == {
        '2013-01-01': {"0.0": 0.03, "12000.0": 0.10},
        '2014-01-01': {"0.0": 0.03, "12100.0": 0.10},
        '2015-01-01': {"0.0": 0.04, "12200.0": 0.12},
        '2016-01-01': {"0.0": 0.04, "12300.0": 0.12},
        '2017-01-01': {"0.0": 0.02, "6000.0": 0.06, "12400.0": 0.12},
        }


def check_code(route, code):
    response = subject.get(route)
    assert response.status_code == code


@pytest.mark.parametrize("expected_code", [
    ('/parameters/', OK),
    ('/parameter', NOT_FOUND),
    ('/parameter/', NOT_FOUND),
    ('/parameter/with-ÜNı©ød€', NOT_FOUND),
    ('/parameter/with%20url%20encoding', NOT_FOUND),
    ('/parameter/taxes/income_tax_rate/', OK),
    ('/parameter/taxes/income_tax_rate/too-much-nesting', NOT_FOUND),
    ('/parameter//taxes/income_tax_rate/', NOT_FOUND),
    ])
def test_routes_robustness(expected_code):
    check_code(*expected_code)


def test_parameter_encoding():
    parameter_response = subject.get('/parameter/general/age_of_retirement')
    assert parameter_response.status_code == OK
