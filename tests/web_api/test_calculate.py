# -*- coding: utf-8 -*-

import os
from httplib import BAD_REQUEST

from nose.tools import assert_equal

from . import subject

invalid_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'invalid_json.json')


def post(data):
    return subject.post('/calculate', data = data, content_type = 'application/json')


def test_invalid_json():
    with open(invalid_json_path, 'r') as file:
        content = file.read()
    response = post(content)
    assert_equal(response.status_code, BAD_REQUEST)
