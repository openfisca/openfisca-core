from openfisca_core.model_api import *  # noqa analysis:ignore
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.tools import assert_near

from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import *  # noqa analysis:ignore

from pytest import fixture, raises


@fixture
def simulation(single):
    return SimulationBuilder().build_from_entities(tax_benefit_system, single)


class simple_variable(Variable):
    entity = Person
    definition_period = MONTH
    value_type = int


class variable_with_calculate_output_add(Variable):
    entity = Person
    definition_period = MONTH
    value_type = int
    calculate_output = calculate_output_add


class variable_with_calculate_output_divide(Variable):
    entity = Person
    definition_period = YEAR
    value_type = int
    calculate_output = calculate_output_divide


tax_benefit_system = CountryTaxBenefitSystem()
tax_benefit_system.add_variables(
    simple_variable,
    variable_with_calculate_output_add,
    variable_with_calculate_output_divide
    )


def test_calculate_output_default(simulation):
    with raises(ValueError):
        simulation.calculate_output('simple_variable', 2017)


def test_calculate_output_add(simulation):
    simulation.set_input('variable_with_calculate_output_add', '2017-01', [10])
    simulation.set_input('variable_with_calculate_output_add', '2017-05', [20])
    simulation.set_input('variable_with_calculate_output_add', '2017-12', [70])
    assert_near(simulation.calculate_output('variable_with_calculate_output_add', 2017), 100)


def test_calculate_output_divide(simulation):
    simulation.set_input('variable_with_calculate_output_divide', 2017, [12000])
    assert_near(simulation.calculate_output('variable_with_calculate_output_divide', '2017-06'), 1000)
