import pytest

from openfisca_core.simulation_builder import SimulationBuilder


@pytest.fixture
def simulation_builder():
    return SimulationBuilder()
