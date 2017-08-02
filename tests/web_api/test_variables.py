# -*- coding: utf-8 -*-

from httplib import OK, NOT_FOUND
import json
from nose.tools import assert_equal, assert_regexp_matches, assert_items_equal, assert_in, assert_is_none, assert_not_in
from . import subject

# /variables

variables_response = subject.get('/variables')
GITHUB_URL_REGEX = '^https://github\.com/openfisca/openfisca-country-template/blob/\d+\.\d+\.\d+((.dev|rc)\d+)?/openfisca_country_template/variables/(.)+\.py#L\d+-L\d+$'


def test_return_code():
    assert_equal(variables_response.status_code, OK)


def test_response_data():
    variables = json.loads(variables_response.data)
    assert_equal(
        variables[u'birth'],
        {u'description': u'Birth date'}
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
        u'description': u'Birth date',
        u'valueType': u'Date',
        u'defaultValue': u'1970-01-01',
        u'definitionPeriod': u'ETERNITY',
        u'entity': u'person',
        u'references': [u'https://en.wiktionary.org/wiki/birthdate'],
        }

    for key, expected_value in expected_values.iteritems():
        yield check_input_variable_value, key, expected_value


def test_input_variable_github_url():
    assert_regexp_matches(input_variable['source'], GITHUB_URL_REGEX)


variable_response = subject.get('/variable/income_tax')
variable = json.loads(variable_response.data)


def test_return_code_existing_variable():
    assert_equal(variable_response.status_code, OK)


def check_variable_value(key, expected_value):
    assert_equal(variable[key], expected_value)


def test_variable_value():
    expected_values = {
        u'description': u'Income tax',
        u'valueType': u'Float',
        u'defaultValue': 0,
        u'definitionPeriod': u'MONTH',
        u'entity': u'person',
        }

    for key, expected_value in expected_values.iteritems():
        yield check_variable_value, key, expected_value


def test_variable_formula_github_link():
    assert_regexp_matches(variable['formulas']['0001-01-01']['source'], GITHUB_URL_REGEX)


def test_variable_formula_content():
    formula_code = "def formula(person, period, legislation):\n    return person('salary', period) * legislation(period).taxes.income_tax_rate\n"
    assert_equal(variable['formulas']['0001-01-01']['content'], formula_code)


def test_null_values_are_dropped():
    variable_response = subject.get('/variable/age')
    variable = json.loads(variable_response.data)
    assert_not_in('references', variable.keys())


def test_variable_with_start_and_stop_date():
    response = subject.get('/variable/housing_allowance')
    variable = json.loads(response.data)
    assert_items_equal(variable['formulas'], ['1980-01-01', '2016-12-01'])
    assert_is_none(variable['formulas']['2016-12-01'])
    assert_in('formula', variable['formulas']['1980-01-01']['content'])


def test_variable_with_enum():
    response = subject.get('/variable/housing_occupancy_status')
    variable = json.loads(response.data)
    assert_equal(variable['valueType'], 'String')
    assert_in('possibleValues', variable.keys())
    assert_equal(variable['possibleValues'], [
        u'Tenant',
        u'Owner',
        u'Free logder',
        u'Homeless']
        )


dated_variable_response = subject.get('/variable/basic_income')
dated_variable = json.loads(dated_variable_response.data)


def test_return_code_existing_dated_variable():
    assert_equal(dated_variable_response.status_code, OK)


def test_dated_variable_formulas_dates():
    assert_items_equal(dated_variable['formulas'], ['2016-12-01', '2015-12-01'])


def test_dated_variable_formulas_content():
    formula_code_2016 = "def formula_2016_12(person, period, legislation):\n    age_condition = person('age', period) >= legislation(period).general.age_of_majority\n    return age_condition * legislation(period).benefits.basic_income  # This '*' is a vectorial 'if'. See https://doc.openfisca.fr/coding-the-legislation/30_case_disjunction.html#simple-multiplication\n"
    formula_code_2015 = "def formula_2015_12(person, period, legislation):\n    age_condition = person('age', period) >= legislation(period).general.age_of_majority\n    salary_condition = person('salary', period) == 0\n    return age_condition * salary_condition * legislation(period).benefits.basic_income  # The '*' is also used as a vectorial 'and'. See https://doc.openfisca.fr/coding-the-legislation/25_vectorial_computing.html#forbidden-operations-and-alternatives\n"

    assert_equal(dated_variable['formulas']['2016-12-01']['content'], formula_code_2016)
    assert_equal(dated_variable['formulas']['2015-12-01']['content'], formula_code_2015)
