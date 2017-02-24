# -*- coding: utf-8 -*-


from openfisca_core import periods
from openfisca_core.columns import IntCol, BoolCol, MONTH
from openfisca_core.variables import Variable
from openfisca_core.tests import dummy_country
from openfisca_core.tests.dummy_country.entities import Individu
from openfisca_core.tools import assert_near
from openfisca_core.base_functions import requested_period_last_value


class formula_1(Variable):
    column = IntCol
    entity = Individu
    period_behavior = MONTH

    def function(self, simulation, period):
        return simulation.calculate('formula_3', period, extra_params = [0])


class formula_2(Variable):
    column = IntCol
    entity = Individu
    period_behavior = MONTH

    def function(self, simulation, period):
        return simulation.calculate('formula_3', period, extra_params = [1])


class formula_3(Variable):
    column = IntCol
    entity = Individu
    period_behavior = MONTH

    def function(self, simulation, period, choice):
        return self.zeros() + choice


class formula_4(Variable):
    column = BoolCol
    entity = Individu
    base_function = requested_period_last_value
    period_behavior = MONTH

    def function(self, simulation, period, choice):
        return self.zeros() + choice


# TaxBenefitSystem instance declared after formulas
tax_benefit_system = dummy_country.DummyTaxBenefitSystem()
tax_benefit_system.add_variables(formula_1, formula_2, formula_3, formula_4)

reference_period = periods.period(u'2013-01')

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
    assert formula_3_holder.get_extra_param_names(period = None) == ('choice',)


def test_json_conversion():
    print(formula_3_holder.to_value_json())
    assert str(formula_3_holder.to_value_json()) == \
        "{'2013-01': {'{choice: 1}': [1], '{choice: 0}': [0]}}"


def test_base_functions():
    assert simulation.calculate('formula_4', '2013-01', extra_params = [0]) == 0
    assert simulation.calculate('formula_4', '2013-01', extra_params = [1]) == 1

    # With the 'requested_period_last_value' base_function,
    # the value on an month can be infered from the year value, without running the function for that month
    assert simulation.calculate('formula_4', "2013-04", extra_params = [1]) == 1
