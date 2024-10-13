from __future__ import annotations

from typing import Final
from typing_extensions import TypeIs

import numpy

from . import types as t

#: Types for int arrays.
ints: Final = {
    numpy.uint8,
    numpy.uint16,
    numpy.uint32,
    numpy.uint64,
    numpy.int8,
    numpy.int16,
    numpy.int32,
    numpy.int64,
}

#: Types for object arrays.
objs: Final = {numpy.object_}

#: Types for str arrays.
strs: Final = {numpy.str_}


def _is_enum_array(array: t.VarArray) -> TypeIs[t.ObjArray]:
    """Narrow the type of a given array to an array of :obj:`numpy.object_`.

    Args:
        array: Array to check.

    Returns:
        bool: True if ``array`` is an array of :obj:`numpy.object_`, False otherwise.

    Examples:
        >>> import numpy

        >>> from openfisca_core import indexed_enums as enum

        >>> Enum = enum.Enum("Enum", ["A", "B"])
        >>> array = numpy.array([Enum.A], dtype=numpy.object_)
        >>> _is_enum_array(array)
        True

        >>> array = numpy.array([1.0])
        >>> _is_enum_array(array)
        False

    """
    return array.dtype.type in objs


def _is_enum_array_like(
    array: t.VarArray | t.ArrayLike[object],
) -> TypeIs[t.ArrayLike[t.Enum]]:
    """Narrow the type of a given array-like to an sequence of :class:`.Enum`.

    Args:
        array: Array to check.

    Returns:
        bool: True if ``array`` is an array-like of :class:`.Enum`, False otherwise.

    Examples:
        >>> from openfisca_core import indexed_enums as enum

        >>> class Housing(enum.Enum):
        ...     OWNER = "owner"
        ...     TENANT = "tenant"

        >>> array = [Housing.OWNER]
        >>> _is_enum_array_like(array)
        True

        >>> array = ["owner"]
        >>> _is_enum_array_like(array)
        False

    """
    return all(isinstance(item, t.Enum) for item in array)


def _is_int_array(array: t.VarArray) -> TypeIs[t.IndexArray]:
    """Narrow the type of a given array to an array of :obj:`numpy.integer`.

    Args:
        array: Array to check.

    Returns:
        bool: True if ``array`` is an array of :obj:`numpy.integer`, False otherwise.

    Examples:
        >>> import numpy

        >>> array = numpy.array([1], dtype=numpy.int16)
        >>> _is_int_array(array)
        True

        >>> array = numpy.array([1], dtype=numpy.int32)
        >>> _is_int_array(array)
        True

        >>> array = numpy.array([1.0])
        >>> _is_int_array(array)
        False

    """
    return array.dtype.type in ints


def _is_int_array_like(
    array: t.VarArray | t.ArrayLike[object],
) -> TypeIs[t.ArrayLike[int]]:
    """Narrow the type of a given array-like to a sequence of :obj:`int`.

    Args:
        array: Array to check.

    Returns:
        bool: True if ``array`` is an array-like of :obj:`int`, False otherwise.

    Examples:
        >>> array = [1]
        >>> _is_int_array_like(array)
        True

        >>> array = (1, 2)
        >>> _is_int_array_like(array)
        True

        >>> array = [1.0]
        >>> _is_int_array_like(array)
        False

    """
    return all(isinstance(item, int) for item in array)


def _is_str_array(array: t.VarArray) -> TypeIs[t.StrArray]:
    """Narrow the type of a given array to an array of :obj:`numpy.str_`.

    Args:
        array: Array to check.

    Returns:
        bool: True if ``array`` is an array of :obj:`numpy.str_`, False otherwise.

    Examples:
        >>> import numpy

        >>> from openfisca_core import indexed_enums as enum

        >>> class Housing(enum.Enum):
        ...     OWNER = "owner"
        ...     TENANT = "tenant"

        >>> array = numpy.array([Housing.OWNER])
        >>> _is_str_array(array)
        False

        >>> array = numpy.array(["owner"])
        >>> _is_str_array(array)
        True

    """
    return array.dtype.type in strs


def _is_str_array_like(
    array: t.VarArray | t.ArrayLike[object],
) -> TypeIs[t.ArrayLike[str]]:
    """Narrow the type of a given array-like to an sequence of :obj:`str`.

    Args:
        array: Array to check.

    Returns:
        bool: True if ``array`` is an array-like of :obj:`str`, False otherwise.

    Examples:
        >>> from openfisca_core import indexed_enums as enum

        >>> class Housing(enum.Enum):
        ...     OWNER = "owner"
        ...     TENANT = "tenant"

        >>> array = [Housing.OWNER]
        >>> _is_str_array_like(array)
        False

        >>> array = ["owner"]
        >>> _is_str_array_like(array)
        True

    """
    return all(isinstance(item, str) for item in array)


__all__ = [
    "_is_enum_array",
    "_is_enum_array_like",
    "_is_int_array",
    "_is_int_array_like",
    "_is_str_array",
    "_is_str_array_like",
]
