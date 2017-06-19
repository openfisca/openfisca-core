# -*- coding: utf-8 -*-

import os
import json
from httplib import BAD_REQUEST

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
        import nose.tools; nose.tools.set_trace(); import ipdb; ipdb.set_trace()


def test_incorrect_inputs():
    tests = [
        ('{"a" : "x", "b"}', BAD_REQUEST, 'error', 'Invalid JSON'),
        ('["An", "array"]', BAD_REQUEST, 'error', 'Invalid type'),
        ('{"unknown_entity": {}}', BAD_REQUEST, 'unknown_entity', 'entity is not defined',),
        ('{"households": {"dupont": {"parents": {}}}}', BAD_REQUEST, 'households/dupont/parents', 'type',),
        ('{"persons": {"bob": {"unknown_variable": {}}}}', BAD_REQUEST, 'persons/bob/unknown_variable', 'You tried to calculate or to set',)

        ]

    for test in tests:
        yield (check_response,) + test
