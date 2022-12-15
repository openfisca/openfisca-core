# -*- coding: utf-8 -*-
import pkg_resources

from openfisca_core.scripts import build_tax_benefit_system
from openfisca_web_api.app import create_app

TEST_COUNTRY_PACKAGE_NAME = 'openfisca_country_template'
distribution = pkg_resources.get_distribution(TEST_COUNTRY_PACKAGE_NAME)
tax_benefit_system = build_tax_benefit_system(TEST_COUNTRY_PACKAGE_NAME, extensions = None, reforms = None)
subject = create_app(tax_benefit_system).test_client()
