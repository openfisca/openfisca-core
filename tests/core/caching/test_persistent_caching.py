import functools

import numpy

from openfisca_core import caching
from openfisca_core import periods

import pytest


@pytest.fixture
def storage():
    return functools.partial(caching.PersistentCaching, storage_dir = "/tmp")


@pytest.fixture
def period():
    return periods.period("2020")


@pytest.fixture
def value():
    return numpy.array([1])


@pytest.fixture
def file(storage, period):
    return f"{storage().storage_dir}/{period}.npy"


def test___init__(storage):
    result = storage()

    assert result


def test__init__when_preserve_storage_dir(storage):
    result = storage(preserve_storage_dir = True)

    assert result.preserve_storage_dir


def test_get(storage, period, file, mocker):
    storage = storage()
    files = {period: file}
    mocker.patch.dict(storage._files, files)
    mocker.patch.object(storage, "_decode_file", autospec = True)
    storage.get(period)

    result = files.get(period)

    storage._decode_file.assert_called_once_with(result)


def test_get_when_cache_is_empty(storage, period):
    storage = storage()

    result = storage.get(period)

    assert not result


def test_put(storage, period, value, file, mocker):
    storage = storage()
    mocker.patch("numpy.save")
    storage.put(value, period)

    result = file, value

    numpy.save.assert_called_once_with(*result)


def test_delete(storage, period, file, mocker):
    storage = storage()
    files = {period: file, period.last_year: file}
    mocker.patch.dict(storage._files, files)
    mocker.patch.object(storage, "_pop", autospec = True)
    storage.delete(period)

    result = period, list(files.items())

    storage._pop.assert_called_once_with(*result)


def test_delete_when_period_is_not_specified(storage, period, file, mocker):
    storage = storage()
    files = {period: file, period.last_year: file}
    mocker.patch.dict(storage._files, files)
    storage.delete()

    result = storage.get(period), storage.get(period.last_year)

    assert result == (None, None)


def test_known_periods(storage, period, file, mocker):
    storage = storage()
    files = {period: file}
    mocker.patch.dict(storage._files, files)

    result = storage.known_periods()

    assert result == [period]


def test_memory_usage(storage, period, file, value, mocker):
    storage = storage()
    files = {period: file, period.last_year: file}
    mocker.patch.dict(storage._files, files)
    mocker.patch("os.path.getsize", return_value = 8)
    mocker.patch.object(storage, "_decode_file", return_value = value)

    result = storage.memory_usage()

    assert result == {
        "nb_files": 2,
        "total_nb_bytes": 16,
        "cell_size": 8,
        }
