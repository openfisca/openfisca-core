# -*- coding: utf-8 -*-


from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import Person
from openfisca_core.variables import Variable
from openfisca_core.periods import MONTH


class input(Variable):
    value_type = int
    entity = Person
    label = u"Input variable"
    definition_period = MONTH


class intermediate(Variable):
    value_type = int
    entity = Person
    label = u"Intermediate result that don't need to be cached"
    definition_period = MONTH

    def formula(person, period):
        return person('input', period)


class output(Variable):
    value_type = int
    entity = Person
    label = u'Output variable'
    definition_period = MONTH

    def formula(person, period):
        return person('intermediate', period)


def get_filled_tbs():
    tax_benefit_system = CountryTaxBenefitSystem()
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
    simulation = scenario.new_simulation()
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(month) is not None)


def test_with_cache_opt_out():
    simulation = scenario.new_simulation(debug = True, opt_out_cache = True)
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(month) is None)


tax_benefit_system2 = get_filled_tbs()

month = '2016-05'
scenario2 = tax_benefit_system2.new_scenario().init_from_attributes(
    period = month,
    input_variables = {
        'input': 1,
        },
    )


def test_with_no_blacklist():
    simulation = scenario2.new_simulation(opt_out_cache = True)
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(month) is not None)
