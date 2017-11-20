# -*- coding: utf-8 -*-

from httplib import OK
from nose.tools import assert_equal
from . import subject


def test_return_code():
    parameters_response = subject.get('/parameters')
    assert_equal(parameters_response.status_code, OK)


def test_return_code_existing_parameter():
    extension_parameter_response = subject.get('/parameter/local_town.child_allowance.amount')
    assert_equal(extension_parameter_response.status_code, OK)


def test_return_code_existing_variable():
    extension_variable_response = subject.get('/variable/local_town_child_allowance')
    assert_equal(extension_variable_response.status_code, OK)
