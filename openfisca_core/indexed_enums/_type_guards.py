from __future__ import annotations

from typing_extensions import TypeIs

import numpy

from . import types as t


def _is_int_array(array: t.AnyArray) -> TypeIs[t.IndexArray | t.IntArray]:
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
    return numpy.issubdtype(array.dtype, numpy.integer)


def _is_str_array(array: t.AnyArray) -> TypeIs[t.StrArray]:
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
    return numpy.issubdtype(array.dtype, str)


__all__ = ["_is_int_array", "_is_str_array"]
