# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from http.client import OK
from nose.tools import assert_equal
import json
from . import subject


entities_response = subject.get('/entities')

# /entities


def test_return_code():
    assert_equal(entities_response.status_code, OK)


def test_response_data():
    entities = json.loads(entities_response.data.decode('utf-8'))
    assert_equal(
        entities['household'],
        {'plural': 'households'}
        )
