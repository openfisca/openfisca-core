import numpy

from openfisca_core import caching
from openfisca_core import periods

import pytest


@pytest.fixture
def storage():
    return caching.MemoryCaching


@pytest.fixture
def period():
    return periods.period("2020")


@pytest.fixture
def value():
    return numpy.array([1])


def test___init__(storage):
    result = storage()

    assert result


def test_put(storage, period, value):
    storage = storage()
    storage.put(value, period)

    result = storage.get(period)

    assert result == value


def test_delete(storage, period, value):
    storage = storage()
    storage.put(value, period)
    storage.put(value, period.last_year)
    storage.delete(period)

    result = storage.get(period), storage.get(period.last_year)

    assert result == (None, value)


def test_delete_all(storage, period, value):
    storage = storage()
    storage.put(value, period)
    storage.put(value, period.last_year)
    storage.delete_all()

    result = storage.get(period)

    assert not result


def test_known_periods(storage, period, value):
    storage = storage()
    storage.put(value, period)

    result = storage.known_periods()

    assert result == [period]


def test_memory_usage(storage, period, value):
    storage = storage()
    storage.put(value, period)

    result = storage.memory_usage()

    assert result == {
        "nb_arrays": 1,
        "total_nb_bytes": 8,
        "cell_size": 8,
        }
