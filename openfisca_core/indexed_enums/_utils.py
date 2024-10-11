import numpy

from . import types as t
from ._errors import EnumMemberNotFoundError


def _enum_to_index(enum_class: type[t.Enum], value: t.ObjArray) -> t.IndexArray:
    """Transform an array of enum members into an index array.

    Args:
        enum_class: The enum class to encode the enum members array.
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

        >>> _enum_to_index(Road, numpy.array(Road.AVENUE))
        Traceback (most recent call last):
        TypeError: iteration over a 0-d array

        >>> _enum_to_index(Road, numpy.array([Road.AVENUE]))
        array([1], dtype=uint8)

        >>> value = numpy.array([Road.STREET, Road.AVENUE, Road.STREET])
        >>> _enum_to_index(Road, value)
        array([0, 1, 0], dtype=uint8)

        >>> value = numpy.array([Road.AVENUE, Road.AVENUE, Rogue.BOULEVARD])
        >>> _enum_to_index(Road, value)
        array([1, 1, 0], dtype=uint8)

    """
    index = [member.index for member in value]
    return _int_to_index(enum_class, numpy.array(index))


def _int_to_index(enum_class: type[t.Enum], value: t.IndexArray) -> t.IndexArray:
    """Transform an integer array into an index array.

    Args:
        enum_class: The enum class to encode the integer array.
        value: The integer array to encode.

    Returns:
        The index array.

    Raises:
        EnumMemberNotFoundError: If one value is not in the enum class.

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

        >>> _int_to_index(Road, numpy.array(1))
        array([1], dtype=uint8)

        >>> _int_to_index(Road, numpy.array([1]))
        array([1], dtype=uint8)

        >>> _int_to_index(Road, numpy.array([0, 1, 0]))
        array([0, 1, 0], dtype=uint8)

        >>> _int_to_index(Road, numpy.array([1, 1, 2]))
        Traceback (most recent call last):
        EnumMemberNotFoundError: Member with index 2 not found in enum 'Road...

    """
    # Create a mask to determine which values are in the enum class.
    mask = value < enum_class.items.size

    # Get the values that are not in the enum class.
    ko = value[~mask]

    # If there are values that are not in the enum class, raise an error.
    if ko.size > 0:
        raise EnumMemberNotFoundError(enum_class, f"with index {ko[0]}")

    # Finally, return the index array.
    return numpy.array(value[mask], dtype=t.EnumDType)


def _str_to_index(enum_class: type[t.Enum], value: t.StrArray) -> t.IndexArray:
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

        >>> _str_to_index(Road, numpy.array("AVENUE"))
        Traceback (most recent call last):
        TypeError: iteration over a 0-d array

        >>> _str_to_index(Road, numpy.array(["AVENUE"]))
        array([1], dtype=uint8)

        >>> _str_to_index(Road, numpy.array(["STREET", "AVENUE", "STREET"]))
        array([0, 1, 0], dtype=uint8)

        >>> _str_to_index(Road, numpy.array(["AVENUE", "AVENUE", "BOULEVARD"]))
        array([1, 1, 0], dtype=uint8)

    """
    names = enum_class.names
    index = [enum_class[name].index if name in names else 0 for name in value]
    return _int_to_index(enum_class, numpy.array(index))


__all__ = ["_enum_to_index", "_int_to_index", "_str_to_index"]
