from http.client import OK
from openfisca_core.scripts import build_tax_benefit_system
from openfisca_web_api.app import create_app


TEST_COUNTRY_PACKAGE_NAME = 'openfisca_country_template'
TEST_EXTENSION_PACKAGE_NAMES = ['openfisca_extension_template']

tax_benefit_system = build_tax_benefit_system(TEST_COUNTRY_PACKAGE_NAME, extensions = TEST_EXTENSION_PACKAGE_NAMES, reforms = None)

extended_subject = create_app(tax_benefit_system).test_client()


def test_return_code():
    parameters_response = extended_subject.get('/parameters')
    assert parameters_response.status_code == OK


def test_return_code_existing_parameter():
    extension_parameter_response = extended_subject.get('/parameter/local_town.child_allowance.amount')
    assert extension_parameter_response.status_code == OK


def test_return_code_existing_variable():
    extension_variable_response = extended_subject.get('/variable/local_town_child_allowance')
    assert extension_variable_response.status_code == OK
