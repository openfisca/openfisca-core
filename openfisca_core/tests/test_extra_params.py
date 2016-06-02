# -*- coding: utf-8 -*-


from openfisca_core import periods
from openfisca_core.columns import IntCol
from openfisca_core.variables import Variable
from openfisca_core.tests import dummy_country
from openfisca_core.tests.dummy_country import Individus
from openfisca_core.tools import assert_near


class formula_1(Variable):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('formula_3', period, extra_params = [0])


class formula_2(Variable):
    column = IntCol
    entity_class = Individus

    def function(self, simulation, period):
        return period, simulation.calculate('formula_3', period, extra_params = [1])


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
tax_benefit_system.add_variables(formula_1, formula_2, formula_3)

reference_period = periods.period(u'2013')

simulation = tax_benefit_system.new_scenario().init_single_entity(
    period = reference_period.this_month,
    parent1 = dict(),
    ).new_simulation(debug = True)
formula_1_result = simulation.calculate('formula_1')
formula_2_result = simulation.calculate('formula_2')
formula_3_holder = simulation.holder_by_name['formula_3']


def test_cache():
    assert_near(formula_1_result, [0])
    assert_near(formula_2_result, [1])


def test_get_extra_param_names():
    assert formula_3_holder.get_extra_param_names() == ('choice',)


def test_json_conversion():
    print(formula_3_holder.to_value_json())
    assert str(formula_3_holder.to_value_json()) == \
        "{'2013-01': {'{choice: 1}': [1], '{choice: 0}': [0]}}"
