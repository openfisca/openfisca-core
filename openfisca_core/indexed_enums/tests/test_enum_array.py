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


# Benchmarking


@pytest.mark.benchmark(group="EnumArray.__eq__")
def test_benchmark_enum_array_eq(benchmark):
    """Benchmark the `EnumArray.__eq__` method."""
    array_1 = numpy.random.choice(list(Fruit), size=50000)
    array_2 = numpy.random.choice(list(Fruit), size=50000)
    enum_array_1 = Fruit.encode(array_1)
    enum_array_2 = Fruit.encode(array_2)

    def test():
        enum_array_1 == enum_array_2
        enum_array_1 != enum_array_2

    benchmark.pedantic(test, iterations=100, rounds=100)


@pytest.mark.benchmark(group="EnumArray.decode")
def test_benchmark_enum_array_decode(benchmark):
    """Benchmark the `EnumArray.decode` method."""
    array = numpy.random.choice(list(Fruit), size=50000)
    enum_array = Fruit.encode(array)

    def test():
        enum_array.decode()

    benchmark.pedantic(test, iterations=100, rounds=100)


@pytest.mark.benchmark(group="EnumArray.decode_to_str")
def test_benchmark_enum_array_decode_to_str(benchmark):
    """Benchmark the `EnumArray.decode_to_str` method."""
    array = numpy.random.choice(list(Fruit), size=50000)
    enum_array = Fruit.encode(array)

    def test():
        enum_array.decode_to_str()

    benchmark.pedantic(test, iterations=100, rounds=100)
