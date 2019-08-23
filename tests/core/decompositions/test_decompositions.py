import logging
import os

import yaml
from pytest import fixture, raises

from openfisca_core.taxbenefitsystems import VariableNameConflict
from openfisca_country_template import CountryTaxBenefitSystem

tax_benefit_system = CountryTaxBenefitSystem()


@fixture
def decomposition_tree():
    decomposition_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'decomposition.yml')
    with open(decomposition_path, 'r') as yaml_file:
        return yaml.load(yaml_file, Loader = yaml.SafeLoader)


def test_existing_variable_conflicts(decomposition_tree):
    with raises(VariableNameConflict):
        tax_benefit_system.add_variables_from_decomposition_tree(decomposition_tree)


def test_update_variable(decomposition_tree):
    tax_benefit_system.add_variables_from_decomposition_tree(decomposition_tree, update = True)


def test_expression(decomposition_tree):
    disposable_income = next(tax_benefit_system._iter_variables_from_decomposition_tree(decomposition_tree))
    assert(disposable_income.__name__ == "disposable_income")
    assert(disposable_income.expression == "salary + basic_income - income_tax - social_security_contribution")
