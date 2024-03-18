from http import client

import pytest

from openfisca_core.scripts import build_tax_benefit_system
from openfisca_web_api.app import create_app


@pytest.fixture()
def tax_benefit_system(test_country_package_name, test_extension_package_name):
    return build_tax_benefit_system(
        test_country_package_name,
        extensions=[test_extension_package_name],
        reforms=None,
    )


@pytest.fixture()
def extended_subject(tax_benefit_system):
    return create_app(tax_benefit_system).test_client()


def test_return_code(extended_subject):
    parameters_response = extended_subject.get("/parameters")
    assert parameters_response.status_code == client.OK


def test_return_code_existing_parameter(extended_subject):
    extension_parameter_response = extended_subject.get(
        "/parameter/local_town.child_allowance.amount"
    )
    assert extension_parameter_response.status_code == client.OK


def test_return_code_existing_variable(extended_subject):
    extension_variable_response = extended_subject.get(
        "/variable/local_town_child_allowance"
    )
    assert extension_variable_response.status_code == client.OK
