"""Benchmarks for as_of variable sparse patch storage.

Run with:
    .venv/bin/pytest benchmarks/test_bench_asof.py -v -s -k memory
    .venv/bin/pytest benchmarks/test_bench_asof.py -v --benchmark-sort=name -k compute
"""

from __future__ import annotations

import numpy
import pytest

from openfisca_core.entities import Entity
from openfisca_core.holders import Holder
from openfisca_core.periods import DateUnit, period
from openfisca_core.populations import Population
from openfisca_core.variables import Variable

# ---------------------------------------------------------------------------
# Local helpers
# ---------------------------------------------------------------------------

_entity = Entity("person", "persons", "", "")


class _AsOfVar(Variable):
    entity = _entity
    definition_period = DateUnit.MONTH
    value_type = int
    as_of = "start"


def _make_holder(count: int) -> Holder:
    pop = Population(_entity)
    pop.simulation = None
    pop.count = count
    return Holder(_AsOfVar(), pop)


def _populate(holder: Holder, n_patches: int, change_rate: float, rng) -> None:
    """Set a base array then *n_patches* incremental updates.

    Each patch randomly changes *change_rate* fraction of individuals.
    """
    n = holder.population.count
    base = rng.integers(0, 10, size=n).astype(numpy.int32)
    holder.set_input("2020-01", base)

    current = base.copy()
    for p in range(1, n_patches + 1):
        month = f"2020-{p + 1:02d}" if p < 12 else f"{2020 + p // 12}-{p % 12 + 1:02d}"
        k = max(1, int(n * change_rate))
        idx = rng.choice(n, size=k, replace=False)
        current = current.copy()
        current[idx] = rng.integers(0, 10, size=k).astype(numpy.int32)
        holder.set_input(month, current)


def _patch_memory(holder: Holder) -> int:
    """Return bytes used by sparse storage (base + all patches)."""
    base_bytes = holder._as_of_base.nbytes
    patch_bytes = sum(
        idx.nbytes + vals.nbytes for _, idx, vals in holder._as_of_patches
    )
    return base_bytes + patch_bytes


def _dense_memory(n: int, dtype, n_periods: int) -> int:
    """Return bytes that dense storage (1 full array per period) would use."""
    return n * numpy.dtype(dtype).itemsize * n_periods


# ---------------------------------------------------------------------------
# Memory benchmarks
# ---------------------------------------------------------------------------


class TestAsOfMemory:
    """Compare sparse storage vs hypothetical dense storage."""

    @pytest.mark.parametrize(
        "n,n_patches,change_rate",
        [
            (10_000, 30, 0.005),
            (100_000, 30, 0.005),
            (1_000_000, 30, 0.005),
        ],
        ids=["10K-30p-0.5%", "100K-30p-0.5%", "1M-30p-0.5%"],
    )
    def test_memory_dense_vs_patches(self, n, n_patches, change_rate, capsys):
        rng = numpy.random.default_rng(42)
        holder = _make_holder(n)
        _populate(holder, n_patches, change_rate, rng)

        sparse = _patch_memory(holder)
        dense = _dense_memory(n, holder._as_of_base.dtype, n_patches + 1)
        ratio = dense / sparse

        with capsys.disabled():
            print(
                f"\n  N={n:>9,}  patches={n_patches}  r={change_rate:.1%}"
                f"  sparse={sparse / 1e6:.2f} Mo"
                f"  dense={dense / 1e6:.2f} Mo"
                f"  ratio={ratio:.1f}×"
            )

        if n == 1_000_000:
            assert (
                ratio > 10
            ), f"Expected >10× memory gain for N=1M, r=0.5%, P=30; got {ratio:.1f}×"


# ---------------------------------------------------------------------------
# Compute benchmarks
# ---------------------------------------------------------------------------


class TestAsOfCompute:
    """Measure GET performance for sequential and backward-jump access."""

    N = 1_000_000
    N_PATCHES = 30
    CHANGE_RATE = 0.005

    @pytest.fixture(autouse=True)
    def _holder(self):
        rng = numpy.random.default_rng(42)
        self.holder = _make_holder(self.N)
        _populate(self.holder, self.N_PATCHES, self.CHANGE_RATE, rng)
        # Build the list of period strings that were stored
        self.periods = ["2020-01"]
        for p in range(1, self.N_PATCHES + 1):
            month = (
                f"2020-{p + 1:02d}" if p < 12 else f"{2020 + p // 12}-{p % 12 + 1:02d}"
            )
            self.periods.append(month)

    def test_get_sequential(self, benchmark):
        """360 sequential GETs on 1M persons with 30 patches (snapshot cursor)."""
        holder = self.holder
        periods_objs = [period(p) for p in self.periods]
        # Extend to 360 periods by repeating the last period
        while len(periods_objs) < 360:
            periods_objs.append(periods_objs[-1])

        def _run():
            for p in periods_objs:
                holder._as_of_snapshot = None  # reset snapshot for fair comparison
            holder._as_of_snapshot = None
            for p in periods_objs:
                holder.get_array(p)

        benchmark.pedantic(_run, rounds=5, iterations=1)

    def test_get_sequential_with_snapshot(self, benchmark):
        """360 sequential GETs on 1M persons — snapshot cursor warmed up."""
        holder = self.holder
        periods_objs = [period(p) for p in self.periods]
        while len(periods_objs) < 360:
            periods_objs.append(periods_objs[-1])

        # Warm up snapshot at the start
        holder.get_array(periods_objs[0])

        def _run():
            for p in periods_objs:
                holder.get_array(p)

        benchmark.pedantic(_run, rounds=5, iterations=1)

    def test_get_backward_jump(self, benchmark):
        """GET at last period then GET at first period (backward jump = O(N+k×P))."""
        holder = self.holder
        first = period(self.periods[0])
        last = period(self.periods[-1])

        def _run():
            holder.get_array(last)  # forward → builds snapshot
            holder.get_array(first)  # backward → full reconstruction

        benchmark.pedantic(_run, rounds=5, iterations=1)


