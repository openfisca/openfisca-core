from __future__ import annotations

import numpy
import pytest

from openfisca_core import data_storage, indexed_enums, periods, types as t


def period(s: str) -> t.Period:
    return periods.period(s)


def arr(*values: float) -> t.VarArray:
    return numpy.array(values, dtype=numpy.float32)


class Housing(indexed_enums.Enum):
    OWNER = "Owner"
    TENANT = "Tenant"


def test_get_unknown_period_returns_none(tmp_path: pytest.TempPathFactory) -> None:
    storage = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    assert storage.get(period("2020")) is None


def test_put_and_get_returns_value(tmp_path: pytest.TempPathFactory) -> None:
    storage = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    storage.put(arr(1.0, 2.0), period("2020"))
    numpy.testing.assert_array_equal(storage.get(period("2020")), arr(1.0, 2.0))


def test_get_known_periods_empty(tmp_path: pytest.TempPathFactory) -> None:
    storage = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    assert list(storage.get_known_periods()) == []


def test_get_known_periods_after_put(tmp_path: pytest.TempPathFactory) -> None:
    storage = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    p = period("2020")
    storage.put(arr(1.0), p)
    assert p in storage.get_known_periods()


def test_delete_specific_period(tmp_path: pytest.TempPathFactory) -> None:
    storage = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    storage.put(arr(1.0), period("2020"))
    storage.delete(period("2020"))
    assert storage.get(period("2020")) is None


def test_delete_all(tmp_path: pytest.TempPathFactory) -> None:
    storage = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    storage.put(arr(1.0), period("2020"))
    storage.put(arr(2.0), period("2021"))
    storage.delete()
    assert storage.get(period("2020")) is None
    assert storage.get(period("2021")) is None


def test_delete_year_removes_contained_months(tmp_path: pytest.TempPathFactory) -> None:
    storage = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    p_month = period("2020-03")
    storage.put(arr(1.0), p_month)
    storage.delete(period("2020"))
    assert storage.get(p_month) is None


def test_is_eternal_stores_under_eternity_key(tmp_path: pytest.TempPathFactory) -> None:
    storage = data_storage.OnDiskStorage(
        str(tmp_path), is_eternal=True, preserve_storage_dir=True
    )
    storage.put(arr(1.0), period("2020"))
    numpy.testing.assert_array_equal(storage.get(period("2021")), arr(1.0))


def test_overwrite_period_replaces_value(tmp_path: pytest.TempPathFactory) -> None:
    storage = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    storage.put(arr(1.0), period("2020"))
    storage.put(arr(9.0), period("2020"))
    numpy.testing.assert_array_equal(storage.get(period("2020")), arr(9.0))


def test_restore_reloads_files(tmp_path: pytest.TempPathFactory) -> None:
    p = period("2020")
    storage1 = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    storage1.put(arr(1.0, 2.0), p)
    storage2 = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    assert storage2.get(p) is None
    storage2.restore()
    numpy.testing.assert_array_equal(storage2.get(p), arr(1.0, 2.0))


def test_enum_array_round_trip(tmp_path: pytest.TempPathFactory) -> None:
    storage = data_storage.OnDiskStorage(str(tmp_path), preserve_storage_dir=True)
    p = period("2020")
    value = indexed_enums.EnumArray(numpy.array([1], dtype=numpy.int32), Housing)
    storage.put(value, p)
    result = storage.get(p)
    assert isinstance(result, indexed_enums.EnumArray)
    assert result.possible_values is Housing
