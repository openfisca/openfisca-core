"""Shared fixtures for OpenFisca-Core benchmarks."""

from __future__ import annotations

import numpy
import pytest


@pytest.fixture
def rng():
    """A seeded NumPy random generator for reproducible benchmarks."""
    return numpy.random.default_rng(42)


@pytest.fixture(params=[10_000, 100_000, 1_000_000])
def population_size(request):
    """Parametrised population sizes: 10K, 100K, 1M."""
    return request.param


@pytest.fixture
def make_asof_holder():
    """Factory: returns a ready-to-use Holder with as_of='start'."""
    from openfisca_core.entities import Entity
    from openfisca_core.holders import Holder
    from openfisca_core.periods import DateUnit
    from openfisca_core.populations import Population
    from openfisca_core.variables import Variable

    entity = Entity("person", "persons", "", "")

    def _make(count):
        class AsOfVar(Variable):
            entity_class = entity
            entity = entity
            definition_period = DateUnit.MONTH
            value_type = int
            as_of = "start"

        pop = Population(entity)
        pop.simulation = None
        pop.count = count
        return Holder(AsOfVar(), pop)

    return _make
