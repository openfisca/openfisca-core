import pytest

from openfisca_country_template.entities import Person

from openfisca_core import periods
from openfisca_core.variables import Variable

PERIOD = periods.build_period("2016-01")


class input(Variable):
    value_type = int
    entity = Person
    label = "Input variable"
    definition_period = periods.DateUnit.MONTH


class intermediate(Variable):
    value_type = int
    entity = Person
    label = "Intermediate result that don't need to be cached"
    definition_period = periods.DateUnit.MONTH

    def formula(person, period):
        return person('input', period)


class output(Variable):
    value_type = int
    entity = Person
    label = 'Output variable'
    definition_period = periods.DateUnit.MONTH

    def formula(person, period):
        return person('intermediate', period)


@pytest.fixture(scope = "module", autouse = True)
def add_variables_to_tax_benefit_system(tax_benefit_system):
    tax_benefit_system.add_variables(input, intermediate, output)


@pytest.fixture(scope = "module", autouse = True)
def add_variables_to_cache_blakclist(tax_benefit_system):
    tax_benefit_system.cache_blacklist = set(['intermediate'])


@pytest.mark.parametrize("simulation", [({'input': 1}, PERIOD)], indirect = True)
def test_without_cache_opt_out(simulation):
    simulation.calculate('output', period = PERIOD)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(PERIOD) is not None)


@pytest.mark.parametrize("simulation", [({'input': 1}, PERIOD)], indirect = True)
def test_with_cache_opt_out(simulation):
    simulation.debug = True
    simulation.opt_out_cache = True
    simulation.calculate('output', period = PERIOD)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(PERIOD) is None)


@pytest.mark.parametrize("simulation", [({'input': 1}, PERIOD)], indirect = True)
def test_with_no_blacklist(simulation):
    simulation.calculate('output', period = PERIOD)
    intermediate_cache = simulation.persons.get_holder('intermediate')
    assert(intermediate_cache.get_array(PERIOD) is not None)
