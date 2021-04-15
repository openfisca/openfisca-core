import copy
import dpath
import json
from http import client
import os
import pytest

from openfisca_country_template.situation_examples import couple

from openfisca_web_api import app


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


def post_json(_client, data = None, file = None):
    if file:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', file)
        with open(file_path, 'r') as file:
            data = file.read()
    return _client.post('/calculate', data = data, content_type = 'application/json')


def check_response(_client, data, expected_error_code, path_to_check, content_to_check):
    response = post_json(_client, data)
    assert response.status_code == expected_error_code
    json_response = json.loads(response.data.decode('utf-8'))
    if path_to_check:
        content = dpath.util.get(json_response, path_to_check)
        assert content_to_check in content


@pytest.mark.parametrize("test", [
    ('{"a" : "x", "b"}', client.BAD_REQUEST, 'error', 'Invalid JSON'),
    ('["An", "array"]', client.BAD_REQUEST, 'error', 'Invalid type'),
    ('{"persons": {}}', client.BAD_REQUEST, 'persons', 'At least one person'),
    ('{"persons": {"bob": {}}, "unknown_entity": {}}', client.BAD_REQUEST, 'unknown_entity', 'entities are not found',),
    ('{"persons": {"bob": {}}, "households": {"dupont": {"parents": {}}}}', client.BAD_REQUEST, 'households/dupont/parents', 'type',),
    ('{"persons": {"bob": {"unknown_variable": {}}}}', client.NOT_FOUND, 'persons/bob/unknown_variable', 'You tried to calculate or to set',),
    ('{"persons": {"bob": {"housing_allowance": {}}}}', client.BAD_REQUEST, 'persons/bob/housing_allowance', "You tried to compute the variable 'housing_allowance' for the entity 'persons'",),
    ('{"persons": {"bob": {"salary": 4000 }}}', client.BAD_REQUEST, 'persons/bob/salary', 'period',),
    ('{"persons": {"bob": {"salary": {"2017-01": "toto"} }}}', client.BAD_REQUEST, 'persons/bob/salary/2017-01', 'expected type number',),
    ('{"persons": {"bob": {"salary": {"2017-01": {}} }}}', client.BAD_REQUEST, 'persons/bob/salary/2017-01', 'expected type number',),
    ('{"persons": {"bob": {"age": {"2017-01": "toto"} }}}', client.BAD_REQUEST, 'persons/bob/age/2017-01', 'expected type integer',),
    ('{"persons": {"bob": {"birth": {"2017-01": "toto"} }}}', client.BAD_REQUEST, 'persons/bob/birth/2017-01', 'Can\'t deal with date',),
    ('{"persons": {"bob": {}}, "households": {"household": {"parents": ["unexpected_person_id"]}}}', client.BAD_REQUEST, 'households/household/parents', 'has not been declared in persons',),
    ('{"persons": {"bob": {}}, "households": {"household": {"parents": ["bob", "bob"]}}}', client.BAD_REQUEST, 'households/household/parents', 'has been declared more than once',),
    ('{"persons": {"bob": {}}, "households": {"household": {"parents": ["bob", {}]}}}', client.BAD_REQUEST, 'households/household/parents/1', 'Invalid type',),
    ('{"persons": {"bob": {"salary": {"invalid period": 2000 }}}}', client.BAD_REQUEST, 'persons/bob/salary', 'Expected a period',),
    ('{"persons": {"bob": {"salary": {"invalid period": null }}}}', client.BAD_REQUEST, 'persons/bob/salary', 'Expected a period',),
    ('{"persons": {"bob": {"basic_income": {"2017": 2000 }}}, "households": {"household": {"parents": ["bob"]}}}', client.BAD_REQUEST, 'persons/bob/basic_income/2017', '"basic_income" can only be set for one month',),
    ('{"persons": {"bob": {"salary": {"ETERNITY": 2000 }}}, "households": {"household": {"parents": ["bob"]}}}', client.BAD_REQUEST, 'persons/bob/salary/ETERNITY', 'salary is only defined for months',),
    ('{"persons": {"alice": {}, "bob": {}, "charlie": {}}, "households": {"_": {"parents": ["alice", "bob", "charlie"]}}}', client.BAD_REQUEST, 'households/_/parents', 'at most 2 parents in a household',),
    ])
