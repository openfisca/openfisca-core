# -*- coding: utf-8 -*-

import os
import json
from httplib import BAD_REQUEST

from nose.tools import assert_equal, assert_in

from . import subject


def post(data):
    return subject.post('/calculate', data = data, content_type = 'application/json')


invalid_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'invalid_json.json')

with open(invalid_json_path, 'r') as file:
    content = file.read()
    invalid_json_response = post(content)


def test_invalid_json_return_code():
    assert_equal(invalid_json_response.status_code, BAD_REQUEST)


def test_invalid_json_response_content():
    response = json.loads(invalid_json_response.data)
    error_message = response['error']
    assert_in('Invalid JSON', error_message)
    # The clients get details about where and why the JSON is invalid
    assert_in('line', error_message)
    assert_in('column', error_message)
