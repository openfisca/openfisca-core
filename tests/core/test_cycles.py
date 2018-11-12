# -*- coding: utf-8 -*-


from __future__ import unicode_literals, print_function, division, absolute_import
from nose.tools import raises

from openfisca_core import periods
from openfisca_core.periods import MONTH
from openfisca_core.simulations import CycleError
from openfisca_core.variables import Variable

from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import Person
from openfisca_core.tools import assert_near


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
        variable6 = person('variable6', period.last_month, max_nb_cycles = 0)
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

reference_period = periods.period('2013-01')


@raises(AssertionError)
def test_pure_cycle():
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = reference_period,
        ).new_simulation(debug = True)
    simulation.calculate('variable1', period = reference_period)


@pytest.mark.skip(reason="The first variable to fail with CycleError (variable4 here) now returns None")
@raises(CycleError)
def test_cycle_time_offset():
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = reference_period,
        ).new_simulation(debug = True)
    simulation.calculate('variable3', period = reference_period)


def test_allowed_cycle():
    """
    Calculate variable5 then variable6 then in the order order, to verify that the first calculated variable
    has no effect on the result.
    """
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = reference_period,
        ).new_simulation(debug = True)
    variable6 = simulation.calculate('variable6', period = reference_period)
    variable5 = simulation.calculate('variable5', period = reference_period)
    variable6_last_month = simulation.calculate('variable6', reference_period.last_month)
    assert_near(variable5, [5])
    assert_near(variable6, [11])
    assert_near(variable6_last_month, [0])


def test_allowed_cycle_different_order():
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = reference_period,
        ).new_simulation(debug = True)
    variable5 = simulation.calculate('variable5', period = reference_period)
    variable6 = simulation.calculate('variable6', period = reference_period)
    variable6_last_month = simulation.calculate('variable6', reference_period.last_month)
    assert_near(variable5, [5])
    assert_near(variable6, [11])
    assert_near(variable6_last_month, [0])


def test_cotisation_1_level():
    month = reference_period.last_month
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = month,  # December
        ).new_simulation(debug = True)
    cotisation = simulation.calculate('cotisation', period = month)
    assert_near(cotisation, [2])


def test_cycle_1_level():
    simulation = tax_benefit_system.new_scenario().init_from_attributes(
        period = reference_period,
        ).new_simulation(debug = True)
    variable7 = simulation.calculate('variable7', period = reference_period)
    # variable8 = simulation.calculate('variable8')
    assert_near(variable7, [22])
