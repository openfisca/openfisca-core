from importlib import metadata

import pytest


@pytest.fixture()
def test_country_package_name():
    return "openfisca_country_template"


@pytest.fixture()
def test_extension_package_name():
    return "openfisca_extension_template"


@pytest.fixture()
def distribution(test_country_package_name):
    return metadata.distribution(test_country_package_name)
