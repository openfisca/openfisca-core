# Benchmarks

## How to run

```bash
# Run all benchmarks
make benchmark

# Run compute benchmarks only
.venv/bin/python -m pytest benchmarks/test_bench_compute.py -v --benchmark-sort=name

# Run memory benchmarks only
.venv/bin/python -m pytest benchmarks/test_bench_memory.py -v -s

# Save results for later comparison
.venv/bin/python -m pytest benchmarks/ --benchmark-save=my_baseline

# Compare with a saved baseline
.venv/bin/python -m pytest benchmarks/ --benchmark-compare=0001_my_baseline
```

## Benchmarks included

### Compute (`test_bench_compute.py`)

| Benchmark | What it measures | Sizes |
|---|---|---|
| `members_position` | GroupPopulation position assignment | 100 → 1M |
| `group_sum` | `household.sum(salary)` | 100 → 1M |
| `disposable_income` | Full variable cascade (~15 vars) | 100 → 100K |
| `tbs_loading` | TaxBenefitSystem initialization | 1 |

### Memory (`test_bench_memory.py`)

| Benchmark | What it measures | Sizes |
|---|---|---|
| `members_position_memory` | Peak memory for position calc | 10K → 1M |
| `simulation_memory` | Peak memory for full simulation | 10K → 1M |
| `per_variable_memory` | Memory per variable per person | 10K → 100K |
