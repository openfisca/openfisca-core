import http
import pytest

from openfisca_core import scripts
from openfisca_web_api import app

TEST_COUNTRY_PACKAGE_NAME = "openfisca_country_template"
TEST_REFORMS_PATHS = [
    "tests.web_api.case_with_reform.dynamic_reform.add_dynamic_variable",
    f"{TEST_COUNTRY_PACKAGE_NAME}.reforms.add_new_tax.add_new_tax",
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
