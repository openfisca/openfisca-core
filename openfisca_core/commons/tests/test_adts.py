import pytest

from openfisca_core import commons


@pytest.fixture
def failure():
    return commons.either.fail("error")


@pytest.fixture
def success():
    return commons.either.succeed(1)


def test_either_is_failure(failure):
    assert failure.is_failure


def test_either_is_success(success):
    assert success.is_success


def test_either_unwrap(failure):
    assert failure.unwrap() == "error"


def test_either_then(failure, success):
    assert failure.then(lambda x: failure).unwrap() == "error"
    assert failure.then(lambda x: success).unwrap() == "error"
    assert success.then(lambda x: failure).unwrap() == "error"
    assert success.then(lambda x: success).unwrap() == 1
    assert success.then(lambda x: commons.either.succeed(x + 1)).unwrap() == 2
