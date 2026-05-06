from __future__ import annotations

import numpy

from openfisca_core import periods, types as t

from ..._store import _CounterFactualStore as Store


def instant(s: str) -> t.Instant:
    return periods.period(s).start


def arr(*values: float) -> t.VarArray:
    return numpy.array(values, dtype=numpy.float32)


def test_clone_returns_same_values() -> None:
    store = Store()
    store.put(instant("2020"), arr(1.0, 2.0))
    store.put(instant("2021"), arr(3.0, 2.0))
    clone = store.clone()
    numpy.testing.assert_array_equal(clone.get(instant("2020")), arr(1.0, 2.0))
    numpy.testing.assert_array_equal(clone.get(instant("2021")), arr(3.0, 2.0))


def test_clone_patches_are_independent() -> None:
    store = Store()
    store.put(instant("2020"), arr(1.0, 2.0))
    clone = store.clone()
    clone.put(instant("2021"), arr(9.0, 2.0))
    assert store.get(instant("2021")) is not None
    numpy.testing.assert_array_equal(store.get(instant("2021")), arr(1.0, 2.0))


def test_clone_shares_base_array() -> None:
    store = Store()
    store.put(instant("2020"), arr(1.0, 2.0))
    clone = store.clone()
    assert clone.get(instant("2020")) is store.get(instant("2020"))


def test_cache_eviction_still_reconstructs_old_instant() -> None:
    store = Store(maxsize=1)
    store.put(instant("2020"), arr(1.0))
    store.put(instant("2021"), arr(2.0))
    store.put(instant("2022"), arr(3.0))
    numpy.testing.assert_array_equal(store.get(instant("2020")), arr(1.0))
    numpy.testing.assert_array_equal(store.get(instant("2022")), arr(3.0))
