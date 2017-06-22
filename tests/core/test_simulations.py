# -*- coding: utf-8 -*-

from openfisca_country_template import CountryTaxBenefitSystem

from openfisca_core.formulas import Formula

tax_benefit_system = CountryTaxBenefitSystem()
scenario = tax_benefit_system.new_scenario().init_from_attributes(
    period=2014
    )


def test_calculate_with_trace():
    simulation = scenario.new_simulation(trace=True)
    simulation.calculate('disposable_income', "2014-01")


def test_calculate__holder_attribute_content():
    simulation = scenario.new_simulation()

    variable_name = 'disposable_income'
    period = "2014-01"
    simulation.calculate(variable_name, period)  # numpy.ndarray
    simulation_holder = simulation.person.get_holder(variable_name)

    assert issubclass(simulation_holder.formula.__class__, Formula)
    assert len(simulation_holder.formula.dated_formulas) > 0  # contains formulas instances
