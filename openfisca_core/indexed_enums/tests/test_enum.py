import numpy
import pytest
from numpy.testing import assert_array_equal

from openfisca_core import indexed_enums as enum


class Animal(enum.Enum):
    CAT = b"Cat"
    DOG = b"Dog"


class Colour(enum.Enum):
    INCARNADINE = "incarnadine"
    TURQUOISE = "turquoise"
    AMARANTH = "amaranth"


# Arrays of Enum


def test_enum_encode_with_array_of_enum():
    """Does encode when called with an array of enums."""
    array = numpy.array([Animal.DOG, Animal.DOG, Animal.CAT])
    enum_array = Animal.encode(array)
    assert_array_equal(enum_array, numpy.array([1, 1, 0]))


def test_enum_encode_with_enum_sequence():
    """Does encode when called with an enum sequence."""
    sequence = list(Animal)
    enum_array = Animal.encode(sequence)
    assert Animal.DOG in enum_array


def test_enum_encode_with_enum_scalar_array():
    """Does not encode when called with an enum scalar array."""
    array = numpy.array(Animal.DOG)
    with pytest.raises(TypeError):
        Animal.encode(array)


def test_enum_encode_with_enum_with_bad_value():
    """Does not encode when called with a value not in an Enum."""
    array = numpy.array([Colour.AMARANTH])
    with pytest.raises(TypeError):
        Animal.encode(array)


# Arrays of int


def test_enum_encode_with_array_of_int():
    """Does encode when called with an array of int."""
    array = numpy.array([1, 1, 0])
    enum_array = Animal.encode(array)
    assert_array_equal(enum_array, numpy.array([1, 1, 0]))


def test_enum_encode_with_int_sequence():
    """Does encode when called with an int sequence."""
    sequence = (0, 1)
    enum_array = Animal.encode(sequence)
    assert Animal.DOG in enum_array


def test_enum_encode_with_int_scalar_array():
    """Does not encode when called with an int scalar array."""
    array = numpy.array(1)
    with pytest.raises(TypeError):
        Animal.encode(array)


def test_enum_encode_with_int_with_bad_value():
    """Does not encode when called with a value not in an Enum."""
    array = numpy.array([2])
    with pytest.raises(IndexError):
        Animal.encode(array)


# Arrays of strings


def test_enum_encode_with_array_of_string():
    """Does encode when called with an array of string."""
    array = numpy.array(["DOG", "DOG", "CAT"])
    enum_array = Animal.encode(array)
    assert_array_equal(enum_array, numpy.array([1, 1, 0]))


def test_enum_encode_with_str_sequence():
    """Does encode when called with a str sequence."""
    sequence = ("DOG", "CAT")
    enum_array = Animal.encode(sequence)
    assert Animal.DOG in enum_array


def test_enum_encode_with_str_scalar_array():
    """Does not encode when called with a str scalar array."""
    array = numpy.array("DOG")
    with pytest.raises(TypeError):
        Animal.encode(array)


def test_enum_encode_with_str_with_bad_value():
    """Encode encode when called with a value not in an Enum."""
    array = numpy.array(["JAIBA"])
    with pytest.raises(IndexError):
        Animal.encode(array)


# Unsupported encodings


def test_enum_encode_with_any_array():
    """Does not encode when called with unsupported types."""
    value = {"animal": "dog"}
    array = numpy.array([value])
    with pytest.raises(TypeError):
        Animal.encode(array)


def test_enum_encode_with_any_scalar_array():
    """Does not encode when called with unsupported types."""
    value = 1.5
    array = numpy.array(value)
    with pytest.raises(TypeError):
        Animal.encode(array)


def test_enum_encode_with_any_sequence():
    """Does not encode when called with unsupported types."""
    sequence = memoryview(b"DOG")
    with pytest.raises(IndexError):
        Animal.encode(sequence)
