from __future__ import annotations

import numpy
import pytest

from openfisca_core import data_storage, periods, types as t


def instant(s: str) -> t.Instant:
    return periods.period(s).start


def arr(*values: float) -> t.VarArray:
    return numpy.array(values, dtype=numpy.float32)


def make_cache() -> data_storage.StorageCache:
    return data_storage.StorageCache(data_storage.InMemoryStorage())


def test_get_unknown_key_returns_none() -> None:
    cache = make_cache()
    assert cache.get(instant("2020")) is None


def test_put_and_get_returns_snapshot() -> None:
    cache = make_cache()
    snap: t.Snapshot = (arr(1.0, 2.0), 0)
    cache.put(instant("2020"), snap)
    result = cache.get(instant("2020"))
    assert result is not None
    array, patch_idx = result
    numpy.testing.assert_array_equal(array, arr(1.0, 2.0))
    assert patch_idx == 0


def test_patch_idx_is_preserved() -> None:
    cache = make_cache()
    cache.put(instant("2020"), (arr(1.0), 5))
    result = cache.get(instant("2020"))
    assert result is not None
    _, patch_idx = result
    assert patch_idx == 5


def test_contains_after_put() -> None:
    cache = make_cache()
    key = instant("2020")
    assert key not in cache
    cache.put(key, (arr(1.0), 0))
    assert key in cache


def test_items_yields_stored_entries() -> None:
    cache = make_cache()
    k1, k2 = instant("2020"), instant("2021")
    cache.put(k1, (arr(1.0), 0))
    cache.put(k2, (arr(2.0), 1))
    keys = {k for k, _ in cache.items()}
    assert keys == {k1, k2}


def test_evict_removes_matching_keys() -> None:
    cache = make_cache()
    cache.put(instant("2020"), (arr(1.0), 0))
    cache.put(instant("2021"), (arr(2.0), 1))
    cache.evict(lambda k: k >= instant("2021"))
    assert cache.get(instant("2021")) is None
    assert cache.get(instant("2020")) is not None


def test_evict_keeps_nonmatching_keys() -> None:
    cache = make_cache()
    cache.put(instant("2020"), (arr(1.0), 0))
    cache.put(instant("2021"), (arr(2.0), 1))
    cache.evict(lambda k: k >= instant("2022"))
    assert cache.get(instant("2020")) is not None
    assert cache.get(instant("2021")) is not None


def test_clear_removes_all() -> None:
    cache = make_cache()
    cache.put(instant("2020"), (arr(1.0), 0))
    cache.put(instant("2021"), (arr(2.0), 1))
    cache.clear()
    assert cache.get(instant("2020")) is None
    assert cache.get(instant("2021")) is None


def test_evict_removes_from_underlying_storage() -> None:
    storage = data_storage.InMemoryStorage()
    cache = data_storage.StorageCache(storage)
    key = instant("2020")
    cache.put(key, (arr(1.0), 0))
    cache.evict(lambda k: True)
    assert len(list(storage.get_known_periods())) == 0


def test_clear_removes_from_underlying_storage() -> None:
    storage = data_storage.InMemoryStorage()
    cache = data_storage.StorageCache(storage)
    cache.put(instant("2020"), (arr(1.0), 0))
    cache.put(instant("2021"), (arr(2.0), 1))
    cache.clear()
    assert len(list(storage.get_known_periods())) == 0


def test_overwrite_key_updates_snapshot() -> None:
    cache = make_cache()
    key = instant("2020")
    cache.put(key, (arr(1.0), 0))
    cache.put(key, (arr(9.0), 3))
    result = cache.get(key)
    assert result is not None
    array, patch_idx = result
    numpy.testing.assert_array_equal(array, arr(9.0))
    assert patch_idx == 3


def test_with_on_disk_storage(tmp_path: pytest.TempPathFactory) -> None:
    storage = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    cache = data_storage.StorageCache(storage)
    key = instant("2020")
    cache.put(key, (arr(1.0, 2.0), 0))
    result = cache.get(key)
    assert result is not None
    numpy.testing.assert_array_equal(result[0], arr(1.0, 2.0))
