from openfisca_core import data_storage

import pytest


@pytest.fixture
def storage():
    return data_storage.InMemoryStorage()


@pytest.fixture
def eternal_storage():
    return data_storage.InMemoryStorage(is_eternal = True)


def test___init__(storage):
    result = storage

    assert result


def test___init__when_is_eternal(eternal_storage):
    result = eternal_storage

    assert result.is_eternal
