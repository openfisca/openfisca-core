# -*- coding: utf-8 -*-
import pkg_resources
from openfisca_web_api_preview.app import create_app

TEST_COUNTRY_PACKAGE_NAME = 'openfisca_country_template'
TEST_EXTENSION_PACKAGE_NAME = 'openfisca_extension_template'

distribution = pkg_resources.get_distribution(TEST_COUNTRY_PACKAGE_NAME)
extended_subject = create_app(TEST_COUNTRY_PACKAGE_NAME, TEST_EXTENSION_PACKAGE_NAME).test_client()

parameters_response = subject.get('/parameters')

def test_return_code():
    assert_equal(parameters_response.status_code, OK)
