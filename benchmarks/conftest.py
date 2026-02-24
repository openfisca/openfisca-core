"""Shared fixtures for OpenFisca benchmarks."""

import numpy
import pytest


@pytest.fixture(params=[100, 10_000, 100_000, 1_000_000], ids=lambda n: f"N={n:_}")
def population_size(request):
    """Population sizes to benchmark."""
    return request.param


@pytest.fixture(params=[100, 10_000, 100_000], ids=lambda n: f"N={n:_}")
def simulation_size(request):
    """Population sizes for full simulation benchmarks (capped for speed)."""
    return request.param


@pytest.fixture
def rng():
    """Deterministic random number generator."""
    return numpy.random.default_rng(42)


@pytest.fixture
def make_group_population():
    """Factory to create a GroupPopulation with random entity assignment."""

    def _make(nb_persons, nb_entities=None):
        from openfisca_core.populations.group_population import GroupPopulation

        if nb_entities is None:
            nb_entities = max(1, nb_persons // 3)

        rng = numpy.random.default_rng(42)
        pop = GroupPopulation.__new__(GroupPopulation)
        pop._members_entity_id = rng.integers(0, nb_entities, size=nb_persons)
        pop._members_position = None
        pop._ordered_members_map = None
        return pop

    return _make


@pytest.fixture
def make_simulation():
    """Factory to create a Simulation with salary input."""

    def _make(nb_persons):
        from openfisca_country_template import CountryTaxBenefitSystem

        from openfisca_core.simulations import SimulationBuilder

        tbs = CountryTaxBenefitSystem()
        sim = SimulationBuilder().build_default_simulation(tbs, count=nb_persons)

        rng = numpy.random.default_rng(42)
        sim.set_input("salary", "2024-01", rng.uniform(1000, 5000, nb_persons))
        return sim

    return _make
