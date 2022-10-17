import pytest

from policyengine_core import periods, simulations, tools
from policyengine_core.country_template import entities, situation_examples
from policyengine_core.simulations import SimulationBuilder
from policyengine_core.variables import Variable


class simple_variable(Variable):
    entity = entities.Person
    definition_period = periods.MONTH
    value_type = int


class variable_with_calculate_output_add(Variable):
    entity = entities.Person
    definition_period = periods.MONTH
    value_type = int
    calculate_output = simulations.calculate_output_add


class variable_with_calculate_output_divide(Variable):
    entity = entities.Person
    definition_period = periods.YEAR
    value_type = int
    calculate_output = simulations.calculate_output_divide


@pytest.fixture(scope="module", autouse=True)
def add_variables_to_tax_benefit_system(tax_benefit_system):
    tax_benefit_system.add_variables(
        simple_variable,
        variable_with_calculate_output_add,
        variable_with_calculate_output_divide,
    )


@pytest.fixture
def simulation(tax_benefit_system):
    return SimulationBuilder().build_from_entities(
        tax_benefit_system, situation_examples.single
    )


def test_calculate_output_default(simulation):
    with pytest.raises(ValueError):
        simulation.calculate_output("simple_variable", 2017)


def test_calculate_output_add(simulation):
    simulation.set_input("variable_with_calculate_output_add", "2017-01", [10])
    simulation.set_input("variable_with_calculate_output_add", "2017-05", [20])
    simulation.set_input("variable_with_calculate_output_add", "2017-12", [70])
    tools.assert_near(
        simulation.calculate_output(
            "variable_with_calculate_output_add", 2017
        ),
        100,
    )


def test_calculate_output_divide(simulation):
    simulation.set_input(
        "variable_with_calculate_output_divide", 2017, [12000]
    )
    tools.assert_near(
        simulation.calculate_output(
            "variable_with_calculate_output_divide", "2017-06"
        ),
        1000,
    )
