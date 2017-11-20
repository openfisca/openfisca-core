# -*- coding: utf-8 -*-
import pkg_resources
from openfisca_web_api_preview.app import create_app
from openfisca_core.scripts import build_tax_benefit_system

TEST_COUNTRY_PACKAGE_NAME = 'openfisca_country_template'

TEST_EXTENSION_PACKAGE_NAMES = ['openfisca_extension_template']

tax_benefit_system = build_tax_benefit_system(TEST_COUNTRY_PACKAGE_NAME, extensions = TEST_EXTENSION_PACKAGE_NAMES, reforms = None)

distribution = pkg_resources.get_distribution(TEST_COUNTRY_PACKAGE_NAME)

subject = create_app(tax_benefit_system).test_client()
