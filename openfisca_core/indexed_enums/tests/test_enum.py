import numpy
import pytest

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
    array = numpy.array([Animal.DOG])
    enum_array = Animal.encode(array)
    assert enum_array == Animal.DOG


def test_enum_encode_with_enum_sequence():
    """Does encode when called with an enum sequence."""
    sequence = list(Animal) + list(Colour)
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
    array = numpy.array([1])
    enum_array = Animal.encode(array)
    assert enum_array == Animal.DOG


def test_enum_encode_with_int_sequence():
    """Does encode when called with an int sequence."""
    sequence = (1, 2)
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
    enum_array = Animal.encode(array)
    assert len(enum_array) == 0


# Arrays of strings


def test_enum_encode_with_array_of_string():
    """Does encode when called with an array of string."""
    array = numpy.array(["DOG"])
    enum_array = Animal.encode(array)
    assert enum_array == Animal.DOG


def test_enum_encode_with_str_sequence():
    """Does encode when called with a str sequence."""
    sequence = ("DOG", "JAIBA")
    enum_array = Animal.encode(sequence)
    assert Animal.DOG in enum_array


def test_enum_encode_with_str_scalar_array():
    """Does not encode when called with a str scalar array."""
    array = numpy.array("DOG")
    with pytest.raises(TypeError):
        Animal.encode(array)


def test_enum_encode_with_str_with_bad_value():
    """Does not encode when called with a value not in an Enum."""
    array = numpy.array(["JAIBA"])
    enum_array = Animal.encode(array)
    assert len(enum_array) == 0


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
    enum_array = Animal.encode(sequence)
    assert len(enum_array) == 0
