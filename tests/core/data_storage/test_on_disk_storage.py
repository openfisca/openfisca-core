import functools

from openfisca_core import data_storage

import pytest


@pytest.fixture
def storage():
    return functools.partial(data_storage.OnDiskStorage, storage_dir = "/tmp")


@pytest.fixture
def eternal_storage(storage):
    return functools.partial(storage, is_eternal = True)


def test___init__(storage):
    result = storage()

    assert result


def test___init__when_is_eternal(eternal_storage):
    result = eternal_storage()

    assert result.is_eternal


def test__init__when_preserve_storage_dir(storage):
    result = storage(preserve_storage_dir = True)

    assert result.preserve_storage_dir
