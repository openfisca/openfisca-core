from http import client
import json
import pytest
import re


def assert_items_equal(x, y):
    assert set(x) == set(y)


GITHUB_URL_REGEX = r'^https://github\.com/openfisca/country-template/blob/\d+\.\d+\.\d+((.dev|rc)\d+)?/openfisca_country_template/variables/(.)+\.py#L\d+-L\d+$'


# /variables


@pytest.fixture(scope="module")
def variables_response(test_client):
    variables_response = test_client.get("/variables")
    return variables_response


def test_return_code(variables_response):
    assert variables_response.status_code == client.OK


def test_response_data(variables_response):
    variables = json.loads(variables_response.data.decode('utf-8'))
    assert variables['birth'] == {
        'description': 'Birth date',
        'href': 'http://localhost/variable/birth'
        }


# /variable/<id>


def test_error_code_non_existing_variable(test_client):
    response = test_client.get('/variable/non_existing_variable')
    assert response.status_code == client.NOT_FOUND


@pytest.fixture(scope="module")
def input_variable_response(test_client):
    input_variable_response = test_client.get('/variable/birth')
    return input_variable_response


def test_return_code_existing_input_variable(input_variable_response):
    assert input_variable_response.status_code == client.OK


def check_input_variable_value(key, expected_value, input_variable=None):
    assert input_variable[key] == expected_value


@pytest.mark.parametrize("expected_values", [
    ('description', 'Birth date'),
    ('valueType', 'Date'),
    ('defaultValue', '1970-01-01'),
    ('definitionPeriod', 'ETERNITY'),
    ('entity', 'person'),
    ('references', ['https://en.wiktionary.org/wiki/birthdate']),
    ])
def test_input_variable_value(expected_values, input_variable_response):
    input_variable = json.loads(input_variable_response.data.decode('utf-8'))

    check_input_variable_value(*expected_values, input_variable=input_variable)


def test_input_variable_github_url(test_client):
    input_variable_response = test_client.get('/variable/income_tax')
    input_variable = json.loads(input_variable_response.data.decode('utf-8'))

    assert re.match(GITHUB_URL_REGEX, input_variable['source'])


def test_return_code_existing_variable(test_client):
    variable_response = test_client.get('/variable/income_tax')
    assert variable_response.status_code == client.OK


def check_variable_value(key, expected_value, variable=None):
    assert variable[key] == expected_value


@pytest.mark.parametrize("expected_values", [
    ('description', 'Income tax'),
    ('valueType', 'Float'),
    ('defaultValue', 0),
    ('definitionPeriod', 'MONTH'),
    ('entity', 'person'),
    ])
def test_variable_value(expected_values, test_client):
    variable_response = test_client.get('/variable/income_tax')
    variable = json.loads(variable_response.data.decode('utf-8'))
    check_variable_value(*expected_values, variable=variable)


def test_variable_formula_github_link(test_client):
    variable_response = test_client.get('/variable/income_tax')
    variable = json.loads(variable_response.data.decode('utf-8'))
    assert re.match(GITHUB_URL_REGEX, variable['formulas']['0001-01-01']['source'])


def test_variable_formula_content(test_client):
    variable_response = test_client.get('/variable/income_tax')
    variable = json.loads(variable_response.data.decode('utf-8'))
    content = variable['formulas']['0001-01-01']['content']
    assert "def formula(person, period, parameters):" in content
    assert "return person(\"salary\", period) * parameters(period).taxes.income_tax_rate" in content


def test_null_values_are_dropped(test_client):
    variable_response = test_client.get('/variable/age')
    variable = json.loads(variable_response.data.decode('utf-8'))
    assert 'references' not in variable.keys()


def test_variable_with_start_and_stop_date(test_client):
    response = test_client.get('/variable/housing_allowance')
    variable = json.loads(response.data.decode('utf-8'))
    assert_items_equal(variable['formulas'], ['1980-01-01', '2016-12-01'])
    assert variable['formulas']['2016-12-01'] is None
    assert 'formula' in variable['formulas']['1980-01-01']['content']


def test_variable_with_enum(test_client):
    response = test_client.get('/variable/housing_occupancy_status')
    variable = json.loads(response.data.decode('utf-8'))
    assert variable['valueType'] == 'String'
    assert variable['defaultValue'] == 'tenant'
    assert 'possibleValues' in variable.keys()
    assert variable['possibleValues'] == {
        'free_lodger': 'Free lodger',
        'homeless': 'Homeless',
        'owner': 'Owner',
        'tenant': 'Tenant'}


@pytest.fixture(scope="module")
def dated_variable_response(test_client):
    dated_variable_response = test_client.get('/variable/basic_income')
    return dated_variable_response


def test_return_code_existing_dated_variable(dated_variable_response):
    assert dated_variable_response.status_code == client.OK


def test_dated_variable_formulas_dates(dated_variable_response):
    dated_variable = json.loads(dated_variable_response.data.decode('utf-8'))
    assert_items_equal(dated_variable['formulas'], ['2016-12-01', '2015-12-01'])


def test_dated_variable_formulas_content(dated_variable_response):
    dated_variable = json.loads(dated_variable_response.data.decode('utf-8'))
    formula_code_2016 = dated_variable['formulas']['2016-12-01']['content']
    formula_code_2015 = dated_variable['formulas']['2015-12-01']['content']

    assert "def formula_2016_12(person, period, parameters):" in formula_code_2016
    assert "return" in formula_code_2016
    assert "def formula_2015_12(person, period, parameters):" in formula_code_2015
    assert "return" in formula_code_2015


def test_variable_encoding(test_client):
    variable_response = test_client.get('/variable/pension')
    assert variable_response.status_code == client.OK


def test_variable_documentation(test_client):
    response = test_client.get('/variable/housing_allowance')
    variable = json.loads(response.data.decode('utf-8'))
    assert variable['documentation'] == "This allowance was introduced on the 1st of Jan 1980.\nIt disappeared in Dec 2016."

    formula_documentation = variable['formulas']['1980-01-01']['documentation']
    assert "Housing allowance." in formula_documentation
    assert "Calculating it before this date will always return the variable default value, 0." in formula_documentation
