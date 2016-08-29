# -*- coding: utf-8 -*-


from openfisca_core import periods
from openfisca_core.columns import IntCol
from openfisca_core.variables import Variable
from openfisca_core.tests import dummy_country
from openfisca_core.tests.dummy_country import Individus, Simulation
from openfisca_core.tools import assert_near


class formula_1(Variable):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('formula_3', period, choice=0)


class formula_2(Variable):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('formula_3', period, choice=1)


class formula_3(Variable):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period, choice):
        if choice == 0:
            return period, self.zeros()
        else:
            return period, self.zeros() + 1

# TaxBenefitSystem instance declared after formulas
tax_benefit_system = dummy_country.DummyTaxBenefitSystem()
tax_benefit_system.add_variable_classes(formula_1, formula_2, formula_3)

reference_period = periods.period(u'2013')

simulation = Simulation(tax_benefit_system,
    period=reference_period.this_month,
    parent1=dict(),
    )

formula_1_result = simulation.calculate('formula_1')
formula_2_result = simulation.calculate('formula_2')
formula_3 = simulation.variable_by_name['formula_3']


def test_cache():
    assert_near(formula_1_result.value, [0])
    assert_near(formula_2_result.value, [1])


def test_get_extra_param_names():
    assert formula_3.get_extra_param_names() == ('choice',)


def test_json_conversion():
    print(formula_3.to_value_json())
    assert str(formula_3.to_value_json()) == \
        "{'2013-01': {'{choice: 1}': [1], '{choice: 0}': [0]}}"
