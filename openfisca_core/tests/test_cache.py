# -*- coding: utf-8 -*-


from nose.tools import raises

from openfisca_core import periods
from openfisca_core.columns import IntCol
from openfisca_core.formulas import CycleError, Variable
from openfisca_core.tests import dummy_country
from openfisca_core.tests.dummy_country import Individus
from openfisca_core.tools import assert_near


class formula_1(Variable):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('formula_3', period, extra_params  =[0])

class formula_2(Variable):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('formula_3', period, extra_params  =[1])

class formula_3(Variable):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period, choice):
        if choice == 0:
            return period, self.zeros()
        else:
            return period, self.zeros() + 1

# TaxBenefitSystem instance declared after formulas
tax_benefit_system = dummy_country.init_tax_benefit_system()

reference_period = periods.period(u'2013')


def test_extra_parameters():
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        period = reference_period.this_month,
        parent1 = dict(),
        ).new_simulation(debug = True)
    formula_1 = simulation.calculate('formula_1')
    formula_2 = simulation.calculate('formula_2')
    assert_near(formula_1, [0])
    assert_near(formula_2, [1])

