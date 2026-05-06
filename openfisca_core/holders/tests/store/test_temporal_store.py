from __future__ import annotations

import numpy
import pytest

from openfisca_core import periods, types as t

from ..._cache import _FIFOCache
from ..._store import _TemporalStore


def instant(s: str) -> t.Instant:
    return periods.period(s).start


def arr(*values: float) -> t.VarArray:
    return numpy.array(values, dtype=numpy.float32)


def make_store() -> _TemporalStore:
    return _TemporalStore(snapshots=_FIFOCache(maxsize=10))


def test_get_before_put_returns_none() -> None:
    store = make_store()
    assert store.get(instant("2020")) is None


def test_first_put_establishes_base() -> None:
    store = make_store()
    store.put(instant("2020"), arr(1.0, 2.0))
    result = store.get(instant("2020"))
    assert result is not None
    numpy.testing.assert_array_equal(result, arr(1.0, 2.0))


def test_get_before_base_instant_returns_none() -> None:
    store = make_store()
    store.put(instant("2021"), arr(1.0, 2.0))
    assert store.get(instant("2020")) is None


def test_get_at_base_instant_after_later_puts_returns_base() -> None:
    store = make_store()
    store.put(instant("2020"), arr(1.0, 2.0))
    store.put(instant("2021"), arr(9.0, 2.0))
    numpy.testing.assert_array_equal(store.get(instant("2020")), arr(1.0, 2.0))


def test_sequential_put_reflects_latest_values() -> None:
    store = make_store()
    store.put(instant("2020"), arr(1.0, 2.0))
    store.put(instant("2021"), arr(3.0, 2.0))
    numpy.testing.assert_array_equal(store.get(instant("2021")), arr(3.0, 2.0))


def test_get_between_puts_interpolates_correctly() -> None:
    store = make_store()
    store.put(instant("2020"), arr(1.0, 1.0))
    store.put(instant("2022"), arr(9.0, 1.0))
    numpy.testing.assert_array_equal(store.get(instant("2021")), arr(1.0, 1.0))


def test_no_patch_stored_when_values_unchanged() -> None:
    store = make_store()
    store.put(instant("2020"), arr(1.0, 2.0))
    store.put(instant("2021"), arr(1.0, 2.0))
    numpy.testing.assert_array_equal(store.get(instant("2021")), arr(1.0, 2.0))


def test_out_of_order_put_corrects_earlier_instant() -> None:
    store = make_store()
    store.put(instant("2020"), arr(0.0, 0.0))
    store.put(instant("2022"), arr(5.0, 0.0))
    store.put(instant("2021"), arr(1.0, 0.0))
    numpy.testing.assert_array_equal(store.get(instant("2021")), arr(1.0, 0.0))
    numpy.testing.assert_array_equal(store.get(instant("2022")), arr(5.0, 0.0))


def test_put_sparse_before_base_raises() -> None:
    store = make_store()
    with pytest.raises(ValueError):
        store.put_sparse(instant("2020"), numpy.array([0], dtype=numpy.int32), arr(9.0))


def test_put_sparse_empty_idx_is_noop() -> None:
    store = make_store()
    store.put(instant("2020"), arr(1.0, 2.0))
    store.put_sparse(
        instant("2021"),
        numpy.array([], dtype=numpy.int32),
        numpy.array([], dtype=numpy.float32),
    )
    numpy.testing.assert_array_equal(store.get(instant("2021")), arr(1.0, 2.0))


def test_put_sparse_applies_patch() -> None:
    store = make_store()
    store.put(instant("2020"), arr(1.0, 2.0, 3.0))
    store.put_sparse(
        instant("2021"),
        numpy.array([1], dtype=numpy.int32),
        arr(9.0),
    )
    numpy.testing.assert_array_equal(store.get(instant("2021")), arr(1.0, 9.0, 3.0))


def test_put_sparse_does_not_change_earlier_instant() -> None:
    store = make_store()
    store.put(instant("2020"), arr(1.0, 2.0, 3.0))
    store.put_sparse(
        instant("2021"),
        numpy.array([1], dtype=numpy.int32),
        arr(9.0),
    )
    numpy.testing.assert_array_equal(store.get(instant("2020")), arr(1.0, 2.0, 3.0))


def test_returned_array_is_read_only() -> None:
    store = make_store()
    store.put(instant("2020"), arr(1.0, 2.0))
    result = store.get(instant("2020"))
    assert result is not None
    assert not result.flags.writeable
