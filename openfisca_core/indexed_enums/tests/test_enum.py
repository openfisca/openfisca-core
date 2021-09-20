import numpy

from openfisca_core.indexed_enums import Enum


class MyEnum(Enum):
    """An enum…"""

    foo = b"foo"
    bar = b"bar"


# ArrayLike["Enum"]


def test_enum_encode_with_enum_scalar_array():
    """Encodes when called with an enum scalar array."""

    array = numpy.array(MyEnum.bar)
    enum_array = MyEnum.encode(array)
    assert enum_array == MyEnum.bar.index


def test_enum_encode_with_enum_sequence():
    """Does not encode when called with an enum sequence."""

    sequence = list(MyEnum)
    enum_array = MyEnum.encode(sequence)
    assert enum_array[0] != MyEnum.bar.index


def test_enum_encode_with_enum_scalar():
    """Does not encode when called with an enum scalar."""

    scalar = MyEnum.bar
    enum_array = MyEnum.encode(scalar)
    assert enum_array != MyEnum.bar.index


# ArrayLike[bytes]


def test_enum_encode_with_bytes_scalar_array():
    """Encodes when called with a bytes scalar array."""

    array = numpy.array(b"bar")
    enum_array = MyEnum.encode(array)
    assert enum_array == MyEnum.bar.index


def test_enum_encode_with_bytes_sequence():
    """Does not encode when called with a bytes sequence."""

    sequence = bytearray(b"bar")
    enum_array = MyEnum.encode(sequence)
    assert enum_array[0] != MyEnum.bar.index


def test_enum_encode_with_bytes_scalar():
    """Does not encode when called with a bytes scalar."""

    scalar = b"bar"
    enum_array = MyEnum.encode(scalar)
    assert enum_array != MyEnum.bar.index


# ArrayLike[int]


def test_enum_encode_with_int_scalar_array():
    """Does not encode when called with an int scalar array (noop)."""

    array = numpy.array(1)
    enum_array = MyEnum.encode(array)
    assert enum_array == MyEnum.bar.index


def test_enum_encode_with_int_sequence():
    """Does not encode when called with an int sequence (noop)."""

    sequence = range(1, 2)
    enum_array = MyEnum.encode(sequence)
    assert enum_array[0] == MyEnum.bar.index


def test_enum_encode_with_int_scalar():
    """Does not encode when called with an int scalar (noop)."""

    scalar = 1
    enum_array = MyEnum.encode(scalar)
    assert enum_array == MyEnum.bar.index


# ArrayLike[str]


def test_enum_encode_with_str_scalar_array():
    """Encodes when called with a str scalar array."""

    array = numpy.array("bar")
    enum_array = MyEnum.encode(array)
    assert enum_array == MyEnum.bar.index


def test_enum_encode_with_str_sequence():
    """Does not encode when called with a str sequence."""

    sequence = tuple(("bar",))
    enum_array = MyEnum.encode(sequence)
    assert enum_array[0] != MyEnum.bar.index


def test_enum_encode_with_str_scalar():
    """Does not encode when called with a str scalar."""

    scalar = "bar"
    enum_array = MyEnum.encode(scalar)
    assert enum_array != MyEnum.bar.index


# Unsupported encodings


def test_enum_encode_with_any_array():
    """Does not encode when called with unsupported types (noop)."""

    array = numpy.array([{"foo": "bar"}])
    enum_array = MyEnum.encode(array)
    assert enum_array[0] == {"foo": "bar"}


def test_enum_encode_with_any_scalar_array():
    """Does not encode when called with unsupported types (noop)."""

    array = numpy.array(1.5)
    enum_array = MyEnum.encode(array)
    assert enum_array == 1.5


def test_enum_encode_with_any_sequence():
    """Does not encode when called with unsupported types (noop)."""

    sequence = memoryview(b"bar")
    enum_array = MyEnum.encode(sequence)
    assert enum_array[0] == sequence[0]


def test_enum_encode_with_anything():
    """Does not encode when called with unsupported types (noop)."""

    anything = {object()}
    enum_array = MyEnum.encode(anything)
    assert enum_array == anything
