import numpy
import pytest

from openfisca_core.indexed_enums import EnumArray, Enum


class MyEnum(Enum):
    """An enum…"""

    foo = b"foo"
    bar = b"bar"


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


def test_enum_array___repr__(enum_array):
    """Enum arrays have a custom debugging representation."""

    assert repr(enum_array) == "EnumArray([<MyEnum.bar: b'bar'>])"


def test_enum_array___str__(enum_array):
    """Enum arrays have a custom end-user representation."""

    assert str(enum_array) == "['bar']"
