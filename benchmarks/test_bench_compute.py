"""Compute time benchmarks for OpenFisca-Core.

Uses pytest-benchmark for statistically rigorous measurements.
Run with: pytest benchmarks/test_bench_compute.py -v --benchmark-sort=name
"""

import pytest

# ---------------------------------------------------------------------------
# S1: members_position (the function we just vectorized)
# ---------------------------------------------------------------------------


class TestMembersPositionBench:
    """Benchmark GroupPopulation.members_position."""

    @pytest.mark.parametrize(
        "nb_persons,nb_entities",
        [
            pytest.param(100, 40, id="N=100"),
            pytest.param(10_000, 4_000, id="N=10K"),
            pytest.param(100_000, 40_000, id="N=100K"),
            pytest.param(1_000_000, 400_000, id="N=1M"),
        ],
    )
    def test_members_position(
        self, benchmark, nb_persons, nb_entities, make_group_population
    ):
        pop = make_group_population(nb_persons, nb_entities)

        def run():
            pop._members_position = None  # force recompute
            return pop.members_position

        result = benchmark.pedantic(run, iterations=3, rounds=5, warmup_rounds=1)
        assert len(result) == nb_persons


# ---------------------------------------------------------------------------
# S2: GroupPopulation aggregations (sum, any)
# ---------------------------------------------------------------------------


class TestGroupAggregationBench:
    """Benchmark household.sum() and household.any()."""

    @pytest.mark.parametrize(
        "nb_persons",
        [
            pytest.param(10_000, id="N=10K"),
            pytest.param(100_000, id="N=100K"),
        ],
    )
    def test_household_sum(self, benchmark, nb_persons, make_simulation):
        sim = make_simulation(nb_persons)

        def run():
            household = sim.populations["household"]
            salaries = household.members("salary", "2024-01")
            return household.sum(salaries)

        result = benchmark.pedantic(run, iterations=5, rounds=5, warmup_rounds=1)
        assert len(result) > 0

    @pytest.mark.parametrize(
        "nb_persons",
        [
            pytest.param(10_000, id="N=10K"),
            pytest.param(100_000, id="N=100K"),
        ],
    )
    def test_household_any(self, benchmark, nb_persons, make_simulation):
        sim = make_simulation(nb_persons)

        def run():
            household = sim.populations["household"]
            salaries = household.members("salary", "2024-01")
            return household.any(salaries > 3000)

        result = benchmark.pedantic(run, iterations=5, rounds=5, warmup_rounds=1)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# S3: Full simulation (disposable_income)
# ---------------------------------------------------------------------------


class TestFullSimulationBench:
    """Benchmark a full disposable_income calculation."""

    @pytest.mark.parametrize(
        "nb_persons",
        [
            pytest.param(100, id="N=100"),
            pytest.param(10_000, id="N=10K"),
            pytest.param(100_000, id="N=100K"),
        ],
    )
    def test_disposable_income(self, benchmark, nb_persons, make_simulation):
        sim = make_simulation(nb_persons)

        def run():
            return sim.calculate("disposable_income", "2024-01")

        result = benchmark.pedantic(run, iterations=1, rounds=3, warmup_rounds=1)
        assert len(result) > 0

    @pytest.mark.parametrize(
        "nb_persons",
        [
            pytest.param(100, id="N=100"),
            pytest.param(10_000, id="N=10K"),
        ],
    )
    def test_income_tax(self, benchmark, nb_persons, make_simulation):
        sim = make_simulation(nb_persons)

        def run():
            return sim.calculate("income_tax", "2024-01")

        result = benchmark.pedantic(run, iterations=3, rounds=5, warmup_rounds=1)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# S4: TBS loading
# ---------------------------------------------------------------------------


class TestTBSLoadingBench:
    """Benchmark TaxBenefitSystem initialization."""

    def test_tbs_loading(self, benchmark):
        def run():
            from openfisca_country_template import CountryTaxBenefitSystem

            return CountryTaxBenefitSystem()

        result = benchmark.pedantic(run, iterations=1, rounds=3, warmup_rounds=1)
        assert result is not None
