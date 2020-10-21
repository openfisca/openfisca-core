import http
import pytest

from openfisca_core import scripts
from openfisca_web_api import app

TEST_COUNTRY_PACKAGE_NAME = "openfisca_country_template"
TEST_REFORMS_PATHS = [
    f"{TEST_COUNTRY_PACKAGE_NAME}.reforms.add_dynamic_variable.add_dynamic_variable",
    f"{TEST_COUNTRY_PACKAGE_NAME}.reforms.add_new_tax.add_new_tax",
    f"{TEST_COUNTRY_PACKAGE_NAME}.reforms.flat_social_security_contribution.flat_social_security_contribution",
    f"{TEST_COUNTRY_PACKAGE_NAME}.reforms.modify_social_security_taxation.modify_social_security_taxation",
    f"{TEST_COUNTRY_PACKAGE_NAME}.reforms.removal_basic_income.removal_basic_income",
    ]


# Create app as in 'openfisca serve' script
@pytest.fixture
def client():
    tax_benefit_system = scripts.build_tax_benefit_system(
        TEST_COUNTRY_PACKAGE_NAME,
        extensions = None,
        reforms = TEST_REFORMS_PATHS,
        )

    return app.create_app(tax_benefit_system).test_client()


def test_return_code_of_dynamic_variable(client):
    result = client.get("/variable/goes_to_school")

    assert result.status_code == http.client.OK


def test_return_code_of_has_car_variable(client):
    result = client.get("/variable/has_car")

    assert result.status_code == http.client.OK


def test_return_code_of_new_tax_variable(client):
    result = client.get("/variable/new_tax")

    assert result.status_code == http.client.OK


def test_return_code_of_social_security_contribution_variable(client):
    result = client.get("/variable/social_security_contribution")

    assert result.status_code == http.client.OK


def test_return_code_of_social_security_contribution_parameter(client):
    result = client.get("/parameter/taxes.social_security_contribution")

    assert result.status_code == http.client.OK


def test_return_code_of_basic_income_variable(client):
    result = client.get("/variable/basic_income")

    assert result.status_code == http.client.OK
