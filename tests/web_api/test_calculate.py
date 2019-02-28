# -*- coding: utf-8 -*-

import os
import json
from http.client import BAD_REQUEST, OK, NOT_FOUND
from copy import deepcopy

import pytest
import dpath

from openfisca_core.commons import to_unicode
from openfisca_country_template.situation_examples import couple

from . import subject


def post_json(data = None, file = None):
    if file:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', file)
        with open(file_path, 'r') as file:
            data = file.read()
    return subject.post('/calculate', data = data, content_type = 'application/json')


def check_response(data, expected_error_code, path_to_check, content_to_check):
    response = post_json(data)
    assert response.status_code == expected_error_code
    json_response = json.loads(response.data.decode('utf-8'))
    if path_to_check:
        content = dpath.util.get(json_response, path_to_check)
        assert content_to_check in content


@pytest.mark.parametrize("test", [
        ('{"a" : "x", "b"}', BAD_REQUEST, 'error', 'Invalid JSON'),
        ('["An", "array"]', BAD_REQUEST, 'error', 'Invalid type'),
        ('{"persons": {}}', BAD_REQUEST, 'persons', 'At least one person'),
        ('{"persons": {"bob": {}}, "unknown_entity": {}}', BAD_REQUEST, 'unknown_entity', 'entities are not found',),
        ('{"persons": {"bob": {}}, "households": {"dupont": {"parents": {}}}}', BAD_REQUEST, 'households/dupont/parents', 'type',),
        ('{"persons": {"bob": {"unknown_variable": {}}}}', NOT_FOUND, 'persons/bob/unknown_variable', 'You tried to calculate or to set',),
        ('{"persons": {"bob": {"housing_allowance": {}}}}', BAD_REQUEST, 'persons/bob/housing_allowance', "You tried to compute the variable 'housing_allowance' for the entity 'persons'",),
        ('{"persons": {"bob": {"salary": 4000 }}}', BAD_REQUEST, 'persons/bob/salary', 'period',),
        ('{"persons": {"bob": {"salary": {"2017-01": "toto"} }}}', BAD_REQUEST, 'persons/bob/salary/2017-01', 'expected type number',),
        ('{"persons": {"bob": {"salary": {"2017-01": {}} }}}', BAD_REQUEST, 'persons/bob/salary/2017-01', 'expected type number',),
        ('{"persons": {"bob": {"age": {"2017-01": "toto"} }}}', BAD_REQUEST, 'persons/bob/age/2017-01', 'expected type integer',),
        ('{"persons": {"bob": {"birth": {"2017-01": "toto"} }}}', BAD_REQUEST, 'persons/bob/birth/2017-01', 'Can\'t deal with date',),
        ('{"persons": {"bob": {}}, "households": {"household": {"parents": ["unexpected_person_id"]}}}', BAD_REQUEST, 'households/household/parents', 'has not been declared in persons',),
        ('{"persons": {"bob": {}}, "households": {"household": {"parents": ["bob", "bob"]}}}', BAD_REQUEST, 'households/household/parents', 'has been declared more than once',),
        ('{"persons": {"bob": {}}, "households": {"household": {"parents": ["bob", {}]}}}', BAD_REQUEST, 'households/household/parents/1', 'Invalid type',),
        ('{"persons": {"bob": {"salary": {"invalid period": 2000 }}}}', BAD_REQUEST, 'persons/bob/salary', 'Expected a period',),
        ('{"persons": {"bob": {"salary": {"invalid period": null }}}}', BAD_REQUEST, 'persons/bob/salary', 'Expected a period',),
        ('{"persons": {"bob": {"basic_income": {"2017": 2000 }}}, "households": {"household": {"parents": ["bob"]}}}', BAD_REQUEST, 'persons/bob/basic_income/2017', 'basic_income is only defined for months',),
        ('{"persons": {"bob": {"salary": {"ETERNITY": 2000 }}}, "households": {"household": {"parents": ["bob"]}}}', BAD_REQUEST, 'persons/bob/salary/ETERNITY', 'salary is only defined for months',),
        ('{"persons": {"bob": {"birth": {"ETERNITY": "1980-01-01"} }}, "households": {}}', BAD_REQUEST, 'households', 'not members of any household',),
        ])
def test_responses(test):
    check_response(*test)


def test_basic_calculation():
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

    response = post_json(simulation_json)
    assert response.status_code == OK
    response_json = json.loads(response.data.decode('utf-8'))
    assert dpath.get(response_json, 'persons/bill/basic_income/2017-12') == 600  # Universal basic income
    assert dpath.get(response_json, 'persons/bill/income_tax/2017-12') == 300  # 15% of the salary
    assert dpath.get(response_json, 'persons/bill/age/2017-12') == 37  # 15% of the salary
    assert dpath.get(response_json, 'persons/bob/basic_income/2017-12') == 600
    assert dpath.get(response_json, 'persons/bob/social_security_contribution/2017-12') == 816  # From social_security_contribution.yaml test
    assert dpath.get(response_json, 'households/first_household/housing_tax/2017') == 3000


def test_enums_sending_identifier():
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

    response = post_json(simulation_json)
    assert response.status_code == OK
    response_json = json.loads(response.data.decode('utf-8'))
    assert dpath.get(response_json, 'households/_/housing_tax/2017') == 0


def test_enum_output():
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

    response = post_json(simulation_json)
    assert response.status_code == OK
    response_json = json.loads(response.data.decode('utf-8'))
    assert dpath.get(response_json, "households/_/housing_occupancy_status/2017-01") == "tenant"


def test_enum_wrong_value():
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

    response = post_json(simulation_json)
    assert response.status_code == BAD_REQUEST
    response_json = json.loads(response.data.decode('utf-8'))
    message = "Possible values are ['owner', 'tenant', 'free_lodger', 'homeless']"
    text = dpath.get(response_json, "households/_/housing_occupancy_status/2017-01")
    assert message in text        


def test_encoding_variable_value():
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
    response = post_json(simulation_json)
    assert response.status_code == BAD_REQUEST, response.data.decode('utf-8')
    response_json = json.loads(response.data.decode('utf-8'))
    message = "'Locataire ou sous-locataire d‘un logement loué vide non-HLM' is not a known value for 'housing_occupancy_status'. Possible values are "
    text = dpath.get(response_json, 'households/_/housing_occupancy_status/2017-07')
    assert message in text        


def test_encoding_entity_name():
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
    response = post_json(simulation_json)
    response_json = json.loads(response.data.decode('utf-8'))

    # In Python 3, there is no encoding issue.
    if response.status_code != OK:
        message = "'O‘Ryan' is not a valid ASCII value."
        text = response_json['error']
        assert message in text        


def test_encoding_period_id():
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
    response = post_json(simulation_json)
    assert response.status_code == BAD_REQUEST
    response_json = json.loads(response.data.decode('utf-8'))

    # In Python 3, there is no encoding issue.
    if "Expected a period" not in to_unicode(response.data):
        message = "'à' is not a valid ASCII value."
        text = response_json['error']
        assert message in text        


def test_str_variable():
    new_couple = deepcopy(couple)
    new_couple['households']['_']['postal_code'] = {'2017-01': None}
    simulation_json = json.dumps(new_couple)

    response = subject.post('/calculate', data = simulation_json, content_type = 'application/json')

    assert response.status_code == OK
