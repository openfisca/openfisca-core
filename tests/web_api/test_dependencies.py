# -*- coding: utf-8 -*-

import json
import os
from http.client import BAD_REQUEST, NOT_FOUND, OK

import dpath

import pytest

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


def test_parenting_payment():
    simulation_json = json.dumps({
        "persons": {
            "Phil": {
                "birth": {
                    "1981-10": "1981-10-01"
                    },
                "salary": {
                    "2020-12": 200
                    }
                },
            "Saz": {
                "birth": {
                    "1980-10": "1980-10-01"
                    },
                "salary": {
                    "2020-12": 210
                    }
                },
            "Caz": {
                "birth": {
                    "2010-10": "2010-10-01"
                    }
                },
            "Eille": {
                "birth": {
                    "2012-10": "2012-10-01"
                    }
                },
            "Nimasay": {
                "birth": {
                    "2018-10": "2018-10-01"
                    },
                }
            },
        "households": {
            "first_household": {
                "parents": ['Phil', 'Saz'],
                "children": ['Caz', 'Eille', 'Nimasay'],
                "parenting_allowance": {
                    "2020": None
                    },
                },
            }
        })

    response = post_json(simulation_json)
    assert response.status_code == OK
    response_json = json.loads(response.data.decode('utf-8'))
    # response_json = {'salary': 1, 'birth': 1}
    assert dpath.get(response_json, 'salary') == 1
    assert dpath.get(response_json, 'birth') == 1
