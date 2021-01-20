from pytest import raises

from openfisca_core.tools import assert_near


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
