# -*- coding: utf-8 -*-

from pytest import fixture

from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_country_template.entities import Person
from openfisca_core.variables import Variable
from openfisca_core.periods import MONTH


@fixture
def month():
    return '2016-05'


@fixture
def make_isolated_simulation(month):
    def _make_simulation(tbs, data):
        builder = SimulationBuilder()
        builder.default_period = month
        return builder.build_from_variables(tbs, data)
    return _make_simulation


class input(Variable):
    value_type = int
    entity = Person
    label = "Input variable"
    definition_period = MONTH


class intermediate(Variable):
    value_type = int
    entity = Person
    label = "Intermediate result that don't need to be cached"
    definition_period = MONTH

    def formula(person, period):
        return person('input', period)


class output(Variable):
    value_type = int
    entity = Person
    label = 'Output variable'
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


def test_without_cache_opt_out(make_isolated_simulation, month):
    simulation = make_isolated_simulation(tax_benefit_system, {'input': 1})
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(month) is not None)


def test_with_cache_opt_out(make_isolated_simulation, month):
    simulation = make_isolated_simulation(tax_benefit_system, {'input': 1})
    simulation.debug = True
    simulation.opt_out_cache = True
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(month) is None)


tax_benefit_system2 = get_filled_tbs()


def test_with_no_blacklist(make_isolated_simulation, month):
    simulation = make_isolated_simulation(tax_benefit_system2, {'input': 1})
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(month) is not None)
