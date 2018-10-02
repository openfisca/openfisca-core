# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from http.client import OK, NOT_FOUND
import json
from nose.tools import assert_equal, assert_regexp_matches, assert_in, assert_is_none, assert_not_in
from . import subject


def assert_items_equal(x, y):
    assert_equal(set(x), set(y))


# /variables

variables_response = subject.get('/variables')
GITHUB_URL_REGEX = '^https://github\.com/openfisca/country-template/blob/\d+\.\d+\.\d+((.dev|rc)\d+)?/openfisca_country_template/variables/(.)+\.py#L\d+-L\d+$'


def test_return_code():
    assert_equal(variables_response.status_code, OK)


def test_response_data():
    variables = json.loads(variables_response.data.decode('utf-8'))
    assert_equal(
        variables['birth'],
        {
            'description': 'Birth date',
            'href': 'http://localhost/variable/birth'
            }
        )


# /variable/<id>


def test_error_code_non_existing_variable():
    response = subject.get('/variable/non_existing_variable')
    assert_equal(response.status_code, NOT_FOUND)


input_variable_response = subject.get('/variable/birth')
input_variable = json.loads(input_variable_response.data.decode('utf-8'))


def test_return_code_existing_input_variable():
    assert_equal(input_variable_response.status_code, OK)


def check_input_variable_value(key, expected_value):
    assert_equal(input_variable[key], expected_value)


def test_input_variable_value():
    expected_values = {
        'description': 'Birth date',
        'valueType': 'Date',
        'defaultValue': '1970-01-01',
        'definitionPeriod': 'ETERNITY',
        'entity': 'person',
        'references': ['https://en.wiktionary.org/wiki/birthdate'],
        }

    for key, expected_value in expected_values.items():
        yield check_input_variable_value, key, expected_value


def test_input_variable_github_url():
    assert_regexp_matches(input_variable['source'], GITHUB_URL_REGEX)


variable_response = subject.get('/variable/income_tax')
variable = json.loads(variable_response.data.decode('utf-8'))


def test_return_code_existing_variable():
    assert_equal(variable_response.status_code, OK)


def check_variable_value(key, expected_value):
    assert_equal(variable[key], expected_value)


def test_variable_value():
    expected_values = {
        'description': 'Income tax',
        'valueType': 'Float',
        'defaultValue': 0,
        'definitionPeriod': 'MONTH',
        'entity': 'person',
        }

    for key, expected_value in expected_values.items():
        yield check_variable_value, key, expected_value


def test_variable_formula_github_link():
    assert_regexp_matches(variable['formulas']['0001-01-01']['source'], GITHUB_URL_REGEX)


def test_variable_formula_content():
    formula_code = "def formula(person, period, parameters):\n    return person('salary', period) * parameters(period).taxes.income_tax_rate\n"
    assert_equal(variable['formulas']['0001-01-01']['content'], formula_code)


def test_null_values_are_dropped():
    variable_response = subject.get('/variable/age')
    variable = json.loads(variable_response.data.decode('utf-8'))
    assert_not_in('references', variable.keys())


def test_variable_with_start_and_stop_date():
    response = subject.get('/variable/housing_allowance')
    variable = json.loads(response.data.decode('utf-8'))
    assert_items_equal(variable['formulas'], ['1980-01-01', '2016-12-01'])
    assert_is_none(variable['formulas']['2016-12-01'])
    assert_in('formula', variable['formulas']['1980-01-01']['content'])


def test_variable_with_enum():
    response = subject.get('/variable/housing_occupancy_status')
    variable = json.loads(response.data.decode('utf-8'))
    assert_equal(variable['valueType'], 'String')
    assert_equal(variable['defaultValue'], 'tenant')
    assert_in('possibleValues', variable.keys())
    assert_equal(variable['possibleValues'], {
        'free_lodger': 'Free lodger',
        'homeless': 'Homeless',
        'owner': 'Owner',
        'tenant': 'Tenant'})


dated_variable_response = subject.get('/variable/basic_income')
dated_variable = json.loads(dated_variable_response.data.decode('utf-8'))


def test_return_code_existing_dated_variable():
    assert_equal(dated_variable_response.status_code, OK)


def test_dated_variable_formulas_dates():
    assert_items_equal(dated_variable['formulas'], ['2016-12-01', '2015-12-01'])


def test_dated_variable_formulas_content():
    formula_code_2016 = "def formula_2016_12(person, period, parameters):\n    age_condition = person('age', period) >= parameters(period).general.age_of_majority\n    return age_condition * parameters(period).benefits.basic_income  # This '*' is a vectorial 'if'. See https://openfisca.org/doc/coding-the-legislation/30_case_disjunction.html#simple-multiplication\n"
    formula_code_2015 = "def formula_2015_12(person, period, parameters):\n    age_condition = person('age', period) >= parameters(period).general.age_of_majority\n    salary_condition = person('salary', period) == 0\n    return age_condition * salary_condition * parameters(period).benefits.basic_income  # The '*' is also used as a vectorial 'and'. See https://openfisca.org/doc/coding-the-legislation/25_vectorial_computing.html#forbidden-operations-and-alternatives\n"

    assert_equal(dated_variable['formulas']['2016-12-01']['content'], formula_code_2016)
    assert_equal(dated_variable['formulas']['2015-12-01']['content'], formula_code_2015)


def test_variable_encoding():
    variable_response = subject.get('/variable/pension')
    assert_equal(variable_response.status_code, OK)


def test_variable_documentation():
    response = subject.get('/variable/housing_allowance')
    variable = json.loads(response.data.decode('utf-8'))
    assert_equal(variable['documentation'],
        "This allowance was introduced on the 1st of Jan 1980.\nIt disappeared in Dec 2016.")

    assert_equal(variable['formulas']['1980-01-01']['documentation'],
        "\nTo compute this allowance, the 'rent' value must be provided for the same month, but 'housing_occupancy_status' is not necessary.\n")
