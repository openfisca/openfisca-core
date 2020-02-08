import functools

import numpy

from openfisca_core import data_storage
from openfisca_core import periods

import pytest


@pytest.fixture
def storage():
    return functools.partial(data_storage.OnDiskStorage, storage_dir = "/tmp")


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


def test__init__when_preserve_storage_dir(storage):
    result = storage(preserve_storage_dir = True)

    assert result.preserve_storage_dir


def test_get(storage, value, period):
    storage = storage()
    storage.put(value, period)

    result = storage.get(period)

    assert result == value
