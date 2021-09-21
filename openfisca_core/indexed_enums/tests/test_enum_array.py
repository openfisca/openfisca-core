import numpy
import pytest

from openfisca_core.indexed_enums import EnumArray, Enum


class MyEnum(Enum):
    """An enum…"""

    FOO = b"foo"
    BAR = b"bar"


@pytest.fixture
def enum_array():
    """An enum array…"""

    return EnumArray([numpy.array(1)], MyEnum)


def test_enum_array_eq_operation(enum_array):
    """The equality operation is permitted."""

    assert enum_array == EnumArray([numpy.array(1)], MyEnum)


def test_enum_array_ne_operation(enum_array):
    """The non-equality operation is permitted."""

    assert enum_array != EnumArray([numpy.array(0)], MyEnum)


def test_enum_array_any_other_operation(enum_array):
    """Only equality and non-equality operations are permitted."""

    with pytest.raises(TypeError, match = "Forbidden operation."):
        enum_array * 1
