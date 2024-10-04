import http

import pytest

from openfisca_core import scripts
from openfisca_web_api import app


@pytest.fixture
def test_reforms_path(test_country_package_name):
    return [
        f"{test_country_package_name}.reforms.add_dynamic_variable.add_dynamic_variable",
        f"{test_country_package_name}.reforms.add_new_tax.add_new_tax",
        f"{test_country_package_name}.reforms.flat_social_security_contribution.flat_social_security_contribution",
        f"{test_country_package_name}.reforms.modify_social_security_taxation.modify_social_security_taxation",
        f"{test_country_package_name}.reforms.removal_basic_income.removal_basic_income",
    ]


# Create app as in 'openfisca serve' script
@pytest.fixture
def client(test_country_package_name, test_reforms_path):
    tax_benefit_system = scripts.build_tax_benefit_system(
        test_country_package_name,
        extensions=None,
        reforms=test_reforms_path,
    )

    return app.create_app(tax_benefit_system).test_client()


def test_return_code_of_dynamic_variable(client) -> None:
    result = client.get("/variable/goes_to_school")

    assert result.status_code == http.client.OK


def test_return_code_of_has_car_variable(client) -> None:
    result = client.get("/variable/has_car")

    assert result.status_code == http.client.OK


def test_return_code_of_new_tax_variable(client) -> None:
    result = client.get("/variable/new_tax")

    assert result.status_code == http.client.OK


def test_return_code_of_social_security_contribution_variable(client) -> None:
    result = client.get("/variable/social_security_contribution")

    assert result.status_code == http.client.OK


def test_return_code_of_social_security_contribution_parameter(client) -> None:
    result = client.get("/parameter/taxes.social_security_contribution")

    assert result.status_code == http.client.OK


def test_return_code_of_basic_income_variable(client) -> None:
    result = client.get("/variable/basic_income")

    assert result.status_code == http.client.OK
