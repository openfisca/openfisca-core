from pytest import fixture, raises

from openfisca_core.tools import assert_near
from openfisca_core.simulations import calculate_output_add
from openfisca_core.simulations import calculate_output_divide
from openfisca_core.periods import YEAR


@fixture
def simple_variable(make_variable):
    return make_variable('simple_variable')


@fixture
def variable_with_calculate_output_add(make_variable):
    return make_variable('variable_with_calculate_output_add', calculate_output = calculate_output_add)


@fixture
def variable_with_calculate_output_divide(make_variable):
    return make_variable('variable_with_calculate_output_divide',
            definition_period = YEAR,
            calculate_output = calculate_output_divide)


@fixture
def simulation_single_with_variables(simulation_builder, tax_benefit_system, single,
        simple_variable, variable_with_calculate_output_add, variable_with_calculate_output_divide):
    tax_benefit_system.add_variables(simple_variable, variable_with_calculate_output_add, variable_with_calculate_output_divide)
    return simulation_builder.build_from_entities(tax_benefit_system, single)


def test_calculate_output_default(simulation_single_with_variables):
    with raises(ValueError):
        simulation_single_with_variables.calculate_output('simple_variable', 2017)


def test_calculate_output_add(simulation_single_with_variables):
    simulation_single_with_variables.set_input('variable_with_calculate_output_add', '2017-01', [10])
    simulation_single_with_variables.set_input('variable_with_calculate_output_add', '2017-05', [20])
    simulation_single_with_variables.set_input('variable_with_calculate_output_add', '2017-12', [70])
    assert_near(simulation_single_with_variables.calculate_output('variable_with_calculate_output_add', 2017), 100)


def test_calculate_output_divide(simulation_single_with_variables):
    simulation_single_with_variables.set_input('variable_with_calculate_output_divide', 2017, [12000])
    assert_near(simulation_single_with_variables.calculate_output('variable_with_calculate_output_divide', '2017-06'), 1000)
