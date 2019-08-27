import logging
import os
import pkg_resources

import yaml
from pytest import fixture, raises

from openfisca_core.taxbenefitsystems import VariableNameConflict
from openfisca_core.tools.test_runner import run_tests
from openfisca_country_template import CountryTaxBenefitSystem

file_dir = os.path.dirname(os.path.realpath(__file__))
country_template_dir = pkg_resources.get_distribution('OpenFisca-Country-Template').location

@fixture
def decomposition_tree():
    decomposition_path = os.path.join(file_dir, 'decomposition.yml')
    with open(decomposition_path, 'r') as yaml_file:
        return yaml.load(yaml_file, Loader = yaml.SafeLoader)


def test_existing_variable_conflicts(decomposition_tree):
    tax_benefit_system = CountryTaxBenefitSystem()
    with raises(VariableNameConflict):
        tax_benefit_system.add_variables_from_decomposition_tree(decomposition_tree)


def test_update_variable(decomposition_tree):
    tax_benefit_system = CountryTaxBenefitSystem()
    tax_benefit_system.add_variables_from_decomposition_tree(decomposition_tree, update = True)


def test_expression(decomposition_tree):
    tax_benefit_system = CountryTaxBenefitSystem()
    disposable_income = next(tax_benefit_system._iter_variables_from_decomposition_tree(decomposition_tree))
    assert(disposable_income.__name__ == "disposable_income")
    assert(disposable_income.expression == "salary + basic_income - income_tax - social_security_contribution")


def test_decomposition_result_equals_formula(decomposition_tree):
    # Just ensure that disposable_income can be calculated with and without decomposition.

    # Without decomposition
    tax_benefit_system = CountryTaxBenefitSystem()
    run_tests(tax_benefit_system, os.path.join(country_template_dir, "openfisca_country_template/tests/disposable_income.yaml"))

    # With decomposition
    tax_benefit_system = CountryTaxBenefitSystem()
    tax_benefit_system.add_variables_from_decomposition_tree(decomposition_tree, update = True)
    run_tests(tax_benefit_system, os.path.join(country_template_dir, "openfisca_country_template/tests/disposable_income.yaml"))
