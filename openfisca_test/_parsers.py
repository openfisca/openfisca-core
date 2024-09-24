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
    t.Array[t.ArrayStr],
]


class _ListEnumArray(tuple[enum.EnumArray, ...]):
    ...


class _ListEnum(tuple[enum.Enum, ...]):
    ...


class _ListDate(tuple[datetime.date, ...]):
    ...


class _ListBool(tuple[bool, ...]):
    ...


class _ListInt(tuple[int, ...]):
    ...


class _ListFloat(tuple[float, ...]):
    ...


class _ListBytes(tuple[bytes, ...]):
    ...


class _ListStr(tuple[str, ...]):
    ...


@functools.singledispatch
def parse(__: object) -> ReturnType:
    """Parse a value to a numpy array.

    Args:
        __: Value to parse.

    Returns:
        Parsed value.

    Raises:
        NotImplementedError: If the value is not supported.

    Examples:
        >>> from openfisca_core import indexed_enums as enum, periods

        >>> class TestEnum(enum.Enum):
        ...     tenant = "tenant"
        ...     owner = "owner"

        >>> period = periods.period(2024)
        >>> instant = period.start
        >>> date = instant.date

        >>> parse(parse(TestEnum))
        array(['tenant', 'owner'], dtype='<U6')

        >>> parse(TestEnum)
        array(['tenant', 'owner'], dtype='<U6')

        >>> parse(TestEnum.tenant)
        array(['tenant'], dtype='<U6')

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

        >>> parse(b"TestEnum")
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
        array(['parent'], dtype='<U6')

    """

    if isinstance(__, numpy.ndarray) and __.ndim == 0:
        return parse(__.item())
    if isinstance(__, numpy.ndarray):
        if numpy.issubdtype(__.dtype, numpy.bool_):
            return __.astype(t.ArrayBool)
        if numpy.issubdtype(__.dtype, numpy.int_):
            return __.astype(t.ArrayInt)
        if numpy.issubdtype(__.dtype, numpy.int32):
            return __.astype(t.ArrayInt)
        if numpy.issubdtype(__.dtype, numpy.int64):
            return __.astype(t.ArrayInt)
        if numpy.issubdtype(__.dtype, numpy.float_):
            return __.astype(t.ArrayFloat)
        if numpy.issubdtype(__.dtype, numpy.float32):
            return __.astype(t.ArrayFloat)
        if numpy.issubdtype(__.dtype, numpy.float64):
            return __.astype(t.ArrayFloat)
        if numpy.issubdtype(__.dtype, numpy.datetime64):
            return __.astype(t.ArrayDate)
    if isinstance(__, (list, tuple, numpy.ndarray)):
        if isinstance(__[0], enum.EnumArray):
            return parse(_ListEnumArray(el for el in __))
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
        if all(isinstance(el, int) for el in __):
            return parse(_ListInt(__))
        if any(isinstance(el, float) for el in __):
            return parse(_ListFloat(__))
        if all(isinstance(el, bytes) for el in __):
            return parse(_ListBytes(__))
        if all(isinstance(el, str) for el in __):
            return parse(_ListStr(__))
        for el in __:
            if isinstance(el, numpy.ndarray):
                return parse(el)
    raise NotImplementedError


@parse.register
def _(__: enum.EnumArray) -> t.Array[t.ArrayStr]:
    return __.decode_to_str()


@parse.register
def _(__: enum.Enum.__class__) -> t.Array[t.ArrayStr]:
    return numpy.array(tuple(el.name for el in __), dtype=t.ArrayStr)


@parse.register
def _(__: enum.Enum) -> t.Array[t.ArrayStr]:
    return numpy.array((__.name,), dtype=t.ArrayStr)


@parse.register
def _(__: periods.Instant) -> t.Array[t.ArrayDate]:
    return numpy.array((__.date,), dtype=t.ArrayDate)


@parse.register
def _(__: datetime.date) -> t.Array[t.ArrayDate]:
    return numpy.array((__,), dtype=t.ArrayDate)


@parse.register
def _(__: pendulum.Date) -> t.Array[t.ArrayDate]:
    return numpy.array((__,), dtype=t.ArrayDate)


@parse.register
def _(__: bool) -> t.Array[t.ArrayBool]:
    return numpy.array((__,), dtype=t.ArrayBool)


@parse.register
def _(__: int) -> t.Array[t.ArrayInt]:
    return numpy.array((__,), dtype=t.ArrayInt)


@parse.register
def _(__: float) -> t.Array[t.ArrayFloat]:
    return numpy.array((__,), dtype=t.ArrayFloat)


@parse.register
def _(__: bytes) -> t.Array[t.ArrayBytes]:
    return numpy.array((__,), dtype=t.ArrayBytes)


@parse.register
def _(__: str) -> ReturnType:
    scalar = tools.eval_expression(__)
    if isinstance(scalar, str):
        return numpy.array((scalar,), dtype=t.ArrayStr)
    return parse(scalar.item())


@parse.register
def _(__: numpy.bool_) -> t.Array[t.ArrayBool]:
    return numpy.array((__,), dtype=t.ArrayBool)


@parse.register
def _(__: numpy.int_) -> t.Array[t.ArrayInt]:
    return numpy.array((__,), dtype=t.ArrayInt)


@parse.register
def _(__: numpy.int32) -> t.Array[t.ArrayInt]:
    return numpy.array((__,), dtype=t.ArrayInt)


@parse.register
def _(__: numpy.int64) -> t.Array[t.ArrayInt]:
    return numpy.array((__,), dtype=t.ArrayInt)


@parse.register
def _(__: numpy.float_) -> t.Array[t.ArrayFloat]:
    return numpy.array((__,), dtype=t.ArrayFloat)


@parse.register
def _(__: numpy.float32) -> t.Array[t.ArrayFloat]:
    return numpy.array((__,), dtype=t.ArrayFloat)


@parse.register
def _(__: numpy.float64) -> t.Array[t.ArrayFloat]:
    return numpy.array((__,), dtype=t.ArrayFloat)


@parse.register
def _(__: numpy.datetime64) -> t.Array[t.ArrayDate]:
    return numpy.array((__,), dtype=t.ArrayDate)


@parse.register
def _(__: _ListEnumArray) -> ReturnType:
    return numpy.array([parse(el) for el in __], dtype=t.ArrayStr)


@parse.register
def _(__: _ListEnum) -> t.Array[t.ArrayStr]:
    return numpy.array(tuple(el.name for el in __), dtype=t.ArrayStr)


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
def _(__: _ListBytes) -> t.Array[t.ArrayBytes]:
    return numpy.array(__, dtype=t.ArrayBytes)


@parse.register
def _(__: _ListStr) -> ReturnType:
    if len(__) == 1:
        scalar = tools.eval_expression(__[0])
        if isinstance(scalar, str):
            return numpy.array((scalar,), dtype=t.ArrayStr)
        return parse(scalar.item())
    return numpy.array(__, dtype=t.ArrayStr)


__all__ = ["parse"]
