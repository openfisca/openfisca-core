# -*- coding: utf-8 -*-

from openfisca_country_template import CountryTaxBenefitSystem

tax_benefit_system = CountryTaxBenefitSystem()
scenario = tax_benefit_system.new_scenario().init_from_attributes(
    period=2014
    )


def test_calculate_with_trace():
    simulation = scenario.new_simulation(trace=True)
    simulation.calculate('disposable_income', "2014-01")
