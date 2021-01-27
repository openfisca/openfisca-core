# -*- coding: utf-8 -*-

import os
import json
from http.client import BAD_REQUEST, OK, NOT_FOUND
from copy import deepcopy

import pytest
import dpath

from openfisca_country_template.situation_examples import couple

from . import subject


def post_json(data = None, file = None):
    if file:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', file)
        with open(file_path, 'r') as file:
            data = file.read()
    return subject.post('/dependencies', data = data, content_type = 'application/json')


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
    ('{"persons": {"bob": {"basic_income": {"2017": 2000 }}}, "households": {"household": {"parents": ["bob"]}}}', BAD_REQUEST, 'persons/bob/basic_income/2017', '"basic_income" can only be set for one month',),
    ('{"persons": {"bob": {"salary": {"ETERNITY": 2000 }}}, "households": {"household": {"parents": ["bob"]}}}', BAD_REQUEST, 'persons/bob/salary/ETERNITY', 'salary is only defined for months',),
    ('{"persons": {"alice": {}, "bob": {}, "charlie": {}}, "households": {"_": {"parents": ["alice", "bob", "charlie"]}}}', BAD_REQUEST, 'households/_/parents', 'at most 2 parents in a household',),
    ])
def test_responses(test):
    check_response(*test)


def test_basic_variable_deps():
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
    # response_json = {'accommodation_size': 1, 'birth': 3, 'housing_occupancy_status': 1, 'salary': 4}

    assert dpath.get(response_json, 'accommodation_size') == 1
    assert dpath.get(response_json, 'birth') == 3
    assert dpath.get(response_json, 'housing_occupancy_status') == 1
    assert dpath.get(response_json, 'salary') == 4


"""
def test_basic_variable_deps():
    simulation_json = json.dumps({
    {
      "persons": {
            "joe": {
                    "basic_income": {
                            "2020-1": None
                    },
                    "housing_allowance": {
                            "2020-1": None
                    }
            },
            "titled_properties": {
            },
            "families": {
            }
    }}})

    response = post_json(simulation_json)
    assert response.status_code == OK
    response_json = json.loads(response.data.decode('utf-8'))
    assert dpath.get(response_json, 'persons/bill/basic_income/2017-12') == 600  # Universal basic income
    assert dpath.get(response_json, 'persons/bill/income_tax/2017-12') == 300  # 15% of the salary
    assert dpath.get(response_json, 'persons/bill/age/2017-12') == 37  # 15% of the salary
    assert dpath.get(response_json, 'persons/bob/basic_income/2017-12') == 600
    assert dpath.get(response_json, 'persons/bob/social_security_contribution/2017-12') == 816  # From social_security_contribution.yaml test
    assert dpath.get(response_json, 'households/first_household/housing_tax/2017') == 3000

"""

