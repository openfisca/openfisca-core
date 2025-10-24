from __future__ import annotations

import numpy

from . import types as t


def _enum_to_index(value: t.ObjArray | t.ArrayLike[t.Enum]) -> t.IndexArray:
    """Transform an array of enum members into an index array.

    Args:
        value: The enum members array to encode.

    Returns:
        The index array.

    Examples:
        >>> import numpy

        >>> from openfisca_core import indexed_enums as enum

        >>> class Road(enum.Enum):
        ...     STREET = (
        ...         "A public road that connects two points, but also has "
        ...         "buildings on both sides of it; these typically run "
        ...         "perpendicular to avenues."
        ...     )
        ...     AVENUE = (
        ...         "A public way that also has buildings and/or trees on both "
        ...         "sides; these run perpendicular to streets and are "
        ...         "traditionally wider."
        ...     )

        >>> class Rogue(enum.Enum):
        ...     BOULEVARD = "More like a shady impasse, to be honest."

        >>> _enum_to_index(Road.AVENUE)
        Traceback (most recent call last):
        TypeError: 'Road' object is not iterable

        >>> _enum_to_index([Road.AVENUE])
        array([1], dtype=uint8)

        >>> _enum_to_index(numpy.array(Road.AVENUE))
        Traceback (most recent call last):
        TypeError: iteration over a 0-d array

        >>> _enum_to_index(numpy.array([Road.AVENUE]))
        array([1], dtype=uint8)

        >>> value = numpy.array([Road.STREET, Road.AVENUE, Road.STREET])
        >>> _enum_to_index(value)
        array([0, 1, 0], dtype=uint8)

        >>> value = numpy.array([Road.AVENUE, Road.AVENUE, Rogue.BOULEVARD])
        >>> _enum_to_index(value)
        array([1, 1, 0], dtype=uint8)

    """
    return numpy.array([enum.index for enum in value], t.EnumDType)


def _int_to_index(
    enum_class: type[t.Enum], value: t.IndexArray | t.ArrayLike[int]
) -> t.IndexArray:
    """Transform an integer array into an index array.

    Args:
        enum_class: The enum class to encode the integer array.
        value: The integer array to encode.

    Returns:
        The index array.

    Examples:
        >>> from array import array

        >>> import numpy

        >>> from openfisca_core import indexed_enums as enum

        >>> class Road(enum.Enum):
        ...     STREET = (
        ...         "A public road that connects two points, but also has "
        ...         "buildings on both sides of it; these typically run "
        ...         "perpendicular to avenues."
        ...     )
        ...     AVENUE = (
        ...         "A public way that also has buildings and/or trees on both "
        ...         "sides; these run perpendicular to streets and are "
        ...         "traditionally wider."
        ...     )

        >>> _int_to_index(Road, 1)
        array([1], dtype=uint8)

        >>> _int_to_index(Road, [1])
        array([1], dtype=uint8)

        >>> _int_to_index(Road, array("B", [1]))
        array([1], dtype=uint8)

        >>> _int_to_index(Road, memoryview(array("B", [1])))
        array([1], dtype=uint8)

        >>> _int_to_index(Road, numpy.array(1))
        array([1], dtype=uint8)

        >>> _int_to_index(Road, numpy.array([1]))
        array([1], dtype=uint8)

        >>> _int_to_index(Road, numpy.array([0, 1, 0]))
        array([0, 1, 0], dtype=uint8)

        >>> _int_to_index(Road, numpy.array([1, 1, 2]))
        array([1, 1], dtype=uint8)

    """
    indices = enum_class.indices
    values = numpy.asarray(value)
    return values[values < indices.size].astype(t.EnumDType)


def _str_to_index(
    enum_class: type[t.Enum], value: t.StrArray | t.ArrayLike[str]
) -> t.IndexArray:
    """Transform a string array into an index array.

    Args:
        enum_class: The enum class to encode the string array.
        value: The string array to encode.

    Returns:
        The index array.

    Examples:
        >>> import numpy

        >>> from openfisca_core import indexed_enums as enum

        >>> class Road(enum.Enum):
        ...     STREET = (
        ...         "A public road that connects two points, but also has "
        ...         "buildings on both sides of it; these typically run "
        ...         "perpendicular to avenues."
        ...     )
        ...     AVENUE = (
        ...         "A public way that also has buildings and/or trees on both "
        ...         "sides; these run perpendicular to streets and are "
        ...         "traditionally wider."
        ...     )

        >>> _str_to_index(Road, "AVENUE")
        array([1], dtype=uint8)

        >>> _str_to_index(Road, ["AVENUE"])
        array([1], dtype=uint8)

        >>> _str_to_index(Road, numpy.array("AVENUE"))
        array([1], dtype=uint8)

        >>> _str_to_index(Road, numpy.array(["AVENUE"]))
        array([1], dtype=uint8)

        >>> _str_to_index(Road, numpy.array(["STREET", "AVENUE", "STREET"]))
        array([0, 1, 0], dtype=uint8)

        >>> _str_to_index(Road, numpy.array(["AVENUE", "AVENUE", "BOULEVARD"]))
        array([1, 1], dtype=uint8)

    """
    values = numpy.asarray(value)
    names = enum_class.names
    mask = numpy.isin(values, names)
    sorter = numpy.argsort(names)
    result = sorter[numpy.searchsorted(names, values[mask], sorter=sorter)]
    return result.astype(t.EnumDType)


__all__ = ["_enum_to_index", "_int_to_index", "_str_to_index"]