# ---------------------------------------------------------------------------
# Forward-simulation benchmark (real use case)
# ---------------------------------------------------------------------------


class TestForwardSimulationBench:
    """Model the real use case: month-by-month simulation.

    Pattern: GET(M-1) → apply rule → SET(M) → GET(M) → apply rule → SET(M+1)...

    Each echelon at month M depends on echelon at month M-1 plus a stochastic
    transition (some fraction of persons change state each month).
    """

    N = 1_000_000

    @pytest.mark.parametrize(
        "n_months,change_rate",
        [
            (12, 0.10),
            (60, 0.10),
            (60, 0.30),
        ],
        ids=["1yr-10%", "5yr-10%", "5yr-30%"],
    )
    def test_forward_simulation(self, benchmark, n_months, change_rate):
        """Forward GET→SET simulation over n_months on 1M persons."""
        N = self.N
        rng = numpy.random.default_rng(42)

        # Pre-generate all random transitions (excludes RNG cost from timing)
        k = max(1, int(N * change_rate))
        all_idx = [rng.choice(N, size=k, replace=False) for _ in range(n_months)]
        all_vals = [
            rng.integers(0, 10, size=k).astype(numpy.int32) for _ in range(n_months)
        ]

        base = rng.integers(0, 10, size=N).astype(numpy.int32)
        months = ["2020-01"] + [
            f"{2020 + m // 12}-{m % 12 + 1:02d}" for m in range(1, n_months + 1)
        ]
        months_periods = [period(m) for m in months]

        def _run():
            h = _make_holder(N)
            h.set_input(months[0], base.copy())
            for m in range(1, n_months + 1):
                h.set_input_sparse(months[m], all_idx[m - 1], all_vals[m - 1])

        benchmark.pedantic(_run, rounds=3, iterations=1)


# ---------------------------------------------------------------------------
# set_input_sparse vs set_input comparison
# ---------------------------------------------------------------------------


class TestSetInputSparseVsDense:
    """Compare set_input (dense O(N) diff) vs set_input_sparse (O(k) + O(N) snapshot).

    Run with:
        .venv/bin/pytest benchmarks/test_bench_asof.py -v --benchmark-sort=name -k "sparse"
    """

    N = 1_000_000

    @pytest.mark.parametrize(
        "n_months,change_rate",
        [
            (12, 0.10),
            (60, 0.10),
            (60, 0.30),
        ],
        ids=["1yr-10%", "5yr-10%", "5yr-30%"],
    )
    def test_dense(self, benchmark, n_months, change_rate):
        """Forward simulation using set_input — O(N) diff + copy per SET."""
        N = self.N
        rng = numpy.random.default_rng(42)
        k = max(1, int(N * change_rate))
        all_idx = [rng.choice(N, size=k, replace=False) for _ in range(n_months)]
        all_vals = [
            rng.integers(0, 10, size=k).astype(numpy.int32) for _ in range(n_months)
        ]
        base = rng.integers(0, 10, size=N).astype(numpy.int32)
        months = ["2020-01"] + [
            f"{2020 + m // 12}-{m % 12 + 1:02d}" for m in range(1, n_months + 1)
        ]
        months_periods = [period(m) for m in months]

        def _run():
            h = _make_holder(N)
            h.set_input(months[0], base.copy())
            for m in range(1, n_months + 1):
                prev = h.get_array(months_periods[m - 1])
                new_val = prev.copy()
                new_val[all_idx[m - 1]] = all_vals[m - 1]
                h.set_input(months[m], new_val)

        benchmark.pedantic(_run, rounds=3, iterations=1)

    @pytest.mark.parametrize(
        "n_months,change_rate",
        [
            (12, 0.10),
            (60, 0.10),
            (60, 0.30),
        ],
        ids=["1yr-10%", "5yr-10%", "5yr-30%"],
    )
    def test_sparse(self, benchmark, n_months, change_rate):
        """Forward simulation using set_input_sparse — skips O(N) diff entirely."""
        N = self.N
        rng = numpy.random.default_rng(42)
        k = max(1, int(N * change_rate))
        all_idx = [rng.choice(N, size=k, replace=False) for _ in range(n_months)]
        all_vals = [
            rng.integers(0, 10, size=k).astype(numpy.int32) for _ in range(n_months)
        ]
        base = rng.integers(0, 10, size=N).astype(numpy.int32)
        months = ["2020-01"] + [
            f"{2020 + m // 12}-{m % 12 + 1:02d}" for m in range(1, n_months + 1)
        ]

        def _run():
            h = _make_holder(N)
            h.set_input(months[0], base.copy())
            for m in range(1, n_months + 1):
                h.set_input_sparse(months[m], all_idx[m - 1], all_vals[m - 1])

        benchmark.pedantic(_run, rounds=3, iterations=1)
