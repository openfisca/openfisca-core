# -*- coding: utf-8 -*-

import os
import json
from httplib import BAD_REQUEST

from nose.tools import assert_equal, assert_in

from . import subject


def post_json(data = None, file = None):
    if file:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', file_name)
        with open(file_path, 'r') as file:
            data = file.read()
    return subject.post('/calculate', data = data, content_type = 'application/json')


invalid_json_response = post_json('{"a" : "x", "b"}')

def test_invalid_json_return_code():
    assert_equal(invalid_json_response.status_code, BAD_REQUEST)


def test_invalid_json_response_content():
    response = json.loads(invalid_json_response.data)
    error_message = response['error']
    assert_in('Invalid JSON', error_message)
    # The clients get details about where and why the JSON is invalid
    assert_in('line', error_message)
    assert_in('column', error_message)


wrong_type_response = post_json('["An", "array"]')

def test_wrong_type_return_code():
    assert_equal(wrong_type_response.status_code, BAD_REQUEST)


def test_wrong_type_response_content():
    response = json.loads(wrong_type_response.data)
    assert_in('Invalid type', response['error'])


unknown_entity_response = post_json('{"unknown_entity": {}}')

def test_unknown_entity_return_code():
    assert_equal(unknown_entity_response.status_code, BAD_REQUEST)


def test_unknown_entity_response_content():
    response = json.loads(unknown_entity_response.data)
    assert_in('entity is not defined', response['unknown_entity'])

invalid_role_type_response = post_json('{"households": {"parents": {}}}')

def test_invalid_role_type_return_code():
    assert_equal(invalid_role_type_response.status_code, BAD_REQUEST)


def test_invalid_role_type_response_content():
    response = json.loads(invalid_role_type_response.data)
    assert_in('type', response['households']['parents'])

another_test_response = post_json('{"households": {"parents": [{}, {}]}}')



def test_another_test_return_code():
    assert_equal(another_test_response.status_code, BAD_REQUEST)


def test_another_test_response_content():
    response = json.loads(another_test_response.data)
    assert_in('type', response['households']['parents'])
