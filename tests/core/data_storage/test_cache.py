import numpy

from openfisca_core import periods
from openfisca_core.data_storage import Cache, DiskStorage

import pytest


@pytest.fixture
def storage():
    return DiskStorage(directory = "/tmp/openfisca", preserve = False)


@pytest.fixture
def cache(storage):
    return Cache(storage = storage)


@pytest.fixture
def period():
    return periods.period("2020")


@pytest.fixture
def eternal_period():
    return periods.period(periods.ETERNITY)


@pytest.fixture
def array():
    return numpy.array([1])


def test_get(cache, storage, period, mocker):
    mocker.patch.object(storage, "get")
    cache.get(period)

    result = {}, period

    storage.get.assert_called_once_with(*result)


def test_get_when_is_eternal(cache, storage, period, eternal_period, mocker):
    """When it is eternal, input periods are actually ignored."""
    mocker.patch.object(storage, "get")
    cache.is_eternal = True
    cache.get(period)

    result = {}, eternal_period

    storage.get.assert_called_once_with(*result)


def test_put(cache, storage, period, array, mocker):
    mocker.patch.object(storage, "put")
    cache.put(array, period)

    result = {}, period, array

    storage.put.assert_called_once_with(*result)


def test_put_when_is_eternal(cache, storage, period, eternal_period, array, mocker):
    """When it is eternal, input periods are actually ignored."""
    mocker.patch.object(storage, "put")
    cache.is_eternal = True
    cache.put(array, period)

    result = {}, eternal_period, array

    storage.put.assert_called_once_with(*result)


def test_delete(cache, storage, period, mocker):
    mocker.patch.object(storage, "delete")
    cache.delete(period)

    result = {}, period

    storage.delete.assert_called_once_with(*result)


def test_delete_when_period_is_not_specified(cache, storage, mocker):
    mocker.patch.object(storage, "delete_all")
    cache.delete()

    result = {}

    storage.delete_all.assert_called_once_with(result)


def test_delete_when_is_eternal(cache, storage, period, eternal_period, mocker):
    """When it is eternal, input periods are actually ignored."""
    mocker.patch.object(storage, "delete")
    cache.is_eternal = True
    cache.delete(period)

    result = {}, eternal_period

    storage.delete.assert_called_once_with(*result)


def test_get_memory_usage(cache, storage, mocker):
    mocker.patch.object(storage, "memory_usage")
    cache.memory_usage()

    result = {}

    storage.memory_usage.assert_called_once_with(result)


def test_known_periods(cache, period, array):
    cache.put(array, period)

    result = cache.known_periods()

    assert period in result
