# -*- coding: utf-8 -*-

import json
from httplib import OK

from nose.tools import assert_equal, assert_items_equal, assert_in
from . import subject

openAPI_response = subject.get('/spec')


def test_return_code():
    assert_equal(openAPI_response.status_code, OK)


body = json.loads(openAPI_response.data)


def test_paths():
    assert_items_equal(
        body['paths'],
        ["/parameter/{parameterID}",
        "/parameters",
        "/variable/{variableID}",
        "/variables",
        "/calculate"]
        )


def test_entity_definition():
    household = body['definitions']['Household']
    person = body['definitions']['Person']
    assert_in('salary', person['properties'])
    assert_in('rent', household['properties'])
    assert_in('parents', household['properties'])
    assert_in('children', household['properties'])


def test_situation_definition():
    situation_input = body['definitions']['SituationInput']
    situation_output = body['definitions']['SituationOutput']
    for situation in situation_input, situation_output:
        properties = situation['properties']
        assert_in('households', properties)
        assert_in('persons', properties)
        assert_equal(properties['households']['additionalProperties'], {"$ref": "#/definitions/Household"})
        assert_equal(properties['persons']['additionalProperties'], {"$ref": "#/definitions/Person"})
