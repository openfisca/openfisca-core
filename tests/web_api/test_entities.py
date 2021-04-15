# -*- coding: utf-8 -*-

from http import client
import json
import pytest

from openfisca_country_template import entities

from openfisca_web_api import app


# /entities


@pytest.fixture(scope="module")
def test_client(tax_benefit_system):
    """ This module-scoped fixture creates an API client for the TBS defined in the `tax_benefit_system`
        fixture. This `tax_benefit_system` is mutable, so you can add/update variables. Example:

        ```
            from openfisca_country_template import entities
            from openfisca_core import periods
            from openfisca_core.variables import Variable
            ...

            class new_variable(Variable):
                value_type = float
                entity = entities.Person
                definition_period = periods.MONTH
                label = "New variable"
                reference = "https://law.gov.example/new_variable"  # Always use the most official source

            tax_benefit_system.add_variable(new_variable)
            flask_app = app.create_app(tax_benefit_system)
        ```
    """

    # Create the test API client
    flask_app = app.create_app(tax_benefit_system)
    return flask_app.test_client()


def test_return_code(test_client):
    entities_response = test_client.get('/entities')
    assert entities_response.status_code == client.OK


def test_response_data(test_client):
    entities_response = test_client.get('/entities')
    entities_dict = json.loads(entities_response.data.decode('utf-8'))
    test_documentation = entities.Household.doc.strip()

    assert entities_dict['household'] == {
        'description': 'All the people in a family or group who live together in the same place.',
        'documentation': test_documentation,
        'plural': 'households',
        'roles': {
            'child': {
                'description': 'Other individuals living in the household.',
                'plural': 'children',
                },
            'parent': {
                'description': 'The one or two adults in charge of the household.',
                'plural': 'parents',
                'max': 2,
                }
            }
        }
