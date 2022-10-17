from __future__ import annotations

import enum
from typing import Union

import numpy

from .config import ENUM_ARRAY_DTYPE
from .enum_array import EnumArray


class Enum(enum.Enum):
    """
    Enum based on `enum34 <https://pypi.python.org/pypi/enum34/>`_, whose items
    have an index.
    """

    # Tweak enums to add an index attribute to each enum item
    def __init__(self, name: str) -> None:
        # When the enum item is initialized, self._member_names_ contains the
        # names of the previously initialized items, so its length is the index
        # of this item.
        self.index = len(self._member_names_)

    # Bypass the slow Enum.__eq__
    __eq__ = object.__eq__

    # In Python 3, __hash__ must be defined if __eq__ is defined to stay
    # hashable.
    __hash__ = object.__hash__

    @classmethod
    def encode(
        cls,
        array: Union[
            EnumArray,
            numpy.int_,
            numpy.float_,
            numpy.object_,
        ],
    ) -> EnumArray:
        """
        Encode a string numpy array, an enum item numpy array, or an int numpy
        array into an :any:`EnumArray`. See :any:`EnumArray.decode` for
        decoding.

        :param numpy.ndarray array: Array of string identifiers, or of enum
                                    items, to encode.

        :returns: An :any:`EnumArray` encoding the input array values.
        :rtype: :any:`EnumArray`

        For instance:

        >>> string_identifier_array = asarray(['free_lodger', 'owner'])
        >>> encoded_array = HousingOccupancyStatus.encode(string_identifier_array)
        >>> encoded_array[0]
        2  # Encoded value

        >>> free_lodger = HousingOccupancyStatus.free_lodger
        >>> owner = HousingOccupancyStatus.owner
        >>> enum_item_array = asarray([free_lodger, owner])
        >>> encoded_array = HousingOccupancyStatus.encode(enum_item_array)
        >>> encoded_array[0]
        2  # Encoded value
        """
        if isinstance(array, EnumArray):
            return array

        # String array
        if isinstance(array, numpy.ndarray) and array.dtype.kind in {"U", "S"}:
            array = numpy.select(
                [array == item.name for item in cls],
                [item.index for item in cls],
            ).astype(ENUM_ARRAY_DTYPE)

        # Enum items arrays
        elif isinstance(array, numpy.ndarray) and array.dtype.kind == "O":
            # Ensure we are comparing the comparable. The problem this fixes:
            # On entering this method "cls" will generally come from
            # variable.possible_values, while the array values may come from
            # directly importing a module containing an Enum class. However,
            # variables (and hence their possible_values) are loaded by a call
            # to load_module, which gives them a different identity from the
            # ones imported in the usual way.
            #
            # So, instead of relying on the "cls" passed in, we use only its
            # name to check that the values in the array, if non-empty, are of
            # the right type.
            if len(array) > 0 and cls.__name__ is array[0].__class__.__name__:
                cls = array[0].__class__

            array = numpy.select(
                [array == item for item in cls],
                [item.index for item in cls],
            ).astype(ENUM_ARRAY_DTYPE)

        return EnumArray(array, cls)
