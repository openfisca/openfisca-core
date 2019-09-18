import logging
import os

import pkg_resources
import yaml
from pytest import fixture, raises

from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.taxbenefitsystems import VariableNameConflict
from openfisca_core.tools import assert_near
from openfisca_core.tools.test_runner import run_tests

from .taxbenefitsystem_3_entities import \
    TaxBenefitSystemFixture as TBS3Entities
from .taxbenefitsystem_depth1 import TaxBenefitSystemFixture as TBSDepth1
from .taxbenefitsystem_depth2 import TaxBenefitSystemFixture as TBSDepth2

file_dir = os.path.dirname(os.path.realpath(__file__))

@fixture
def decomposition_depth1():
    decomposition_path = os.path.join(file_dir, 'decomposition_depth1.yml')
    with open(decomposition_path, 'r') as yaml_file:
        return yaml.load(yaml_file, Loader = yaml.SafeLoader)


@fixture
def decomposition_depth2():
    decomposition_path = os.path.join(file_dir, 'decomposition_depth2.yml')
    with open(decomposition_path, 'r') as yaml_file:
        return yaml.load(yaml_file, Loader = yaml.SafeLoader)


@fixture
def decomposition_3_entities():
    decomposition_path = os.path.join(file_dir, 'decomposition_3_entities.yml')
    with open(decomposition_path, 'r') as yaml_file:
        return yaml.load(yaml_file, Loader = yaml.SafeLoader)


@fixture
def make_isolated_simulation():
    def _make_simulation(tbs, test_case):
        builder = SimulationBuilder()
        return builder.build_from_entities(tbs, test_case)
    return _make_simulation


def test_existing_variable_conflicts(decomposition_depth1):
    tax_benefit_system = TBSDepth1()
    with raises(VariableNameConflict):
        tax_benefit_system.add_variables_from_decomposition_tree(decomposition_depth1)


def test_update_variable(decomposition_depth1):
    tax_benefit_system = TBSDepth1()
    tax_benefit_system.add_variables_from_decomposition_tree(decomposition_depth1, update = True)


def test_generated_expression_matches_decomposition_subtree_depth1(decomposition_depth1):
    tax_benefit_system = TBSDepth1()
    root = next(tax_benefit_system._iter_variables_from_decomposition_tree(decomposition_depth1))
    assert root.__name__ == "root"
    assert root.expression == "income_a - tax_a"


def test_decomposition_result_equals_formula_depth1(decomposition_depth1):
    # Just ensure that disposable_income can be calculated with and without decomposition.

    decomposition_path = os.path.join(file_dir, 'decomposition_depth1.yml')

    # Without decomposition
    tax_benefit_system = TBSDepth1()
    # TODO make run_tests raise an error, not just print
    run_tests(tax_benefit_system, decomposition_path)

    # With decomposition
    tax_benefit_system = TBSDepth1()
    tax_benefit_system.add_variables_from_decomposition_tree(decomposition_depth1, update = True)
    run_tests(tax_benefit_system, decomposition_path)


def test_generated_expression_matches_decomposition_subtree_depth2(decomposition_depth2):
    tax_benefit_system = TBSDepth2()
    variables = list(tax_benefit_system._iter_variables_from_decomposition_tree(decomposition_depth2))
    assert variables[0].__name__ == "taxes"
    assert variables[0].expression == "tax_a + tax_b"
    assert variables[1].__name__ == "root"
    assert variables[1].expression == "income_a - taxes"


# TODO make run_tests raise an error, not just print
# def test_decomposition_result_equals_formula_depth2(decomposition_depth1):
#     # Just ensure that disposable_income can be calculated with and without decomposition.

#     decomposition_path = os.path.join(file_dir, 'decomposition_depth2.yml')

#     # Without decomposition
#     tax_benefit_system = TBSDepth2()
#     run_tests(tax_benefit_system, decomposition_path)

#     # With decomposition
#     tax_benefit_system = TBSDepth2()
#     tax_benefit_system.add_variables_from_decomposition_tree(decomposition_depth2, update = True)
#     run_tests(tax_benefit_system, decomposition_path)


def test_household_parent_and_person_children(make_isolated_simulation, decomposition_3_entities):
    period = "2016-01"

    test_case = {
        'persons': {
            'Ari': {'income_a': {period: 4000}},
            'Paul': {'income_a': {period: 20}}
        },
        'households': {
            'h1': {'parents': ['Ari', 'Paul']},
        },
    }

    tax_benefit_system_a = TBS3Entities()
    simulation_a = make_isolated_simulation(tax_benefit_system_a, test_case)
    root_a = simulation_a.calculate('root', period)

    tax_benefit_system_b = TBS3Entities()
    tax_benefit_system_b.add_variables_from_decomposition_tree(decomposition_3_entities, update = True)
    simulation_b = make_isolated_simulation(tax_benefit_system_b, test_case)
    root_b = simulation_b.calculate('root', period)

    # Ensure there is only one household, because persons are in the same household.
    assert len(root_a) == 1
    assert len(root_b) == 1
    v = 4000 + 20 - 2 * (21.1 + 13)
    assert_near(root_a, v)
    assert_near(root_b, v)
    assert_near(root_a, root_b, absolute_error_margin = 0.01)
