# -*- coding: utf-8 -*-


from openfisca_core.tests import dummy_country
from openfisca_core.formulas import Variable
from openfisca_core.columns import IntCol
from openfisca_core.tests.dummy_country import Individus


class input(Variable):
    column = IntCol
    entity_class = Individus
    label = u"Input variable"


class intermediate(Variable):
    column = IntCol
    entity_class = Individus
    label = u"Intermediate result that don't need to be cached"

    def function(self, simulation, period):
        return period, simulation.calculate('input', period)


class output(Variable):
    column = IntCol
    entity_class = Individus
    label = u'Output variable'

    def function(self, simulation, period):
        return period, simulation.calculate('intermediate', period)

cache_blacklist = set(['intermediate'])

# TaxBenefitSystem instance declared after formulas
tax_benefit_system = dummy_country.init_tax_benefit_system()
scenario = tax_benefit_system.new_scenario().init_from_attributes(
    period = 2016,
    input_variables = {
        'input': 1,
        },
    )

def test_without_cache_opt_out():
    simulation = scenario.new_simulation(debug = True)
    simulation.calculate('output')
    intermediate_cache = simulation.get_or_new_holder('intermediate')
    assert(len(intermediate_cache._array_by_period) > 0)

def test_with_cache_opt_out():
    simulation = scenario.new_simulation(debug = True, opt_out_cache = True)
    simulation.cache_blacklist = cache_blacklist
    simulation.calculate('output')
    intermediate_cache = simulation.get_or_new_holder('intermediate')
    assert(intermediate_cache._array_by_period is None)