def test_responses(test_client, test):
    check_response(test_client, *test)


def test_basic_calculation(test_client):
    simulation_json = json.dumps({
        "persons": {
            "bill": {
                "birth": {
                    "2017-12": "1980-01-01"
                    },
                "age": {
                    "2017-12": None
                    },
                "salary": {
                    "2017-12": 2000
                    },
                "basic_income": {
                    "2017-12": None
                    },
                "income_tax": {
                    "2017-12": None
                    }
                },
            "bob": {
                "salary": {
                    "2017-12": 15000
                    },
                "basic_income": {
                    "2017-12": None
                    },
                "social_security_contribution": {
                    "2017-12": None
                    }
                },
            },
        "households": {
            "first_household": {
                "parents": ['bill', 'bob'],
                "housing_tax": {
                    "2017": None
                    },
                "accommodation_size": {
                    "2017-01": 300
                    }
                },
            }
        })

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.OK
    response_json = json.loads(response.data.decode('utf-8'))
    assert dpath.get(response_json, 'persons/bill/basic_income/2017-12') == 600  # Universal basic income
    assert dpath.get(response_json, 'persons/bill/income_tax/2017-12') == 300  # 15% of the salary
    assert dpath.get(response_json, 'persons/bill/age/2017-12') == 37  # 15% of the salary
    assert dpath.get(response_json, 'persons/bob/basic_income/2017-12') == 600
    assert dpath.get(response_json, 'persons/bob/social_security_contribution/2017-12') == 816  # From social_security_contribution.yaml test
    assert dpath.get(response_json, 'households/first_household/housing_tax/2017') == 3000


def test_enums_sending_identifier(test_client):
    simulation_json = json.dumps({
        "persons": {
            "bill": {}
            },
        "households": {
            "_": {
                "parents": ["bill"],
                "housing_tax": {
                    "2017": None
                    },
                "accommodation_size": {
                    "2017-01": 300
                    },
                "housing_occupancy_status": {
                    "2017-01": "free_lodger"
                    }
                }
            }
        })

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.OK
    response_json = json.loads(response.data.decode('utf-8'))
    assert dpath.get(response_json, 'households/_/housing_tax/2017') == 0


def test_enum_output(test_client):
    simulation_json = json.dumps({
        "persons": {
            "bill": {},
            },
        "households": {
            "_": {
                "parents": ["bill"],
                "housing_occupancy_status": {
                    "2017-01": None
                    }
                },
            }
        })

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.OK
    response_json = json.loads(response.data.decode('utf-8'))
    assert dpath.get(response_json, "households/_/housing_occupancy_status/2017-01") == "tenant"


def test_enum_wrong_value(test_client):
    simulation_json = json.dumps({
        "persons": {
            "bill": {},
            },
        "households": {
            "_": {
                "parents": ["bill"],
                "housing_occupancy_status": {
                    "2017-01": "Unknown value lodger"
                    }
                },
            }
        })

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.BAD_REQUEST
    response_json = json.loads(response.data.decode('utf-8'))
    message = "Possible values are ['owner', 'tenant', 'free_lodger', 'homeless']"
    text = dpath.get(response_json, "households/_/housing_occupancy_status/2017-01")
    assert message in text


def test_encoding_variable_value(test_client):
    simulation_json = json.dumps({
        "persons": {
            "toto": {}
            },
        "households": {
            "_": {
                "housing_occupancy_status": {
                    "2017-07": "Locataire ou sous-locataire d‘un logement loué vide non-HLM"

                    },
                "parent": [
                    "toto",
                    ]
                }
            }
        })

    # No UnicodeDecodeError
    response = post_json(test_client, simulation_json)
    assert response.status_code == client.BAD_REQUEST, response.data.decode('utf-8')
    response_json = json.loads(response.data.decode('utf-8'))
    message = "'Locataire ou sous-locataire d‘un logement loué vide non-HLM' is not a known value for 'housing_occupancy_status'. Possible values are "
    text = dpath.get(response_json, 'households/_/housing_occupancy_status/2017-07')
    assert message in text


