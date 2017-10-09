# -*- coding: utf-8 -*-

from httplib import OK
from nose.tools import assert_equal
from openfisca_web_api_preview.app import create_app


TEST_COUNTRY_PACKAGE_NAME = 'openfisca_country_template'
TEST_EXTENSION_PACKAGE_NAME = ['openfisca_extension_template']

extended_subject = create_app(TEST_COUNTRY_PACKAGE_NAME, TEST_EXTENSION_PACKAGE_NAME).test_client()


def test_return_code():
    parameters_response = extended_subject.get('/parameters')
    assert_equal(parameters_response.status_code, OK)


def test_return_code_existing_parameter():
    extension_parameter_response = extended_subject.get('/parameter/local_town.child_allowance.amount')
    assert_equal(extension_parameter_response.status_code, OK)


def test_return_code_existing_variable():
    extension_variable_response = extended_subject.get('/variable/local_town_child_allowance')
    assert_equal(extension_variable_response.status_code, OK)
