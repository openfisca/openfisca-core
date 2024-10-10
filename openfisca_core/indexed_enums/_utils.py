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

        >>> class Rogue(enum.Enum):
        ...     BOULEVARD = "More like a shady impasse, to be honest."

        # >>> _enum_to_index(Road, numpy.array(Road.AVENUE))
        # array([1], dtype=uint8)
        #
        # >>> _enum_to_index(Road, numpy.array([Road.AVENUE]))
        # array([1], dtype=uint8)
        #
        # >>> value = numpy.array([Road.STREET, Road.AVENUE, Road.STREET])
        # >>> _enum_to_index(Road, value)
        # array([0, 1, 0], dtype=uint8)

        >>> value = numpy.array([Road.AVENUE, Road.AVENUE, Rogue.BOULEVARD])
        >>> _enum_to_index(Road, value)
        Traceback (most recent call last):
        EnumMemberNotFoundError: Member BOULEVARD not found in enum 'Road'...

    """
    # Create a mask to determine which values are in the enum class.
    mask = numpy.isin(value, enum_class.enums)

    # Get the values that are not in the enum class.
    ko = value[~mask]

    # If there are values that are not in the enum class, raise an error.
    if ko.size > 0:
        raise EnumMemberNotFoundError(enum_class, ko[0].name)

    # In case we're dealing with a scalar, we need to convert it to an array.
    ok = value[mask]

    # Get the indices that would sort the enums.
    sorted_index = numpy.argsort(enum_class.enums)

    # Get the enums as if they were sorted.
    sorted_enums = enum_class.enums[sorted_index]

    # Get the index positions of the enums in the sorted enums.
    index_where = numpy.searchsorted(sorted_enums, ok)

    # Get the actual index of the enums in the enum class.
    index = sorted_index[index_where]

    # Finally, return the index array.
    return numpy.array(index, dtype=t.EnumDType)


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
    mask = numpy.isin(value, enum_class.indices)

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

        >>> _str_to_index(Road, numpy.array("AVENUE"))
        array([1], dtype=uint8)

        >>> _str_to_index(Road, numpy.array(["AVENUE"]))
        array([1], dtype=uint8)

        >>> _str_to_index(Road, numpy.array(["STREET", "AVENUE", "STREET"]))
        array([0, 1, 0], dtype=uint8)

        >>> _str_to_index(Road, numpy.array(["AVENUE", "AVENUE", "BOULEVARD"]))
        Traceback (most recent call last):
        EnumMemberNotFoundError: Member BOULEVARD not found in enum 'Road'...

    """
    # Create a mask to determine which values are in the enum class.
    mask = numpy.isin(value, enum_class.names)

    # Get the values that are not in the enum class.
    ko = value[~mask]

    # If there are values that are not in the enum class, raise an error.
    if ko.size > 0:
        raise EnumMemberNotFoundError(enum_class, ko[0])

    # In case we're dealing with a scalar, we need to convert it to an array.
    ok = value[mask]

    # Get the indices that would sort the names.
    sorted_index = numpy.argsort(enum_class.names)

    # Get the names as if they were sorted.
    sorted_names = enum_class.names[sorted_index]

    # Get the index positions of the names in the sorted names.
    index_where = numpy.searchsorted(sorted_names, ok)

    # Get the actual index of the names in the enum class.
    index = sorted_index[index_where]

    # Finally, return the index array.
    return numpy.array(index, dtype=t.EnumDType)


__all__ = ["_enum_to_index", "_int_to_index", "_str_to_index"]
