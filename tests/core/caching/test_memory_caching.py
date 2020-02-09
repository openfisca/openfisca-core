import functools

import numpy

from openfisca_core import caching
from openfisca_core import periods

import pytest


@pytest.fixture
def storage():
    return caching.MemoryCaching


@pytest.fixture
def eternal_storage(storage):
    return functools.partial(storage, is_eternal = True)


@pytest.fixture
def period():
    return periods.period("2020")


@pytest.fixture
def value():
    return numpy.array([1])


def test___init__(storage):
    result = storage()

    assert result


def test___init__when_is_eternal(eternal_storage):
    result = eternal_storage()

    assert result.is_eternal


def test_put(storage, period, value):
    storage = storage()
    storage.put(value, period)

    result = storage.get(period)

    assert result == value


def test_put_when_is_eternal(eternal_storage, value):
    storage = eternal_storage()
    storage.put(value, "foo")

    result = storage.get("bar")

    assert result == value


def test_delete(storage, period, value):
    storage = storage()
    storage.put(value, period)
    storage.put(value, period.last_year)
    storage.delete(period)

    result = storage.get(period), storage.get(period.last_year)

    assert result == (None, value)


def test_delete_when_period_is_not_specified(storage, period, value):
    storage = storage()
    storage.put(value, period)
    storage.put(value, period.last_year)
    storage.delete()

    result = storage.get(period)

    assert not result


def test_delete_when_is_eternal(eternal_storage, value):
    storage = eternal_storage()
    storage.put(value, "qwerty")
    storage.put(value, "azerty")
    storage.delete("asdf1234")

    result = storage.get("qwerty"), storage.get("azerty")

    assert result == (None, None)


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
