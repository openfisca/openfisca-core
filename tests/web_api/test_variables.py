# -*- coding: utf-8 -*-

from datetime import date
from http.client import OK, NOT_FOUND
import json
from numpy import where
import re

import pytest

from openfisca_core.indexed_enums import Enum
from openfisca_core.periods import MONTH, ETERNITY
from openfisca_core.variables import Variable
from openfisca_web_api.app import create_app
from .conftest import Person, Household


def assert_items_equal(x, y):
    assert set(x) == set(y)


GITHUB_URL_REGEX = r'^https://github\.com/openfisca/openfisca-core/blob/\d+\.\d+\.\d+((.dev|rc)\d+)?/tests/web_api/(.)+\.py#L\d+-L\d+$'


@pytest.fixture(scope="module")
def test_client(test_tax_benefit_system):

    ###
    # In this section you define the mock Variables you will need for tests in this module
    class birth(Variable):
        value_type = date
        default_value = date(1970, 1, 1)  # By default, if no value is set for a simulation, we consider the people involved in a simulation to be born on the 1st of Jan 1970.
        entity = Person
        label = "Birth date"
        definition_period = ETERNITY  # This variable cannot change over time.
        reference = "https://en.wiktionary.org/wiki/birthdate"

    class income_tax(Variable):
        value_type = float
        entity = Person
        definition_period = MONTH
        label = "Income tax"
        reference = "https://law.gov.example/income_tax"  # Always use the most official source

        def formula(person, period, parameters):
            """
            Income tax.

            The formula to compute the income tax for a given person at a given period
            """
            return person("salary", period) * parameters(period).taxes.income_tax_rate

    class age(Variable):
        value_type = int
        entity = Person
        definition_period = MONTH
        label = "Person's age (in years)"

        def formula(person, period, _parameters):
            """
            Person's age (in years).

            A person's age is computed according to its birth date.
            """
            birth = person("birth", period)
            birth_year = birth.astype("datetime64[Y]").astype(int) + 1970
            birth_month = birth.astype("datetime64[M]").astype(int) % 12 + 1
            birth_day = (birth - birth.astype("datetime64[M]") + 1).astype(int)

            is_birthday_past = (birth_month < period.start.month) + (birth_month == period.start.month) * (birth_day <= period.start.day)

            return (period.start.year - birth_year) - where(is_birthday_past, 0, 1)  # If the birthday is not passed this year, subtract one year

    class housing_allowance(Variable):
        value_type = float
        entity = Household
        definition_period = MONTH
        label = "Housing allowance"
        reference = "https://law.gov.example/housing_allowance"  # Always use the most official source
        end = "2016-11-30"  # This allowance was removed on the 1st of Dec 2016. Calculating it before this date will always return the variable default value, 0.
        unit = "currency-EUR"
        documentation = """
        This allowance was introduced on the 1st of Jan 1980.
        It disappeared in Dec 2016.
        """

        def formula_1980(household, period, parameters):
            """
            Housing allowance.

            This allowance was introduced on the 1st of Jan 1980.
            Calculating it before this date will always return the variable default value, 0.

            To compute this allowance, the 'rent' value must be provided for the same month,
            but 'housing_occupancy_status' is not necessary.
            """
            return household("rent", period) * parameters(period).benefits.housing_allowance

    class HousingOccupancyStatus(Enum):
        __order__ = "owner tenant free_lodger homeless"
        owner = "Owner"
        tenant = "Tenant"
        free_lodger = "Free lodger"
        homeless = "Homeless"

    class housing_occupancy_status(Variable):
        value_type = Enum
        possible_values = HousingOccupancyStatus
        default_value = HousingOccupancyStatus.tenant
        entity = Household
        definition_period = MONTH
        label = "Legal housing situation of the household concerning their main residence"

    class basic_income(Variable):
        value_type = float
        entity = Person
        definition_period = MONTH
        label = "Basic income provided to adults"
        reference = "https://law.gov.example/basic_income"  # Always use the most official source

        def formula_2016_12(person, period, parameters):
            """
            Basic income provided to adults.

            Since Dec 1st 2016, the basic income is provided to any adult, without considering their income.
            """
            age_condition = person("age", period) >= parameters(period).general.age_of_majority
            return age_condition * parameters(period).benefits.basic_income  # This '*' is a vectorial 'if'. See https://openfisca.org/doc/coding-the-legislation/25_vectorial_computing.html#control-structures

        def formula_2015_12(person, period, parameters):
            """
            Basic income provided to adults.

            From Dec 1st 2015 to Nov 30 2016, the basic income is provided to adults who have no income.
            Before Dec 1st 2015, the basic income does not exist in the law, and calculating it returns its default value, which is 0.
            """
            age_condition = person("age", period) >= parameters(period).general.age_of_majority
            salary_condition = person("salary", period) == 0
            return age_condition * salary_condition * parameters(period).benefits.basic_income  # The '*' is also used as a vectorial 'and'. See https://openfisca.org/doc/coding-the-legislation/25_vectorial_computing.html#boolean-operations

    class pension(Variable):
        value_type = float
        entity = Person
        definition_period = MONTH
        label = "Pension for the elderly. Pension attribuée aux personnes âgées. تقاعد."
        reference = ["https://fr.wikipedia.org/wiki/Retraite_(économie)", "https://ar.wikipedia.org/wiki/تقاعد"]

        def formula(person, period, parameters):
            """
            Pension for the elderly.

            A person's pension depends on their birth date.
            In French: retraite selon l'âge.
            In Arabic: تقاعد.
            """
            age_condition = person("age", period) >= parameters(period).general.age_of_retirement
            return age_condition

    ###
    # Add the Variables above to the `test_tax_benefit_system` fixture
    test_tax_benefit_system.add_variable(birth)
    test_tax_benefit_system.add_variable(income_tax)
    test_tax_benefit_system.add_variable(age)
    test_tax_benefit_system.add_variable(housing_allowance)
    test_tax_benefit_system.add_variable(housing_occupancy_status)
    test_tax_benefit_system.add_variable(basic_income)
    test_tax_benefit_system.add_variable(pension)

    ###
    # Create the test API client
    app = create_app(test_tax_benefit_system)
    return app.test_client()


