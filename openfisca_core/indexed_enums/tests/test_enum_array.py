import numpy
import pytest

from openfisca_core import indexed_enums as enum


class Fruit(enum.Enum):
    APPLE = b"apple"
    BERRY = b"berry"


@pytest.fixture
def enum_array():
    return enum.EnumArray(numpy.array([1]), Fruit)


def test_enum_array_eq_operation(enum_array):
    """The equality operation is permitted."""
    assert enum_array == enum.EnumArray(numpy.array([1]), Fruit)


def test_enum_array_ne_operation(enum_array):
    """The non-equality operation is permitted."""
    assert enum_array != enum.EnumArray(numpy.array([0]), Fruit)


def test_enum_array_any_other_operation(enum_array):
    """Only equality and non-equality operations are permitted."""
    with pytest.raises(TypeError, match="Forbidden operation."):
        enum_array * 1
