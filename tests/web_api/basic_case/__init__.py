# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pkg_resources
from openfisca_web_api_preview.app import create_app
from openfisca_core.scripts import build_tax_benefit_system

TEST_COUNTRY_PACKAGE_NAME = 'openfisca_country_template'
distribution = pkg_resources.get_distribution(TEST_COUNTRY_PACKAGE_NAME)
tax_benefit_system = build_tax_benefit_system(TEST_COUNTRY_PACKAGE_NAME, extensions = None, reforms = None)
subject = create_app(tax_benefit_system).test_client()
