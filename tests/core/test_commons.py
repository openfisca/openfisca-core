import numpy

from openfisca_core import commons

import pytest


def test_dummy():
    with pytest.warns(DeprecationWarning):
        result = commons.Dummy()
        assert result


def test_empty_clone():
    dummy_class = type("Dummmy", (), {})
    dummy = dummy_class()

    result = commons.empty_clone(dummy)

    assert type(result) == dummy_class


def test_stringify_array():
    array = numpy.array([10, 20])

    result = commons.stringify_array(array)

    assert result == "[10, 20]"


def test_stringify_array_when_none():
    array = None

    result = commons.stringify_array(array)

    assert result == "None"
