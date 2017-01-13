# -*- coding: utf-8 -*-


from nose.tools import raises

from openfisca_core.tests.dummy_country import DummyTaxBenefitSystem


tax_benefit_system = DummyTaxBenefitSystem()
scenario = tax_benefit_system.new_scenario().init_single_entity(
    parent1=dict(),
    period=2014,
    )
simulation = scenario.new_simulation(trace=True)


def test_calculate_with_print_trace():
    simulation.calculate('revenu_disponible', 2014, print_trace=True)


def test_calculate_with_print_trace_and_max_depth():
    simulation.calculate('revenu_disponible', 2014, print_trace=True, max_depth=0)
    simulation.calculate('revenu_disponible', 2014, print_trace=True, max_depth=1)
    simulation.calculate('revenu_disponible', 2014, print_trace=True, max_depth=5)
    simulation.calculate('revenu_disponible', 2014, print_trace=True, max_depth=1000)
    simulation.calculate('revenu_disponible', 2014, print_trace=True, max_depth=-1)
    simulation.calculate('revenu_disponible', 2014, print_trace=True, max_depth=None)


@raises(ValueError)
def test_calculate_with_print_trace_and_invalid_max_depth():
    simulation.calculate('revenu_disponible', 2014, print_trace=True, max_depth=-2)


@raises(ValueError)
def test_calculate_with_print_trace_without_trace_option():
    simulation = scenario.new_simulation()
    simulation.calculate('revenu_disponible', 2014, print_trace=True)
