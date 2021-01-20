# -*- coding: utf-8 -*-

from openfisca_core import periods
from openfisca_core.simulations import CycleError
from openfisca_core.tools import assert_near

from pytest import fixture, raises


@fixture
def reference_period():
    return periods.period('2013-01')


def test_pure_cycle(simulation_with_variables, reference_period):
    with raises(CycleError):
        simulation_with_variables.calculate('variable1', period = reference_period)


def test_spirals_result_in_default_value(simulation_with_variables, reference_period):
    variable3 = simulation_with_variables.calculate('variable3', period = reference_period)
    assert_near(variable3, [0])


def test_spiral_heuristic(simulation_with_variables, reference_period):
    variable5 = simulation_with_variables.calculate('variable5', period = reference_period)
    variable6 = simulation_with_variables.calculate('variable6', period = reference_period)
    variable6_last_month = simulation_with_variables.calculate('variable6', reference_period.last_month)
    assert_near(variable5, [11])
    assert_near(variable6, [11])
    assert_near(variable6_last_month, [11])


def test_spiral_cache(simulation_with_variables, reference_period):
    simulation_with_variables.calculate('variable7', period = reference_period)
    cached_variable7 = simulation_with_variables.get_holder('variable7').get_array(reference_period)
    assert cached_variable7 is not None


def test_cotisation_1_level(simulation_with_variables, reference_period):
    month = reference_period.last_month
    cotisation = simulation_with_variables.calculate('cotisation', period = month)
    assert_near(cotisation, [0])
