# -*- coding: utf-8 -*-

from httplib import OK, NOT_FOUND
import json
from nose.tools import assert_equal, assert_regexp_matches, assert_not_in, assert_items_equal, assert_in, assert_is_none
from . import subject

# /variables

variables_response = subject.get('/variables')
GITHUB_URL_REGEX = '^https://github\.com/openfisca/openfisca-dummy-country/blob/\d+\.\d+\.\d+/openfisca_dummy_country/model/model\.py#L\d+-L\d+$'


def test_return_code():
    assert_equal(variables_response.status_code, OK)


def test_response_data():
    variables = json.loads(variables_response.data)
    assert_equal(
        variables[u'birth'],
        {u'description': u'Date de naissance'}
        )


# /variable/<id>


def test_error_code_non_existing_variable():
    response = subject.get('/variable/non_existing_variable')
    assert_equal(response.status_code, NOT_FOUND)


input_variable_response = subject.get('/variable/birth')
input_variable = json.loads(input_variable_response.data)


def test_return_code_existing_input_variable():
    assert_equal(input_variable_response.status_code, OK)


def check_input_variable_value(key, expected_value):
    assert_equal(input_variable[key], expected_value)


def test_input_variable_value():
    expected_values = {
        u'description': u'Date de naissance',
        u'valueType': u'Date',
        u'defaultValue': u'1970-01-01',
        u'definitionPeriod': u'ETERNITY',
        u'entity': u'individu',
        u'references': [u'https://fr.wikipedia.org/wiki/Date_de_naissance'],
        }

    for key, expected_value in expected_values.iteritems():
        yield check_input_variable_value, key, expected_value


def test_input_variable_github_url():
    assert_regexp_matches(input_variable['source'], GITHUB_URL_REGEX)


variable_response = subject.get('/variable/salaire_net')
variable = json.loads(variable_response.data)


def test_return_code_existing_variable():
    assert_equal(variable_response.status_code, OK)


def check_variable_value(key, expected_value):
    assert_equal(variable[key], expected_value)


def test_variable_value():
    expected_values = {
        u'description': u'Salaire net',
        u'valueType': u'Float',
        u'defaultValue': 0,
        u'definitionPeriod': u'MONTH',
        u'entity': u'individu',
        }

    for key, expected_value in expected_values.iteritems():
        yield check_variable_value, key, expected_value


def test_null_values_are_dropped():
    assert_not_in('references', variable.keys())


def test_variable_formula_github_link():
    assert_regexp_matches(variable['formulas']['0001-01-01']['source'], GITHUB_URL_REGEX)


def test_variable_formula_content():
    formula_code = "def function(individu, period):\n    salaire_brut = individu('salaire_brut', period)\n\n    return salaire_brut * 0.8\n"
    assert_equal(variable['formulas']['0001-01-01']['content'], formula_code)


def test_variable_with_start_and_stop_date():
    response = subject.get('/variable/fixed_tax')
    variable = json.loads(response.data)
    assert_items_equal(variable['formulas'], ['1980-01-01', '1990-01-01'])
    assert_is_none(variable['formulas']['1990-01-01'])
    assert_in('function', variable['formulas']['1980-01-01']['content'])


dated_variable_response = subject.get('/variable/rsa')
dated_variable = json.loads(dated_variable_response.data)


def test_return_code_existing_dated_variable():
    assert_equal(dated_variable_response.status_code, OK)


def test_dated_variable_formulas_dates():
    assert_items_equal(dated_variable['formulas'], ['2010-01-01', '2011-01-01', '2013-01-01'])


def test_dated_variable_formulas_content():
    formula_code_2010 = "def function_2010(individu, period):\n    salaire_imposable = individu('salaire_imposable', period, options = [DIVIDE])\n\n    return (salaire_imposable < 500) * 100.0\n"
    formula_code_2011 = "def function_2011_2012(individu, period):\n    salaire_imposable = individu('salaire_imposable', period, options = [DIVIDE])\n\n    return (salaire_imposable < 500) * 200.0\n"
    formula_code_2013 = "def function_2013(individu, period):\n    salaire_imposable = individu('salaire_imposable', period, options = [DIVIDE])\n\n    return (salaire_imposable < 500) * 300.0\n"

    assert_equal(dated_variable['formulas']['2010-01-01']['content'], formula_code_2010)
    assert_equal(dated_variable['formulas']['2011-01-01']['content'], formula_code_2011)
    assert_equal(dated_variable['formulas']['2013-01-01']['content'], formula_code_2013)


def test_dated_variable_with_no_start():
    response = subject.get('/variable/contribution_sociale')
    variable = json.loads(response.data)
    assert_items_equal(variable['formulas'], ['0001-01-01', '1880-01-01'])
    assert_in('function_avant_1880', variable['formulas']['0001-01-01']['content'])


def test_interrupted_dated_variable():
    response = subject.get('/variable/rmi')
    variable = json.loads(response.data)
    assert_is_none(variable['formulas']['2010-01-01'])


def test_dated_variable_with_start_and_stop_date():
    response = subject.get('/variable/api')
    variable = json.loads(response.data)
    assert_items_equal(variable['formulas'], ['2000-01-01', '2005-01-01', '2010-01-01'])
    assert_is_none(variable['formulas']['2010-01-01'])
    assert_in('function_2005', variable['formulas']['2005-01-01']['content'])
    assert_in('function_2000', variable['formulas']['2000-01-01']['content'])
