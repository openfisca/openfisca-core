# -*- coding: utf-8 -*-

import json
from http.client import OK

import dpath.util
from . import subject


def assert_items_equal(x, y):
    assert sorted(x) == sorted(y)


openAPI_response = subject.get('/spec')


def test_return_code():
    assert openAPI_response.status_code == OK


body = json.loads(openAPI_response.data.decode('utf-8'))


def test_paths():
    assert_items_equal(
        body['paths'],
        ["/parameter/{parameterID}",
        "/parameters",
        "/variable/{variableID}",
        "/variables",
        "/entities",
        "/trace",
        "/calculate",
        "/spec"]
        )


def test_entity_definition():
    assert 'parents' in dpath.util.get(body, 'definitions/Household/properties')
    assert 'children' in dpath.util.get(body, 'definitions/Household/properties')
    assert 'salary' in dpath.util.get(body, 'definitions/Person/properties')
    assert 'rent' in dpath.util.get(body, 'definitions/Household/properties')
    assert 'number' == dpath.util.get(body, 'definitions/Person/properties/salary/additionalProperties/type')


def test_situation_definition():
    situation_input = body['definitions']['SituationInput']
    situation_output = body['definitions']['SituationOutput']
    for situation in situation_input, situation_output:
        assert 'households' in dpath.util.get(situation, '/properties')
        assert 'persons' in dpath.util.get(situation, '/properties')
        assert "#/definitions/Household" == dpath.util.get(situation, '/properties/households/additionalProperties/$ref')
        assert "#/definitions/Person" == dpath.util.get(situation, '/properties/persons/additionalProperties/$ref')


def test_host():
    assert 'http' not in body['host']
