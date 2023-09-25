import functools

import pytest

from openfisca_country_template import situation_examples

from openfisca_core.memory_config import MemoryConfig
from openfisca_core.simulations import SimulationBuilder


@pytest.fixture
def memory_config():
    return MemoryConfig(max_memory_occupation=0)


@pytest.fixture
def simulation(tax_benefit_system, request):
    variables, period = request.param

    return _simulation(
        SimulationBuilder(),
        tax_benefit_system,
        variables,
        period,
    )


@pytest.fixture
def make_simulation():
    return functools.partial(_simulation, SimulationBuilder())


def _simulation(simulation_builder, tax_benefit_system, variables, period):
    simulation_builder.set_default_period(period)
    simulation = simulation_builder.build_from_variables(tax_benefit_system, variables)

    return simulation


@pytest.fixture
def single(tax_benefit_system):
    return SimulationBuilder().build_from_entities(
        tax_benefit_system, situation_examples.single
    )


@pytest.fixture
def couple(tax_benefit_system):
    return SimulationBuilder().build_from_entities(
        tax_benefit_system, situation_examples.couple
    )
