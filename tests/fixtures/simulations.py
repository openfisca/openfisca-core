import pytest

from openfisca_core.simulation_builder import SimulationBuilder


@pytest.fixture
def simulation_builder():
    return SimulationBuilder()


@pytest.fixture
def simulation(simulation_builder, tax_benefit_system, request):
    variables, period = request.param
    simulation_builder.set_default_period(period)
    simulation = \
        simulation_builder \
        .build_from_variables(tax_benefit_system, variables)

    return simulation
