# -*- coding: utf-8 -*-

import json
from httplib import OK

from nose.tools import assert_equal, assert_items_equal
from . import subject

openAPI_response = subject.get('/spec')


def test_return_code():
    assert_equal(openAPI_response.status_code, OK)


def test_paths():
    assert_items_equal(
        json.loads(openAPI_response.data)['paths'],
        ["/parameter/{parameterID}", "/parameters", "/variable/{variableID}", "/variables"])
