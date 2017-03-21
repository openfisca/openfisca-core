# -*- coding: utf-8 -*-


from openfisca_dummy_country import DummyTaxBenefitSystem
from openfisca_dummy_country.entities import Individu
from openfisca_core.variables import Variable
from openfisca_core.columns import IntCol
from openfisca_core.periods import MONTH


class input(Variable):
    column = IntCol
    entity = Individu
    label = u"Input variable"
    definition_period = MONTH


class intermediate(Variable):
    column = IntCol
    entity = Individu
    label = u"Intermediate result that don't need to be cached"
    definition_period = MONTH

    def function(self, simulation, period):
        return simulation.calculate('input', period)


class output(Variable):
    column = IntCol
    entity = Individu
    label = u'Output variable'
    definition_period = MONTH

    def function(self, simulation, period):
        return simulation.calculate('intermediate', period)


def get_filled_tbs():
    tax_benefit_system = DummyTaxBenefitSystem()
    tax_benefit_system.add_variables(input, intermediate, output)

    return tax_benefit_system


# TaxBenefitSystem instance declared after formulas


tax_benefit_system = get_filled_tbs()


tax_benefit_system.cache_blacklist = set(['intermediate'])


month = '2016-05'
scenario = tax_benefit_system.new_scenario().init_from_attributes(
    period = month,
    input_variables = {
        'input': 1,
        },
    )


def test_without_cache_opt_out():
    simulation = scenario.new_simulation(debug = True)
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.get_or_new_holder('intermediate')
    assert(len(intermediate_cache._array_by_period) > 0)


def test_with_cache_opt_out():
    simulation = scenario.new_simulation(debug = True, opt_out_cache = True)
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.get_or_new_holder('intermediate')
    assert(intermediate_cache._array_by_period is None)


tax_benefit_system2 = get_filled_tbs()

month = '2016-09'
scenario2 = tax_benefit_system2.new_scenario().init_from_attributes(
    period = month,
    input_variables = {
        'input': 1,
        },
    )


def test_with_no_blacklist():
    simulation = scenario2.new_simulation(debug = True, opt_out_cache = True)
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.get_or_new_holder('intermediate')
    assert(len(intermediate_cache._array_by_period) > 0)
