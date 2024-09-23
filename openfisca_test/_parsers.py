from typing import NoReturn, Union
from typing_extensions import TypeAlias

import datetime
import functools

import numpy
import pendulum

from openfisca_core import indexed_enums as enum
from openfisca_core import periods, tools

from . import types as t

ReturnType: TypeAlias = Union[
    NoReturn,
    enum.EnumArray,
    t.Array[t.ArrayDate],
    t.Array[t.ArrayBool],
    t.Array[t.ArrayInt],
    t.Array[t.ArrayFloat],
    t.Array[t.ArrayBytes],
]


class _ListEnum(list[enum.Enum]):
    ...


class _ListDate(list[datetime.date]):
    ...


class _ListBool(list[bool]):
    ...


class _ListInt(list[int]):
    ...


class _ListFloat(list[float]):
    ...


class _ListStr(list[str]):
    ...


@functools.singledispatch
def parse(__: object) -> ReturnType:
    """Parse a value to a numpy array.

    Args:
        __: Value to parse.

    Returns:
        Parsed value.

    Examples:
        >>> from openfisca_core import indexed_enums as enum, periods

        >>> class TestEnum(enum.Enum):
        ...     tenant = "tenant"
        ...     owner = "owner"

        >>> period = periods.period(2024)
        >>> instant = period.start
        >>> date = instant.date

        >>> parse(TestEnum)
        EnumArray([<TestEnum.tenant: 'tenant'> <TestEnum.owner: 'owner'>])

        >>> parse(TestEnum.tenant)
        EnumArray([<TestEnum.tenant: 'tenant'>])

        >>> parse(period)
        Traceback (most recent call last):
        NotImplementedError

        >>> parse(instant)
        array(['2024-01-01'], dtype='datetime64[D]')

        >>> parse(date)
        array(['2024-01-01'], dtype='datetime64[D]')

        >>> parse(True)
        array([ True])

        >>> parse(1)
        array([1], dtype=int32)

        >>> parse(1.0)
        array([1.], dtype=float32)

        >>> parse("TestEnum")
        array([b'TestEnum'], dtype='|S8')

        >>> parse("2024-01-01")
        Traceback (most recent call last):
        SyntaxError: leading zeros in decimal integer literals are not permi...

        >>> parse("True")
        array([ True])

        >>> parse("1")
        array([1], dtype=int32)

        >>> parse("1.0")
        array([1.], dtype=float32)

        >>> parse("parent")
        array([b'parent'], dtype='|S6')

    """

    if isinstance(__, numpy.ndarray) and __.ndim == 0:
        return parse(__.item())
    if isinstance(__, numpy.ndarray):
        if numpy.issubdtype(__.dtype, numpy.bool_):
            return __.astype(t.ArrayBool)
        if numpy.issubdtype(__.dtype, numpy.int_):
            return __.astype(t.ArrayInt)
        if numpy.issubdtype(__.dtype, numpy.float_):
            return __.astype(t.ArrayInt)
        for el in __:
            if isinstance(el, numpy.ndarray):
                return parse(el)
    if isinstance(__, (list, tuple, numpy.ndarray)):
        if isinstance(__[0], enum.Enum.__class__):
            return parse(_ListEnum(el for el in __[0]))
        if isinstance(__[0], enum.Enum):
            return parse(_ListEnum(__))
        if isinstance(__[0], periods.Instant):
            return parse(_ListDate(el.date for el in __))
        if isinstance(__[0], datetime.date):
            return parse(_ListDate(__))
        if isinstance(__[0], pendulum.Date):
            return parse(_ListDate(__))
        if isinstance(__[0], bool):
            return parse(_ListBool(__))
        if isinstance(__[0], int):
            return parse(_ListInt(__))
        if isinstance(__[0], float):
            return parse(_ListFloat(__))
        if all(isinstance(el, str) for el in __):
            return parse(_ListStr(__))
    raise NotImplementedError


@parse.register
def _(__: enum.Enum.__class__) -> ReturnType:
    return parse(_ListEnum([el for el in __]))


@parse.register
def _(__: enum.Enum) -> ReturnType:
    return parse(_ListEnum([__]))


@parse.register
def _(__: periods.Instant) -> ReturnType:
    return parse(_ListDate([__.date]))


@parse.register
def _(__: datetime.date) -> ReturnType:
    return parse(_ListDate([__]))


@parse.register
def _(__: pendulum.Date) -> ReturnType:
    return parse(_ListDate([__]))


@parse.register
def _(__: bool) -> ReturnType:
    return parse(_ListBool([__]))


@parse.register
def _(__: int) -> ReturnType:
    return parse(_ListInt([__]))


@parse.register
def _(__: float) -> ReturnType:
    return parse(_ListFloat([__]))


@parse.register
def _(__: str) -> ReturnType:
    return parse(_ListStr([__]))


@parse.register
def _(__: _ListEnum) -> enum.EnumArray:
    index = [el.index for el in __]
    array = numpy.array(index, dtype=t.ArrayEnum)
    return enum.EnumArray(array, __[0].__class__)


@parse.register
def _(__: _ListDate) -> t.Array[t.ArrayDate]:
    return numpy.array(__, dtype=t.ArrayDate)


@parse.register
def _(__: _ListBool) -> t.Array[t.ArrayBool]:
    return numpy.array(__, dtype=t.ArrayBool)


@parse.register
def _(__: _ListInt) -> t.Array[t.ArrayInt]:
    return numpy.array(__, dtype=t.ArrayInt)


@parse.register
def _(__: _ListFloat) -> t.Array[t.ArrayFloat]:
    return numpy.array(__, dtype=t.ArrayFloat)


@parse.register
def _(
    __: _ListStr,
) -> Union[
    t.Array[t.ArrayBool],
    t.Array[t.ArrayInt],
    t.Array[t.ArrayFloat],
    t.Array[t.ArrayBytes],
]:
    if len(__) == 1:
        scalar = tools.eval_expression(__[0])
        if isinstance(scalar, str):
            return numpy.array([scalar], dtype=t.ArrayBytes)
        value = scalar.item()
        if isinstance(value, bool):
            return numpy.array([value], dtype=t.ArrayBool)
        if isinstance(value, int):
            return numpy.array([value], dtype=t.ArrayInt)
        return numpy.array([value], dtype=t.ArrayFloat)
    return numpy.array(__, dtype=t.ArrayBytes)


__all__ = ["parse"]
