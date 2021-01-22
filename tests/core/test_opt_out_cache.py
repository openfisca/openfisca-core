# -*- coding: utf-8 -*-

from pytest import fixture

from openfisca_country_template.entities import Person
from openfisca_core.variables import Variable
from openfisca_core.periods import MONTH


@fixture
def month():
    return '2016-05'


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


@fixture
def simulation(tax_benefit_system, make_isolated_simulation):
    tax_benefit_system.cache_blacklist = set(['intermediate'])
    tax_benefit_system.add_variables(input, intermediate, output)
    return make_isolated_simulation(tax_benefit_system, {'input': 1})


def test_without_cache_opt_out(simulation, month):
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(month) is not None)


def test_with_cache_opt_out(simulation, month):
    simulation.debug = True
    simulation.opt_out_cache = True
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(month) is None)


def test_with_no_blacklist(simulation, month):
    simulation.calculate('output', period = month)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(month) is not None)
