# -*- coding: utf-8 -*-

import pytest

from openfisca_core import periods
from openfisca_core.periods import MONTH
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_core.simulations import CycleError
from openfisca_core.variables import Variable

from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import Person
from openfisca_core.tools import assert_near

from pytest import fixture, raises


@fixture
def reference_period():
    return periods.period('2013-01')


@fixture
def simulation(reference_period):
    return SimulationBuilder().build_default_simulation(tax_benefit_system)


# 1 <--> 2 with same period
class variable1(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        return person('variable2', period)


class variable2(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        return person('variable1', period)


# 3 <--> 4 with a period offset, but without explicit cycle allowed
class variable3(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        return person('variable4', period.last_month)


class variable4(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        return person('variable3', period)


# 5 -f-> 6 with a period offset, with cycle flagged but not allowed
#   <---
class variable5(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        variable6 = person('variable6', period.last_month)
        return 5 + variable6


class variable6(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        variable5 = person('variable5', period)
        return 6 + variable5


# december cotisation depending on november value
class cotisation(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        if period.start.month == 12:
            return 2 * person('cotisation', period.last_month, max_nb_cycles = 1)
        else:
            return person.empty_array() + 1


# 7 -f-> 8 with a period offset, with explicit cycle allowed (1 level)
#   <---
class variable7(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        variable8 = person('variable8', period.last_month, max_nb_cycles = 1)
        return 7 + variable8


class variable8(Variable):
    value_type = int
    entity = Person
    definition_period = MONTH

    def formula(person, period):
        variable7 = person('variable7', period)
        return 8 + variable7


# TaxBenefitSystem instance declared after formulas
tax_benefit_system = CountryTaxBenefitSystem()
tax_benefit_system.add_variables(variable1, variable2, variable3, variable4,
    variable5, variable6, cotisation, variable7, variable8)


def test_pure_cycle(simulation, reference_period):
    with raises(AssertionError):
        simulation.calculate('variable1', period = reference_period)


def test_spirals_result_in_default_value(simulation, reference_period):
    variable3 = simulation.calculate('variable3', period = reference_period)
    assert_near(variable3, [0])


@pytest.mark.xfail
def test_spiral_heuristic(simulation, reference_period):
    """
    Calculate variable5 then variable6 then in the other order, to verify that the first calculated variable
    has no effect on the result.
    """
    variable5 = simulation.calculate('variable5', period = reference_period)
    variable6 = simulation.calculate('variable6', period = reference_period)
    variable6_last_month = simulation.calculate('variable6', reference_period.last_month)
    simulation.tracer.print_computation_log()
    assert_near(variable5, [5])
    assert_near(variable6, [11])
    assert_near(variable6_last_month, [11])


def test_cotisation_1_level(simulation, reference_period):
    month = reference_period.last_month
    cotisation = simulation.calculate('cotisation', period = month)
    assert_near(cotisation, [2])


def test_cycle_1_level(simulation, reference_period):
    variable7 = simulation.calculate('variable7', period = reference_period)
    # variable8 = simulation.calculate('variable8')
    assert_near(variable7, [22])
