# -*- coding: utf-8 -*-

from openfisca_core import periods
from openfisca_core.simulations import CycleError
from openfisca_core.tools import assert_near

from pytest import fixture, raises


@fixture
def reference_period():
    return periods.period('2013-01')


# december cotisation depending on november value
@fixture
def cotisation(make_variable):
    variable = make_variable('cotisation')

    def formula(person, period):
        if period.start.month == 12:
            return 2 * person('cotisation', period.last_month)
        else:
            return person.empty_array() + 1
    variable.formula = formula
    return variable


@fixture
def cycle_variables(make_variable, cotisation):
    variables = [
        # 1 <--> 2 with same period
        make_variable('variable1', formula = lambda person, period: person('variable2', period)),
        make_variable('variable2', formula = lambda person, period: person('variable1', period)),
        # 3 <--> 4 with a period offset
        make_variable('variable3', formula = lambda person, period: person('variable4', period.last_month)),
        make_variable('variable4', formula = lambda person, period: person('variable3', period)),
        # 5 -f-> 6 with a period offset
        #   <---
        make_variable('variable5', formula = lambda person, period: 5 + person('variable6', period.last_month)),
        make_variable('variable6', formula = lambda person, period: 6 + person('variable5', period)),
        make_variable('variable7', formula = lambda person, period: 7 + person('variable5', period)),
        cotisation
        ]
    return variables


@fixture
def simulation_with_variables(tax_benefit_system, simulation_builder, cycle_variables):
    tax_benefit_system.add_variables(*cycle_variables)
    return simulation_builder.build_default_simulation(tax_benefit_system)


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
