# -*- coding: utf-8 -*-

from http.client import OK, NOT_FOUND
import json
import pytest
from nose.tools import assert_equal, assert_regexp_matches, assert_in, assert_is_none, assert_not_in
from . import subject


def assert_items_equal(x, y):
    assert set(x) == set(y)


# /variables

variables_response = subject.get('/variables')
GITHUB_URL_REGEX = r'^https://github\.com/openfisca/country-template/blob/\d+\.\d+\.\d+((.dev|rc)\d+)?/openfisca_country_template/variables/(.)+\.py#L\d+-L\d+$'


def test_return_code():
    assert variables_response.status_code == OK


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
    assert response.status_code == NOT_FOUND


input_variable_response = subject.get('/variable/birth')
input_variable = json.loads(input_variable_response.data.decode('utf-8'))


def test_return_code_existing_input_variable():
    assert input_variable_response.status_code == OK


def check_input_variable_value(key, expected_value):
    assert input_variable[key] == expected_value


@pytest.mark.parametrize("expected_values", [
    ('description', 'Birth date'),
    ('valueType', 'Date'),
    ('defaultValue', '1970-01-01'),
    ('definitionPeriod', 'ETERNITY'),
    ('entity', 'person'),
    ('references', ['https://en.wiktionary.org/wiki/birthdate']),
    ])
def test_input_variable_value(expected_values):
    check_input_variable_value(*expected_values)


def test_input_variable_github_url():
    assert_regexp_matches(input_variable['source'], GITHUB_URL_REGEX)


variable_response = subject.get('/variable/income_tax')
variable = json.loads(variable_response.data.decode('utf-8'))


def test_return_code_existing_variable():
    assert variable_response.status_code == OK


def check_variable_value(key, expected_value):
    assert variable[key] == expected_value


@pytest.mark.parametrize("expected_values", [
    ('description', 'Income tax'),
    ('valueType', 'Float'),
    ('defaultValue', 0),
    ('definitionPeriod', 'MONTH'),
    ('entity', 'person'),
    ])
def test_variable_value(expected_values):
    check_variable_value(*expected_values)


def test_variable_formula_github_link():
    assert_regexp_matches(variable['formulas']['0001-01-01']['source'], GITHUB_URL_REGEX)


def test_variable_formula_content():
    formula_code = "def formula(person, period, parameters):\n    return person('salary', period) * parameters(period).taxes.income_tax_rate\n"
    assert variable['formulas']['0001-01-01']['content'] == formula_code


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
    assert variable['valueType'] == 'String'
    assert variable['defaultValue'] == 'tenant'
    assert_in('possibleValues', variable.keys())
    assert_equal(variable['possibleValues'], {
        'free_lodger': 'Free lodger',
        'homeless': 'Homeless',
        'owner': 'Owner',
        'tenant': 'Tenant'})


dated_variable_response = subject.get('/variable/basic_income')
dated_variable = json.loads(dated_variable_response.data.decode('utf-8'))


def test_return_code_existing_dated_variable():
    assert dated_variable_response.status_code == OK


def test_dated_variable_formulas_dates():
    assert_items_equal(dated_variable['formulas'], ['2016-12-01', '2015-12-01'])


def test_dated_variable_formulas_content():
    formula_code_2016 = dated_variable['formulas']['2016-12-01']['content']
    formula_code_2015 = dated_variable['formulas']['2015-12-01']['content']

    assert "def formula_2016_12(person, period, parameters):" in formula_code_2016
    assert "return" in formula_code_2016
    assert "def formula_2015_12(person, period, parameters):" in formula_code_2015
    assert "return" in formula_code_2015


def test_variable_encoding():
    variable_response = subject.get('/variable/pension')
    assert variable_response.status_code == OK


def test_variable_documentation():
    response = subject.get('/variable/housing_allowance')
    variable = json.loads(response.data.decode('utf-8'))
    assert_equal(variable['documentation'],
        "This allowance was introduced on the 1st of Jan 1980.\nIt disappeared in Dec 2016.")

    assert_equal(variable['formulas']['1980-01-01']['documentation'],
        "\nTo compute this allowance, the 'rent' value must be provided for the same month, but 'housing_occupancy_status' is not necessary.\n")
