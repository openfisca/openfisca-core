import functools

import pytest

from policyengine_core.simulations import SimulationBuilder


@pytest.fixture
def simulation(tax_benefit_system, request):
    variables, period = request.param

    return _simulation(
        SimulationBuilder(), tax_benefit_system, variables, period,
    )


@pytest.fixture
def make_simulation():
    return functools.partial(_simulation, SimulationBuilder())


def _simulation(simulation_builder, tax_benefit_system, variables, period):
    simulation_builder.set_default_period(period)
    simulation = simulation_builder.build_from_variables(
        tax_benefit_system, variables
    )

    return simulation
