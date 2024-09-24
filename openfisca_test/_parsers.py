from numpy.typing import NDArray
from typing import Union
from typing_extensions import TypeAlias

import datetime
import functools

import numpy
import pendulum

from openfisca_core import indexed_enums as enum, periods, tools

ReturnType: TypeAlias = Union[
    enum.EnumArray,
    NDArray[numpy.datetime64],
    NDArray[numpy.bool_],
    NDArray[numpy.int32],
    NDArray[numpy.float32],
    NDArray[numpy.bytes_],
    NDArray[numpy.str_],
]


class _ListEnumArray(tuple[enum.EnumArray, ...]): ...


class _ListEnum(tuple[enum.Enum, ...]): ...


class _ListDate(tuple[datetime.date, ...]): ...


class _ListBool(tuple[bool, ...]): ...


class _ListInt(tuple[int, ...]): ...


class _ListFloat(tuple[float, ...]): ...


class _ListBytes(tuple[bytes, ...]): ...


class _ListStr(tuple[str, ...]): ...


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
            return __.astype(numpy.bool_)
        if numpy.issubdtype(__.dtype, numpy.int_):
            return __.astype(numpy.int32)
        if numpy.issubdtype(__.dtype, numpy.int32):
            return __.astype(numpy.int32)
        if numpy.issubdtype(__.dtype, numpy.int64):
            return __.astype(numpy.int32)
        if numpy.issubdtype(__.dtype, numpy.float64):
            return __.astype(numpy.float32)
        if numpy.issubdtype(__.dtype, numpy.float32):
            return __.astype(numpy.float32)
        if numpy.issubdtype(__.dtype, numpy.float64):
            return __.astype(numpy.float32)
        if numpy.issubdtype(__.dtype, numpy.datetime64):
            return __.astype(numpy.datetime64)
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
def _(__: enum.EnumArray) -> NDArray[numpy.str_]:
    return __.decode_to_str()


@parse.register
def _(__: enum.Enum.__class__) -> NDArray[numpy.str_]:
    return numpy.array(tuple(el.name for el in __), dtype=numpy.str_)


@parse.register
def _(__: enum.Enum) -> NDArray[numpy.str_]:
    return numpy.array((__.name,), dtype=numpy.str_)


@parse.register
def _(__: periods.Instant) -> NDArray[numpy.datetime64]:
    return numpy.array((__.date,), dtype=numpy.datetime64)


@parse.register
def _(__: datetime.date) -> NDArray[numpy.datetime64]:
    return numpy.array((__,), dtype=numpy.datetime64)


@parse.register
def _(__: pendulum.Date) -> NDArray[numpy.datetime64]:
    return numpy.array((__,), dtype=numpy.datetime64)


@parse.register
def _(__: bool) -> NDArray[numpy.bool_]:
    return numpy.array((__,), dtype=numpy.bool_)


@parse.register
def _(__: int) -> NDArray[numpy.int32]:
    return numpy.array((__,), dtype=numpy.int32)


@parse.register
def _(__: float) -> NDArray[numpy.float32]:
    return numpy.array((__,), dtype=numpy.float32)


@parse.register
def _(__: bytes) -> NDArray[numpy.bytes_]:
    return numpy.array((__,), dtype=numpy.bytes_)


@parse.register
def _(__: str) -> ReturnType:
    scalar = tools.eval_expression(__)
    if isinstance(scalar, str):
        return numpy.array((scalar,), dtype=numpy.str_)
    return parse(scalar.item())


@parse.register
def _(__: numpy.bool_) -> NDArray[numpy.bool_]:
    return numpy.array((__,), dtype=numpy.bool_)


@parse.register
def _(__: numpy.int_) -> NDArray[numpy.int32]:
    return numpy.array((__,), dtype=numpy.int32)


@parse.register
def _(__: numpy.int32) -> NDArray[numpy.int32]:
    return numpy.array((__,), dtype=numpy.int32)


@parse.register
def _(__: numpy.int64) -> NDArray[numpy.int32]:
    return numpy.array((__,), dtype=numpy.int32)


@parse.register
def _(__: numpy.float64) -> NDArray[numpy.float32]:
    return numpy.array((__,), dtype=numpy.float32)


@parse.register
def _(__: numpy.float32) -> NDArray[numpy.float32]:
    return numpy.array((__,), dtype=numpy.float32)


@parse.register
def _(__: numpy.float64) -> NDArray[numpy.float32]:
    return numpy.array((__,), dtype=numpy.float32)


@parse.register
def _(__: numpy.datetime64) -> NDArray[numpy.datetime64]:
    return numpy.array((__,), dtype=numpy.datetime64)


@parse.register
def _(__: _ListEnumArray) -> ReturnType:
    return numpy.array([parse(el) for el in __], dtype=numpy.str_)


@parse.register
def _(__: _ListEnum) -> NDArray[numpy.str_]:
    return numpy.array(tuple(el.name for el in __), dtype=numpy.str_)


@parse.register
def _(__: _ListDate) -> NDArray[numpy.datetime64]:
    return numpy.array(__, dtype=numpy.datetime64)


@parse.register
def _(__: _ListBool) -> NDArray[numpy.bool_]:
    return numpy.array(__, dtype=numpy.bool_)


@parse.register
def _(__: _ListInt) -> NDArray[numpy.int32]:
    return numpy.array(__, dtype=numpy.int32)


@parse.register
def _(__: _ListFloat) -> NDArray[numpy.float32]:
    return numpy.array(__, dtype=numpy.float32)


@parse.register
def _(__: _ListBytes) -> NDArray[numpy.bytes_]:
    return numpy.array(__, dtype=numpy.bytes_)


@parse.register
def _(__: _ListStr) -> ReturnType:
    if len(__) == 1:
        scalar = tools.eval_expression(__[0])
        if isinstance(scalar, str):
            return numpy.array((scalar,), dtype=numpy.str_)
        return parse(scalar.item())
    return numpy.array(__, dtype=numpy.str_)


__all__ = ["parse"]
