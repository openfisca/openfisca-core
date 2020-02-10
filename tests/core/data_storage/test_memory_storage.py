import numpy

from openfisca_core import periods
from openfisca_core.data_storage import MemoryStorage

import pytest


@pytest.fixture
def storage():
    return MemoryStorage()


@pytest.fixture
def state():
    return {}


@pytest.fixture
def period():
    return periods.period("2020")


@pytest.fixture
def array():
    return numpy.array([1])


def test_put(storage, state, period, array):
    state = storage.put(state, period, array)

    result = storage.get(state, period)

    assert result == array


def test_delete(storage, state, period, array):
    state = storage.put(state, period, array)
    state = storage.put(state, period.last_year, array)
    state = storage.delete(state, period)

    result = storage.get(state, period), storage.get(state, period.last_year)

    assert result == (None, array)


def test_delete_all(storage, state, period, array):
    state = storage.put(state, period, array)
    state = storage.put(state, period.last_year, array)
    state = storage.delete_all(state)

    result = storage.get(state, period), storage.get(state, period.last_year)

    assert result == (None, None)


def test_memory_usage(storage, state, period, array):
    state = storage.put(state, period, array)

    result = storage.memory_usage(state)

    assert result == {
        "nb_arrays": 1,
        "total_nb_bytes": 8,
        "cell_size": 8,
        }


def test_memory_usage_when_cache_is_empty(storage, state, period, array):
    state = storage.delete_all(state)

    result = storage.memory_usage(state)

    assert result == {
        "nb_arrays": 0,
        "total_nb_bytes": 0,
        "cell_size": numpy.nan,
        }
