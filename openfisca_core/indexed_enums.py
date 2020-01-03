from __future__ import annotations

from enum import Enum as BaseEnum
from typing import Any, NoReturn, Optional, Type, Union

from numpy import (
    asarray,
    int16,
    logical_not as not_,
    ndarray,
    select,
    )

ENUM_ARRAY_DTYPE = int16


class Enum(BaseEnum):
    """
    Enum based on `enum34 <https://pypi.python.org/pypi/enum34/>`_, whose items have an
    index.
    """

    # Tweak enums to add an index attribute to each enum item
    def __init__(self, name: str) -> None:
        # When the enum item is initialized, self._member_names_ contains the names of
        # the previously initialized items, so its length is the index of this item.
        self.index = len(self._member_names_)

    # Bypass the slow Enum.__eq__
    __eq__ = object.__eq__

    # In Python 3, __hash__ must be defined if __eq__ is defined to stay hashable.
    __hash__ = object.__hash__

    @classmethod
    def encode(
            cls,
            array: Union[
                "EnumArray",
                ndarray[str],
                ndarray["Enum"],
                ndarray[int],
                ],
            ) -> "EnumArray":
        """
        Encode a string numpy array, an enum item numpy array, or an int numpy array
        into an :any:`EnumArray`. See :any:`EnumArray.decode` for decoding.

        :param ndarray array: Array of string identifiers, or of enum items, to encode.

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
        if type(array) is EnumArray:
            return array

        if array.dtype.kind in {'U', 'S'}:  # String array
            array = select(
                [array == item.name for item in cls],
                [item.index for item in cls],
                ).astype(ENUM_ARRAY_DTYPE)

        elif array.dtype.kind == 'O':  # Enum items arrays
            # Ensure we are comparing the comparable. The problem this fixes:
            # On entering this method "cls" will generally come from
            # variable.possible_values, while the array values may come from directly
            # importing a module containing an Enum class. However, variables (and
            # hence their possible_values) are loaded by a call to load_module, which
            # gives them a different identity from the ones imported in the usual way.
            # So, instead of relying on the "cls" passed in, we use only its name to
            # check that the values in the array, if non-empty, are of the right type.
            if len(array) > 0 and cls.__name__ is array[0].__class__.__name__:
                cls = array[0].__class__

            array = select(
                [array == item for item in cls],
                [item.index for item in cls],
                ).astype(ENUM_ARRAY_DTYPE)

        return EnumArray(array, cls)


class EnumArray(ndarray):
    """Numpy array subclass representing an array of enum items.

    EnumArrays are encoded as ``int`` arrays to improve performance
    """

    # Subclassing ndarray is a little tricky.
    # To read more about the two following methods, see:
    # https://docs.scipy.org/doc/numpy-1.13.0/user/basics.subclassing.html#slightly-more-realistic-example-attribute-added-to-existing-array.
    def __new__(
            cls,
            input_array: ndarray[int],
            possible_values: Optional[Type["Enum"]] = None,
            ) -> "EnumArray":
        obj = asarray(input_array).view(cls)
        obj.possible_values = possible_values
        return obj

    # See previous comment
    def __array_finalize__(self, obj: Optional[ndarray[int]]) -> None:
        if obj is None:
            return

        self.possible_values = getattr(obj, "possible_values", None)

    def __eq__(self, other: Any) -> bool:
        # When comparing to an item of self.possible_values, use the item index to
        # speed up the comparison.
        if other.__class__.__name__ is self.possible_values.__name__:
            # Use view(ndarray) so that the result is a classic ndarray, not an
            # EnumArray.
            return self.view(ndarray) == other.index

        return self.view(ndarray) == other

    def __ne__(self, other: Any) -> bool:
        return not_(self == other)

    def _forbidden_operation(self, other: Any) -> NoReturn:
        raise TypeError(
            "Forbidden operation. The only operations allowed on EnumArrays are "
            "'==' and '!='.",
            )

    __add__ = _forbidden_operation
    __mul__ = _forbidden_operation
    __lt__ = _forbidden_operation
    __le__ = _forbidden_operation
    __gt__ = _forbidden_operation
    __ge__ = _forbidden_operation
    __and__ = _forbidden_operation
    __or__ = _forbidden_operation

    def decode(self) -> ndarray["Enum"]:
        """Return the array of enum items corresponding to self.

        For instance:

        >>> enum_array = household('housing_occupancy_status', period)
        >>> enum_array[0]
        >>> 2  # Encoded value
        >>> enum_array.decode()[0]
        <HousingOccupancyStatus.free_lodger: 'Free lodger'>  # Decoded value : enum item
        """
        return select(
            [self == item.index for item in self.possible_values],
            list(self.possible_values),
            )

    def decode_to_str(self) -> ndarray[str]:
        """Return the array of string identifiers corresponding to self.

        For instance:

        >>> enum_array = household('housing_occupancy_status', period)
        >>> enum_array[0]
        >>> 2  # Encoded value
        >>> enum_array.decode_to_str()[0]
        'free_lodger'  # String identifier
        """
        return select(
            [self == item.index for item in self.possible_values],
            [item.name for item in self.possible_values],
            )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self.decode())})"

    def __str__(self) -> str:
        return str(self.decode_to_str())