# /variables


@pytest.fixture(scope="module")
def variables_response(test_client):
    variables_response = test_client.get("/variables")
    return variables_response


def test_return_code(variables_response):
    assert variables_response.status_code == OK


def test_response_data(variables_response):
    variables = json.loads(variables_response.data.decode('utf-8'))
    assert variables['birth'] == {
        'description': 'Birth date',
        'href': 'http://localhost/variable/birth'
        }


# /variable/<id>


def test_error_code_non_existing_variable(test_client):
    response = test_client.get('/variable/non_existing_variable')
    assert response.status_code == NOT_FOUND


@pytest.fixture(scope="module")
def input_variable_response(test_client):
    input_variable_response = test_client.get('/variable/birth')
    return input_variable_response


def test_return_code_existing_input_variable(input_variable_response):
    assert input_variable_response.status_code == OK


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
    assert variable_response.status_code == OK


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


def test_variable_formula_content():
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
    assert dated_variable_response.status_code == OK


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
    assert variable_response.status_code == OK


def test_variable_documentation(test_client):
    response = test_client.get('/variable/housing_allowance')
    variable = json.loads(response.data.decode('utf-8'))
    assert variable['documentation'] == "This allowance was introduced on the 1st of Jan 1980.\nIt disappeared in Dec 2016."

    formula_documentation = variable['formulas']['1980-01-01']['documentation']
    assert "Housing allowance." in formula_documentation
    assert "Calculating it before this date will always return the variable default value, 0." in formula_documentation
