import datetime

import numpy
import pytest

import openfisca_test as test
from openfisca_core import indexed_enums as enum, periods

date = numpy.array(["2024-01-01"], dtype="datetime64[D]")


class TestEnum(enum.Enum):
    tenant = "tenant"
    owner = "owner"


def value(value):
    return value


def sequence(value):
    return [value]


def scalar(value):
    if isinstance(value, enum.EnumArray):
        return numpy.array(value.decode())
    return numpy.array(value)


def array(value):
    if isinstance(value, enum.EnumArray):
        return numpy.array([value.decode()])
    return numpy.array([value])


def enum_array(value):
    return TestEnum.encode(numpy.array(value))


@pytest.mark.parametrize("f", [value, sequence, scalar, array])
@pytest.mark.parametrize(
    "arg, expected",
    [
        (enum_array(["tenant", "owner"]), numpy.array(["tenant", "owner"])),
        (TestEnum, numpy.array(["tenant", "owner"], dtype="<U6")),
        (TestEnum.tenant, numpy.array(["tenant"], dtype="<U6")),
        (periods.Instant((2024, 1, 1)).date, date),
        (datetime.date(2024, 1, 1), date),
        (True, numpy.array([True])),
        (1, numpy.array([1], dtype=numpy.int32)),
        (1.0, numpy.array([1.0], dtype=numpy.float32)),
        ("TestEnum", numpy.array(["TestEnum"], dtype="<U8")),
        ("True", numpy.array([True])),
        ("1", numpy.array([1], dtype=numpy.int32)),
        ("1.0", numpy.array([1.0], dtype=numpy.float32)),
        ("parent", numpy.array(["parent"], dtype="<U6")),
    ],
)
def test_parse(f, arg, expected):
    actual = test.parse(f(arg))
    assert (actual == expected).all()
