# -*- coding: utf-8 -*-
import pkg_resources
from openfisca_web_api_preview.app import create_app

TEST_COUNTRY_PACKAGE_NAME = 'openfisca_country_template'
distribution = pkg_resources.get_distribution(TEST_COUNTRY_PACKAGE_NAME)
subject = create_app(TEST_COUNTRY_PACKAGE_NAME).test_client()
