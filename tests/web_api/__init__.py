# -*- coding: utf-8 -*-
import pkg_resources
from openfisca_web_api_preview.app import create_app

TEST_COUNTRY_PACKAGE_NAME = 'openfisca_country_template'
TRACKER_URL = 'https://openfisca.innocraft.cloud/piwik.php'
TRACKER_IDSITE = 1

ACTIVE_TRACKING = True

distribution = pkg_resources.get_distribution(TEST_COUNTRY_PACKAGE_NAME)

if ACTIVE_TRACKING:
    subject = create_app(TEST_COUNTRY_PACKAGE_NAME, TRACKER_URL, TRACKER_IDSITE).test_client()
else:
    subject = create_app(TEST_COUNTRY_PACKAGE_NAME).test_client()
