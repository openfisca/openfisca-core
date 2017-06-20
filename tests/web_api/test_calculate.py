# -*- coding: utf-8 -*-

import os
import json
from httplib import BAD_REQUEST, NOT_FOUND

from nose.tools import assert_equal, assert_in
import dpath

from . import subject


def post_json(data = None, file = None):
    if file:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', file_name)
        with open(file_path, 'r') as file:
            data = file.read()
    return subject.post('/calculate', data = data, content_type = 'application/json')


def check_response(data, expected_error_code, path_to_check, content_to_check):
    response = post_json(data)
    try:
        assert_equal(response.status_code, expected_error_code)
        json_response = json.loads(response.data)
        content = dpath.util.get(json_response, path_to_check)
        assert_in(content_to_check, content)
    except:
        raise
        import nose.tools; nose.tools.set_trace(); import ipdb; ipdb.set_trace()


def test_incorrect_inputs():
    tests = [
        ('{"a" : "x", "b"}', BAD_REQUEST, 'error', 'Invalid JSON'),
        ('["An", "array"]', BAD_REQUEST, 'error', 'Invalid type'),
        ('{"unknown_entity": {}}', BAD_REQUEST, 'unknown_entity', 'entity is not defined',),
        ('{"households": {"dupont": {"parents": {}}}}', BAD_REQUEST, 'households/dupont/parents', 'type',),
        # ('{"persons": {"bob": {"unknown_variable": {}}}}', NOT_FOUND, 'persons/bob/unknown_variable', 'You tried to calculate or to set',),
        # ('{"persons": {"bob": {"housing_allowance": {}}}}', BAD_REQUEST, 'persons/bob/housing_allowance', 'housing_allowance is only defined for households',),
        # ('{"persons": {"bob": {"salary": 4000 }}}', BAD_REQUEST, 'persons/bob/salary', 'period',),

        ]

    for test in tests:
        yield (check_response,) + test


def test_basic_calculation():
    simulation_json = json.dumps({
        "persons": {
            "bill": {
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
                "accomodation_size": {
                    "2017": 300
                    }
                },
            }
    })

    response = json.loads(post_json(simulation_json).data)
    assert_equal(dpath.get(response, 'persons/bill/basic_income/2017-12'), 600)  # Universal basic income
    assert_equal(dpath.get(response, 'persons/bill/income_tax/2017-12'), 300)  # 15% of the salary
    assert_equal(dpath.get(response, 'persons/bob/basic_income/2017-12'), 600)
    assert_equal(dpath.get(response, 'persons/bob/social_security_contribution/2017-12'), 816)  # From social_security_contribution.yaml test

