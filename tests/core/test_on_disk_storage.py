import os
import shutil
import tempfile

import numpy as np
import pytest

from openfisca_core import periods
from openfisca_core.data_storage import OnDiskStorage, OnDiskStorageZarr


@pytest.fixture(params=[OnDiskStorage, OnDiskStorageZarr])
def storage_class(request):
    return request.param


@pytest.fixture
def storage(storage_class):
    # Use a temporary directory for tests
    temp_dir = tempfile.mkdtemp()
    storage_instance = storage_class(temp_dir)
    yield storage_instance
    # Cleanup after test ends
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_put_and_get(storage):
    array = np.array([1, 2, 3])
    period = periods.Period(("year", periods.Instant((2017, 1, 1)), 1))

    storage.put(array, period)
    retrieved = storage.get(period)

    assert retrieved is not None
    assert np.array_equal(retrieved, array)


def test_delete(storage):
    array = np.array([1, 2, 3])
    period = periods.Period(("year", periods.Instant((2017, 1, 1)), 1))

    storage.put(array, period)
    storage.delete(period)

    retrieved = storage.get(period)
    assert retrieved is None


def test_get_known_periods(storage):
    array = np.array([1, 2, 3])
    period = periods.Period(("year", periods.Instant((2017, 1, 1)), 1))

    storage.put(array, period)
    periods_list = list(storage.get_known_periods())

    assert len(periods_list) == 1
    assert periods_list[0] == period


def test_restore(storage, storage_class):
    array = np.array([1, 2, 3])
    period = periods.Period(("year", periods.Instant((2017, 1, 1)), 1))

    storage.put(array, period)

    # Create a new storage object pointing to the same directory
    storage2 = storage_class(storage.storage_dir)
    assert storage2.get(period) is None  # Not restored yet

    storage2.restore()
    retrieved = storage2.get(period)

    assert retrieved is not None
    assert np.array_equal(retrieved, array)


def test_delete_all(storage):
    period1 = periods.Period(("year", periods.Instant((2017, 1, 1)), 1))
    period2 = periods.Period(("year", periods.Instant((2018, 1, 1)), 1))

    storage.put(np.array([1]), period1)
    storage.put(np.array([2]), period2)

    storage.delete()

    assert storage.get(period1) is None
    assert storage.get(period2) is None
    assert len(storage.get_known_periods()) == 0
