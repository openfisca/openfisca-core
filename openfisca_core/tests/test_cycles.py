# -*- coding: utf-8 -*-


from nose.tools import raises

from openfisca_core import periods
from openfisca_core.columns import IntCol
from openfisca_core.formulas import CycleError
from openfisca_core.variables import Variable
from openfisca_core.tests import dummy_country
from openfisca_core.tests.dummy_country import Individu
from openfisca_core.tools import assert_near


# 1 <--> 2 with same period
class variable1(Variable):
    column = IntCol
    entity_class = Individu

    def function(self, simulation, period):
        return period, simulation.calculate('variable2', period)


class variable2(Variable):
    column = IntCol
    entity_class = Individu

    def function(self, simulation, period):
        return period, simulation.calculate('variable1', period)


# 3 <--> 4 with a period offset, but without explicit cycle allowed
class variable3(Variable):
    column = IntCol
    entity_class = Individu

    def function(self, simulation, period):
        return period, simulation.calculate('variable4', period.last_year)


class variable4(Variable):
    column = IntCol
    entity_class = Individu

    def function(self, simulation, period):
        return period, simulation.calculate('variable3', period)


# 5 -f-> 6 with a period offset, with cycle flagged but not allowed
#   <---
class variable5(Variable):
    column = IntCol
    entity_class = Individu

    def function(self, simulation, period):
        variable6 = simulation.calculate('variable6', period.last_year, max_nb_cycles = 0)
        return period, 5 + variable6


class variable6(Variable):
    column = IntCol
    entity_class = Individu

    def function(self, simulation, period):
        variable5 = simulation.calculate('variable5', period)
        return period, 6 + variable5


# december cotisation depending on november value
class cotisation(Variable):
    column = IntCol
    entity_class = Individu

    def function(self, simulation, period):
        period = period.this_month
        if period.start.month == 12:
            return period, 2 * simulation.calculate('cotisation', period.last_month, max_nb_cycles = 1)
        else:
            return period, self.zeros() + 1


# 7 -f-> 8 with a period offset, with explicit cycle allowed (1 level)
#   <---
class variable7(Variable):
    column = IntCol
    entity_class = Individu

    def function(self, simulation, period):
        variable8 = simulation.calculate('variable8', period.last_year, max_nb_cycles = 1)
        return period, 7 + variable8


class variable8(Variable):
    column = IntCol
    entity_class = Individu

    def function(self, simulation, period):
        variable7 = simulation.calculate('variable7', period)
        return period, 8 + variable7


# TaxBenefitSystem instance declared after formulas
tax_benefit_system = dummy_country.DummyTaxBenefitSystem()
tax_benefit_system.add_variables(variable1, variable2, variable3, variable4,
    variable5, variable6, cotisation, variable7, variable8)

reference_period = periods.period(u'2013')


@raises(AssertionError)
def test_pure_cycle():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period,
        parent1 = dict(),
        ).new_simulation(debug = True)
    simulation.calculate('variable1')


@raises(CycleError)
def test_cycle_time_offset():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period,
        parent1 = dict(),
        ).new_simulation(debug = True)
    simulation.calculate('variable3')


def test_allowed_cycle():
    """
    Calculate variable5 then variable6 then in the order order, to verify that the first calculated variable
    has no effect on the result.
    """
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period,
        parent1 = dict(),
        ).new_simulation(debug = True)
    variable6 = simulation.calculate('variable6')
    variable5 = simulation.calculate('variable5')
    variable6_last_year = simulation.calculate('variable6', reference_period.last_year)
    assert_near(variable5, [5])
    assert_near(variable6, [11])
    assert_near(variable6_last_year, [0])


def test_allowed_cycle_different_order():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period,
        parent1 = dict(),
        ).new_simulation(debug = True)
    variable5 = simulation.calculate('variable5')
    variable6 = simulation.calculate('variable6')
    variable6_last_year = simulation.calculate('variable6', reference_period.last_year)
    assert_near(variable5, [5])
    assert_near(variable6, [11])
    assert_near(variable6_last_year, [0])


def test_cotisation_1_level():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period.last_month,  # December
        parent1 = dict(),
        ).new_simulation(debug = True)
    cotisation = simulation.calculate('cotisation')
    assert_near(cotisation, [2])


def test_cycle_1_level():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period,
        parent1 = dict(),
        ).new_simulation(debug = True)
    variable7 = simulation.calculate('variable7')
    # variable8 = simulation.calculate('variable8')
    assert_near(variable7, [22])
