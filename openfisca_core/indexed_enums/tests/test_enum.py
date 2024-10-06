import numpy

from openfisca_core import indexed_enums as enum


class Animal(enum.Enum):
    CAT = b"Cat"
    DOG = b"Dog"


# Arrays of Enum


def test_enum_encode_with_enum_scalar_array():
    """Encode when called with an enum scalar array."""
    array = numpy.array(Animal.DOG)
    enum_array = Animal.encode(array)
    assert enum_array == Animal.DOG.index


def test_enum_encode_with_enum_sequence():
    """Does not encode when called with an enum sequence."""
    sequence = list(Animal)
    enum_array = Animal.encode(sequence)
    assert enum_array[0] != Animal.DOG.index


def test_enum_encode_with_enum_scalar():
    """Does not encode when called with an enum scalar."""
    scalar = Animal.DOG
    enum_array = Animal.encode(scalar)
    assert enum_array != Animal.DOG.index


# Arrays of int


def test_enum_encode_with_int_scalar_array():
    """Does not encode when called with an int scalar array (noop)."""
    array = numpy.array(1)
    enum_array = Animal.encode(array)
    assert enum_array == Animal.DOG.index


def test_enum_encode_with_int_sequence():
    """Does not encode when called with an int sequence (noop)."""
    sequence = range(1, 2)
    enum_array = Animal.encode(sequence)
    assert enum_array[0] == Animal.DOG.index


def test_enum_encode_with_int_scalar():
    """Does not encode when called with an int scalar (noop)."""
    scalar = 1
    enum_array = Animal.encode(scalar)
    assert enum_array == Animal.DOG.index


# Arrays of bytes

def test_enum_encode_with_bytes_scalar_array():
    """Encode when called with a bytes scalar array."""
    array = numpy.array(b"DOG")
    enum_array = Animal.encode(array)
    assert enum_array == Animal.DOG.index


def test_enum_encode_with_bytes_sequence():
    """Does not encode when called with a bytes sequence."""
    sequence = bytearray(b"DOG")
    enum_array = Animal.encode(sequence)
    assert enum_array[0] != Animal.DOG.index


def test_enum_encode_with_bytes_scalar():
    """Does not encode when called with a bytes scalar."""
    scalar = b"DOG"
    enum_array = Animal.encode(scalar)
    assert enum_array != Animal.DOG.index


def test_enum_encode_with_bytes_with_bad_value():
    """Does not encode when called with a value not in an Enum."""
    array = numpy.array([b"IGUANA"])
    enum_array = Animal.encode(array)
    assert enum_array != Animal.CAT.index
    assert enum_array != Animal.DOG.index


# Arrays of strings


def test_enum_encode_with_str_scalar_array():
    """Encode when called with a str scalar array."""
    array = numpy.array("DOG")
    enum_array = Animal.encode(array)
    assert enum_array == Animal.DOG.index


def test_enum_encode_with_str_sequence():
    """Does not encode when called with a str sequence."""
    sequence = ("DOG",)
    enum_array = Animal.encode(sequence)
    assert enum_array[0] != Animal.DOG.index


def test_enum_encode_with_str_scalar():
    """Does not encode when called with a str scalar."""
    scalar = "DOG"
    enum_array = Animal.encode(scalar)
    assert enum_array != Animal.DOG.index


def test_enum_encode_with_str_with_bad_value():
    """Does not encode when called with a value not in an Enum."""
    array = numpy.array(["JAIBA"])
    enum_array = Animal.encode(array)
    assert enum_array != Animal.CAT.index
    assert enum_array != Animal.DOG.index


# Unsupported encodings


def test_enum_encode_with_any_array():
    """Does not encode when called with unsupported types (noop)."""
    value = {"animal": "dog"}
    array = numpy.array([value])
    enum_array = Animal.encode(array)
    assert enum_array[0] == value


def test_enum_encode_with_any_scalar_array():
    """Does not encode when called with unsupported types (noop)."""
    value = 1.5
    array = numpy.array(value)
    enum_array = Animal.encode(array)
    assert enum_array == value


def test_enum_encode_with_any_sequence():
    """Does not encode when called with unsupported types (noop)."""
    sequence = memoryview(b"DOG")
    enum_array = Animal.encode(sequence)
    assert enum_array[0] == sequence[0]


def test_enum_encode_with_anything():
    """Does not encode when called with unsupported types (noop)."""
    anything = {object()}
    enum_array = Animal.encode(anything)
    assert enum_array == anything
