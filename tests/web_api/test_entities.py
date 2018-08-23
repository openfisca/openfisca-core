# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from http.client import OK
from nose.tools import assert_equal
from . import subject


entities_response = subject.get('/entities')

# /entities


def test_return_code():
    assert_equal(entities_response.status_code, OK)


