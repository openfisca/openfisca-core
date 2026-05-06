from __future__ import annotations

import numpy

from openfisca_core import data_storage, periods, types as t


def period(s: str) -> t.Period:
    return periods.period(s)


def arr(*values: float) -> t.VarArray:
    return numpy.array(values, dtype=numpy.float32)


def test_get_unknown_period_returns_none() -> None:
    storage = data_storage.InMemoryStorage()
    assert storage.get(period("2020")) is None


def test_put_and_get_returns_value() -> None:
    storage = data_storage.InMemoryStorage()
    storage.put(arr(1.0, 2.0), period("2020"))
    numpy.testing.assert_array_equal(storage.get(period("2020")), arr(1.0, 2.0))


def test_get_known_periods_empty() -> None:
    storage = data_storage.InMemoryStorage()
    assert list(storage.get_known_periods()) == []


def test_get_known_periods_after_put() -> None:
    storage = data_storage.InMemoryStorage()
    p = period("2020")
    storage.put(arr(1.0), p)
    assert p in storage.get_known_periods()


def test_delete_specific_period() -> None:
    storage = data_storage.InMemoryStorage()
    storage.put(arr(1.0), period("2020"))
    storage.delete(period("2020"))
    assert storage.get(period("2020")) is None


def test_delete_all() -> None:
    storage = data_storage.InMemoryStorage()
    storage.put(arr(1.0), period("2020"))
    storage.put(arr(2.0), period("2021"))
    storage.delete()
    assert storage.get(period("2020")) is None
    assert storage.get(period("2021")) is None


def test_delete_year_removes_contained_months() -> None:
    storage = data_storage.InMemoryStorage()
    p_month = period("2020-03")
    storage.put(arr(1.0), p_month)
    storage.delete(period("2020"))
    assert storage.get(p_month) is None


def test_delete_year_keeps_other_year() -> None:
    storage = data_storage.InMemoryStorage()
    storage.put(arr(1.0), period("2020"))
    storage.put(arr(2.0), period("2021"))
    storage.delete(period("2020"))
    numpy.testing.assert_array_equal(storage.get(period("2021")), arr(2.0))


def test_is_eternal_stores_under_eternity_key() -> None:
    storage = data_storage.InMemoryStorage(is_eternal=True)
    storage.put(arr(1.0), period("2020"))
    numpy.testing.assert_array_equal(storage.get(period("2021")), arr(1.0))


def test_get_memory_usage_empty() -> None:
    storage = data_storage.InMemoryStorage()
    usage = storage.get_memory_usage()
    assert usage["nb_arrays"] == 0
    assert usage["total_nb_bytes"] == 0


def test_get_memory_usage_after_put() -> None:
    storage = data_storage.InMemoryStorage()
    storage.put(arr(1.0, 2.0), period("2020"))
    usage = storage.get_memory_usage()
    assert usage["nb_arrays"] == 1
    assert usage["total_nb_bytes"] > 0


def test_overwrite_period_replaces_value() -> None:
    storage = data_storage.InMemoryStorage()
    storage.put(arr(1.0), period("2020"))
    storage.put(arr(9.0), period("2020"))
    numpy.testing.assert_array_equal(storage.get(period("2020")), arr(9.0))
