from __future__ import unicode_literals, print_function, division, absolute_import
from nose.tools import raises

from openfisca_core.model_api import *  # noqa analysis:ignore
from openfisca_core.simulations import Simulation
from openfisca_core.tools import assert_near

from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import *  # noqa analysis:ignore
from openfisca_country_template.situation_examples import single


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


@raises(ValueError)
def test_calculate_output_default():
    simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = single)
    simulation.calculate_output('simple_variable', 2017)


def test_calculate_output_add():
    simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = single)
    simulation.set_input('variable_with_calculate_output_add', '2017-01', [10])
    simulation.set_input('variable_with_calculate_output_add', '2017-05', [20])
    simulation.set_input('variable_with_calculate_output_add', '2017-12', [70])
    assert_near(simulation.calculate_output('variable_with_calculate_output_add', 2017), 100)


def test_calculate_output_divide():
    simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = single)
    simulation.set_input('variable_with_calculate_output_divide', 2017, [12000])
    assert_near(simulation.calculate_output('variable_with_calculate_output_divide', '2017-06'), 1000)
