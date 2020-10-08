from http.client import OK
from openfisca_core.scripts import build_tax_benefit_system
from openfisca_web_api.app import create_app


TEST_COUNTRY_PACKAGE_NAME = 'openfisca_country_template'
TEST_REFORMS_PATHS = ['tests.web_api.case_with_reform.reforms.add_variable_reform']

# create app as in 'openfisca serve' script
tax_benefit_system = build_tax_benefit_system(TEST_COUNTRY_PACKAGE_NAME, extensions = None, reforms = TEST_REFORMS_PATHS)
reformed_subject = create_app(tax_benefit_system).test_client()


def test_return_code_existing_variable():
    reform_variable_response = reformed_subject.get('/variable/goes_to_school')
    assert reform_variable_response.status_code == OK
