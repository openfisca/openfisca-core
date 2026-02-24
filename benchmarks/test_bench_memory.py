"""Memory benchmarks for OpenFisca-Core.

Uses tracemalloc (stdlib) for peak memory measurements.
Run with: pytest benchmarks/test_bench_memory.py -v -s
(the -s flag is needed to see the printed memory reports)
"""

import tracemalloc

import pytest


def _measure_memory(func):
    """Run func and return (result, current_bytes, peak_bytes)."""
    tracemalloc.start()
    tracemalloc.reset_peak()
    result = func()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, current, peak


def _fmt(nbytes):
    """Format bytes as human-readable string."""
    if nbytes < 1024:
        return f"{nbytes} B"
    if nbytes < 1024**2:
        return f"{nbytes / 1024:.1f} KB"
    return f"{nbytes / 1024**2:.1f} MB"


# ---------------------------------------------------------------------------
# M1: members_position memory
# ---------------------------------------------------------------------------


class TestMembersPositionMemory:
    """Measure memory for members_position computation."""

    @pytest.mark.parametrize(
        "nb_persons",
        [
            pytest.param(10_000, id="N=10K"),
            pytest.param(100_000, id="N=100K"),
            pytest.param(1_000_000, id="N=1M"),
        ],
    )
    def test_members_position_memory(self, nb_persons, make_group_population):
        pop = make_group_population(nb_persons)

        _, current, peak = _measure_memory(lambda: pop.members_position)

        per_person = peak / nb_persons
        print(  # noqa: T201
            f"\n  [members_position] N={nb_persons:>10_d}"
            f"  current={_fmt(current)}"
            f"  peak={_fmt(peak)}"
            f"  per_person={per_person:.0f} B"
        )

        # Sanity check: should not use more than 100 bytes per person
        # (the arrays themselves are ~4 bytes each, but intermediates exist)
        assert per_person < 100, f"Too much memory: {per_person:.0f} B/person"


# ---------------------------------------------------------------------------
# M2: Full simulation memory
# ---------------------------------------------------------------------------


class TestSimulationMemory:
    """Measure memory for full simulation calculations."""

    @pytest.mark.parametrize(
        "nb_persons",
        [
            pytest.param(10_000, id="N=10K"),
            pytest.param(100_000, id="N=100K"),
        ],
    )
    def test_disposable_income_memory(self, nb_persons, make_simulation):
        sim = make_simulation(nb_persons)

        _, current, peak = _measure_memory(
            lambda: sim.calculate("disposable_income", "2024-01")
        )

        per_person = peak / nb_persons
        print(  # noqa: T201
            f"\n  [disposable_income] N={nb_persons:>10_d}"
            f"  current={_fmt(current)}"
            f"  peak={_fmt(peak)}"
            f"  per_person={per_person:.0f} B"
        )

    @pytest.mark.parametrize(
        "nb_persons",
        [
            pytest.param(10_000, id="N=10K"),
            pytest.param(100_000, id="N=100K"),
        ],
    )
    def test_multi_period_memory(self, nb_persons, make_simulation):
        """Measure memory growth over 12 monthly calculations."""
        sim = make_simulation(nb_persons)

        def run_12_months():
            for month in range(1, 13):
                sim.calculate("disposable_income", f"2024-{month:02d}")

        _, current, peak = _measure_memory(run_12_months)

        per_person = peak / nb_persons
        print(  # noqa: T201
            f"\n  [12-month simulation] N={nb_persons:>10_d}"
            f"  current={_fmt(current)}"
            f"  peak={_fmt(peak)}"
            f"  per_person={per_person:.0f} B"
            f"  per_person_per_month={per_person / 12:.0f} B"
        )


# ---------------------------------------------------------------------------
# M3: Per-variable memory cost
# ---------------------------------------------------------------------------


class TestPerVariableMemory:
    """Measure the incremental memory cost of calculating one more variable."""

    def test_per_variable_cost(self, make_simulation):
        nb_persons = 100_000
        sim = make_simulation(nb_persons)

        variables = [
            "salary",
            "income_tax",
            "social_security_contribution",
            "basic_income",
            "pension",
        ]

        print(f"\n  Per-variable memory cost (N={nb_persons:_d}):")  # noqa: T201
        print(
            f"  {'Variable':<35s} {'Current':>10s} {'Peak':>10s} {'Marginal':>10s}"
        )  # noqa: T201
        print(f"  {'-' * 35} {'-' * 10} {'-' * 10} {'-' * 10}")  # noqa: T201

        prev_current = 0
        for var_name in variables:
            tracemalloc.start()
            tracemalloc.reset_peak()
            sim.calculate(var_name, "2024-01")
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            marginal = current - prev_current
            print(  # noqa: T201
                f"  {var_name:<35s}"
                f" {_fmt(current):>10s}"
                f" {_fmt(peak):>10s}"
                f" {_fmt(marginal):>10s}"
            )
            prev_current = current


# ---------------------------------------------------------------------------
# M4: Scaling analysis
# ---------------------------------------------------------------------------


class TestScalingAnalysis:
    """Verify that memory scales linearly with population size."""

    def test_memory_scales_linearly(self, make_simulation):
        """Memory should roughly double when population doubles."""
        sizes = [10_000, 20_000, 40_000]
        peaks = []

        for n in sizes:
            sim = make_simulation(n)
            _, _, peak = _measure_memory(lambda: sim.calculate("income_tax", "2024-01"))
            peaks.append(peak)
            print(f"\n  N={n:>6_d}  peak={_fmt(peak)}")

        # Check roughly linear: ratio should be close to 2
        ratio_1 = peaks[1] / peaks[0]
        ratio_2 = peaks[2] / peaks[1]
        print(f"\n  Ratio {sizes[1]:_}/{sizes[0]:_} = {ratio_1:.2f}x")
        print(f"  Ratio {sizes[2]:_}/{sizes[1]:_} = {ratio_2:.2f}x")

        # Allow tolerance for fixed overhead at small sizes
        assert 1.2 < ratio_1 < 3.0, f"Non-linear scaling: {ratio_1:.2f}x"
        assert 1.2 < ratio_2 < 3.0, f"Non-linear scaling: {ratio_2:.2f}x"
