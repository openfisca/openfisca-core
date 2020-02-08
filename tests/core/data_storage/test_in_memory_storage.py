import functools

import numpy

from openfisca_core import data_storage
from openfisca_core import periods

import pytest


@pytest.fixture
def storage():
    return data_storage.InMemoryStorage


@pytest.fixture
def eternal_storage(storage):
    return functools.partial(storage, is_eternal = True)


@pytest.fixture
def value():
    return numpy.array([1])


@pytest.fixture
def period():
    return periods.Instant((2020, 1, 1))


def test___init__(storage):
    result = storage()

    assert result


def test___init__when_is_eternal(eternal_storage):
    result = eternal_storage()

    assert result.is_eternal


def test_get(storage, value, period):
    storage = storage()
    storage.put(value, period)

    result = storage.get(period)

    assert result == value


def test_get_when_is_eternal(eternal_storage, value):
    storage = eternal_storage()
    storage.put(value, "foo")

    result = storage.get("bar")

    assert result == value
