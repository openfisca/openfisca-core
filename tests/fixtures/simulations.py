import functools

import pytest

from openfisca_core.simulations.simulation_builder import SimulationBuilder


@pytest.fixture
def simulation_builder():
    return SimulationBuilder()


@pytest.fixture
def simulation(simulation_builder, tax_benefit_system, request):
    variables, period = request.param
    return _simulation(simulation_builder, tax_benefit_system, variables, period)


@pytest.fixture
def make_simulation(simulation_builder):
    return functools.partial(_simulation, simulation_builder)


def _simulation(simulation_builder, tax_benefit_system, variables, period):
    simulation_builder.set_default_period(period)
    simulation = \
        simulation_builder \
        .build_from_variables(tax_benefit_system, variables)

    return simulation
