# -*- coding: utf-8 -*-

from openfisca_core.tests.dummy_country import DummyTaxBenefitSystem


tax_benefit_system = DummyTaxBenefitSystem()
scenario = tax_benefit_system.new_scenario().init_single_entity(
    parent1=dict(),
    period=2014,
    )
simulation = scenario.new_simulation(trace=True)


def test_calculate_with_trace():
    simulation.calculate('revenu_disponible', 2014)
