"""CPU benchmarks for general OpenFisca-Core operations.

Run with:
    .venv/bin/pytest benchmarks/test_bench_compute.py -v --benchmark-sort=name
"""

from __future__ import annotations

import numpy
import pytest

from openfisca_country_template import CountryTaxBenefitSystem
from openfisca_core.simulation_builder import SimulationBuilder

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

N = 1_000  # population size for compute benchmarks (fast measurements)
PERIOD = "2020-01"


def _build_simulation(n: int = N):
    """Build a simulation with *n* persons spread across households of 3."""
    tbs = CountryTaxBenefitSystem()
    n_hh = n // 3
    persons = {f"p{i}": {} for i in range(n)}
    households = {}
    for h in range(n_hh):
        adults = [f"p{h * 3}", f"p{h * 3 + 1}"]
        child_idx = h * 3 + 2
        if child_idx < n:
            households[f"hh_{h}"] = {"adults": adults, "children": [f"p{child_idx}"]}
        else:
            households[f"hh_{h}"] = {"adults": adults}
    # Handle remaining persons not assigned to a household
    remaining = n - n_hh * 3
    if remaining > 0:
        last_hh = f"hh_{n_hh}"
        adults = [f"p{n_hh * 3 + i}" for i in range(min(remaining, 2))]
        households[last_hh] = {"adults": adults}

    situation = {"persons": persons, "households": households}
    sb = SimulationBuilder()
    sim = sb.build_from_entities(tbs, situation)

    # Pre-load realistic input values
    rng = numpy.random.default_rng(42)
    salary = rng.integers(1_000, 5_000, size=n).astype(float)
    sim.set_input("salary", PERIOD, salary)

    return sim


# ---------------------------------------------------------------------------
# Module-level shared simulation (avoids rebuilding for each test class)
# ---------------------------------------------------------------------------

_SIM = None


def _get_sim():
    global _SIM
    if _SIM is None:
        _SIM = _build_simulation(N)
    return _SIM


# ---------------------------------------------------------------------------
# Benchmark: members_position access
# ---------------------------------------------------------------------------


class TestMembersPositionBench:
    """Measure access to the group population members_position array."""

    def test_members_position(self, benchmark):
        """Read members_position on a household population of ~333 households."""
        sim = _get_sim()
        hh = sim.household

        def _run():
            pos = hh.members_position
            # Force evaluation — sum prevents dead-code elimination
            return pos.sum()

        benchmark(_run)


# ---------------------------------------------------------------------------
# Benchmark: group aggregations
# ---------------------------------------------------------------------------


class TestGroupAggregationBench:
    """Measure household-level aggregation operations."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.sim = _get_sim()
        self.hh = self.sim.household
        self.salary_arr = self.sim.calculate("salary", PERIOD)
        # Derive a boolean "is_employed" from salary > 0
        self.is_employed = self.salary_arr > 0

    def test_household_sum(self, benchmark):
        """household.sum(salary_arr) over ~333 households, 1 000 persons."""
        hh = self.hh
        salary_arr = self.salary_arr

        benchmark(hh.sum, salary_arr)

    def test_household_any(self, benchmark):
        """household.any(is_employed) over ~333 households, 1 000 persons."""
        hh = self.hh
        is_employed = self.is_employed

        benchmark(hh.any, is_employed)


# ---------------------------------------------------------------------------
# Benchmark: full simulation calculate()
# ---------------------------------------------------------------------------


class TestFullSimulationBench:
    """Measure end-to-end variable calculation."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.sim = _get_sim()
        # Warm up the cache by running once before benchmarking
        self.sim.calculate("income_tax", PERIOD)
        self.sim.calculate("disposable_income", PERIOD)

    def test_income_tax(self, benchmark):
        """sim.calculate('income_tax', period) on 1 000 persons (cached)."""
        sim = self.sim

        benchmark(sim.calculate, "income_tax", PERIOD)

    def test_disposable_income(self, benchmark):
        """sim.calculate('disposable_income', period) on 1 000 persons (cached)."""
        sim = self.sim

        benchmark(sim.calculate, "disposable_income", PERIOD)


# ---------------------------------------------------------------------------
# Benchmark: TaxBenefitSystem loading + simulation build
# ---------------------------------------------------------------------------


class TestTBSLoadingBench:
    """Measure the cost of instantiating a TaxBenefitSystem and building a sim."""

    def test_tbs_loading(self, benchmark):
        """CountryTaxBenefitSystem() + SimulationBuilder.build_from_entities()."""

        def _run():
            _build_simulation(N)

        benchmark.pedantic(_run, rounds=5, iterations=1)