def test_encoding_entity_name(test_client):
    simulation_json = json.dumps({
        "persons": {
            "O‘Ryan": {},
            "Renée": {}
            },
        "households": {
            "_": {
                "parents": [
                    "O‘Ryan",
                    "Renée"
                    ]
                }
            }
        })

    # No UnicodeDecodeError
    response = post_json(test_client, simulation_json)
    response_json = json.loads(response.data.decode('utf-8'))

    # In Python 3, there is no encoding issue.
    if response.status_code != client.OK:
        message = "'O‘Ryan' is not a valid ASCII value."
        text = response_json['error']
        assert message in text


def test_encoding_period_id(test_client):
    simulation_json = json.dumps({
        "persons": {
            "bill": {
                "salary": {
                    "2017": 60000
                    }
                },
            "bell": {
                "salary": {
                    "2017": 60000
                    }
                }
            },
        "households": {
            "_": {
                "parents": ["bill", "bell"],
                "housing_tax": {
                    "à": 400
                    },
                "accommodation_size": {
                    "2017-01": 300
                    },
                "housing_occupancy_status": {
                    "2017-01": "tenant"
                    }
                }
            }
        })

    # No UnicodeDecodeError
    response = post_json(test_client, simulation_json)
    assert response.status_code == client.BAD_REQUEST
    response_json = json.loads(response.data.decode('utf-8'))

    # In Python 3, there is no encoding issue.
    if "Expected a period" not in str(response.data):
        message = "'à' is not a valid ASCII value."
        text = response_json['error']
        assert message in text


def test_str_variable(test_client):
    new_couple = copy.deepcopy(couple)
    new_couple['households']['_']['postal_code'] = {'2017-01': None}
    simulation_json = json.dumps(new_couple)

    response = test_client.post('/calculate', data = simulation_json, content_type = 'application/json')

    assert response.status_code == client.OK


def test_periods(test_client):
    simulation_json = json.dumps({
        "persons": {
            "bill": {}
            },
        "households": {
            "_": {
                "parents": ["bill"],
                "housing_tax": {
                    "2017": None
                    },
                "housing_occupancy_status": {
                    "2017-01": None
                    }
                }
            }
        })

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.OK

    response_json = json.loads(response.data.decode('utf-8'))

    yearly_variable = dpath.get(response_json, 'households/_/housing_tax')  # web api year is an int
    assert yearly_variable == {'2017': 200.0}

    monthly_variable = dpath.get(response_json, 'households/_/housing_occupancy_status')  # web api month is a string
    assert monthly_variable == {'2017-01': 'tenant'}


def test_gracefully_handle_unexpected_errors(test_client):
    """
    Context
    ========

    Whenever an exception is raised by the calculation engine, the API will try
    to handle it and to provide a useful message to the user (4XX). When the
    unexpected happens, if the exception is available it will be forwarded
    and given to the user even in this worst case scenario (500).

    Scenario
    ========

    Calculate the housing tax due by Bill a thousand years ago.

    Expected behaviour
    ========

    In the `country-template`, Housing Tax is only defined from 2010 onwards.
    The calculation engine should therefore raise an exception `ParameterNotFound`.
    The API is not expecting this, but she should handle the situation nonetheless.
    """
    variable = "housing_tax"
    period = "1234-05-06"

    simulation_json = json.dumps({
        "persons": {
            "bill": {},
            },
        "households": {
            "_": {
                "parents": ["bill"],
                variable: {
                    period: None,
                    },
                }
            }
        })

    response = post_json(test_client, simulation_json)
    assert response.status_code == client.INTERNAL_SERVER_ERROR

    error = json.loads(response.data)["error"]
    assert f"Unable to compute variable '{variable}' for period {period}" in error
