from __future__ import annotations

import typing
from typing import Any, NoReturn, Optional, Type

import numpy

if typing.TYPE_CHECKING:
    from policyengine_core.enums import Enum


class EnumArray(numpy.ndarray):
    """
    Numpy array subclass representing an array of enum items.

    EnumArrays are encoded as ``int`` arrays to improve performance
    """

    # Subclassing ndarray is a little tricky.
    # To read more about the two following methods, see:
    # https://docs.scipy.org/doc/numpy-1.13.0/user/basics.subclassing.html#slightly-more-realistic-example-attribute-added-to-existing-array.
    def __new__(
        cls,
        input_array: numpy.int_,
        possible_values: Optional[Type[Enum]] = None,
    ) -> EnumArray:
        obj = numpy.asarray(input_array).view(cls)
        obj.possible_values = possible_values
        return obj

    # See previous comment
    def __array_finalize__(self, obj: Optional[numpy.int_]) -> None:
        if obj is None:
            return

        self.possible_values = getattr(obj, "possible_values", None)

    def __eq__(self, other: Any) -> bool:
        # When comparing to an item of self.possible_values, use the item index
        # to speed up the comparison.
        if other.__class__.__name__ is self.possible_values.__name__:
            # Use view(ndarray) so that the result is a classic ndarray, not an
            # EnumArray.
            return self.view(numpy.ndarray) == other.index

        return self.view(numpy.ndarray) == other

    def __ne__(self, other: Any) -> bool:
        return numpy.logical_not(self == other)

    def _forbidden_operation(self, other: Any) -> NoReturn:
        raise TypeError(
            "Forbidden operation. The only operations allowed on EnumArrays "
            "are '==' and '!='.",
        )

    __add__ = _forbidden_operation
    __mul__ = _forbidden_operation
    __lt__ = _forbidden_operation
    __le__ = _forbidden_operation
    __gt__ = _forbidden_operation
    __ge__ = _forbidden_operation
    __and__ = _forbidden_operation
    __or__ = _forbidden_operation

    def decode(self) -> numpy.object_:
        """
        Return the array of enum items corresponding to self.

        For instance:

        >>> enum_array = household('housing_occupancy_status', period)
        >>> enum_array[0]
        >>> 2  # Encoded value
        >>> enum_array.decode()[0]
        <HousingOccupancyStatus.free_lodger: 'Free lodger'>

        Decoded value: enum item
        """
        return numpy.select(
            [self == item.index for item in self.possible_values],
            list(self.possible_values),
        )

    def decode_to_str(self) -> numpy.str_:
        """
        Return the array of string identifiers corresponding to self.

        For instance:

        >>> enum_array = household('housing_occupancy_status', period)
        >>> enum_array[0]
        >>> 2  # Encoded value
        >>> enum_array.decode_to_str()[0]
        'free_lodger'  # String identifier
        """
        return numpy.select(
            [self == item.index for item in self.possible_values],
            [item.name for item in self.possible_values],
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self.decode())})"

    def __str__(self) -> str:
        return str(self.decode_to_str())
