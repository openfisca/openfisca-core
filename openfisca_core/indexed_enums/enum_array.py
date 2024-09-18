from __future__ import annotations

from typing import NoReturn, overload
from typing_extensions import TypeGuard

import numpy

from . import types as t


class EnumArray(t.EnumArray):
    """
    NumPy array subclass representing an array of enum items.

    EnumArrays are encoded as ``int`` arrays to improve performance
    """

    # Subclassing ndarray is a little tricky.
    # To read more about the two following methods, see:
    # https://docs.scipy.org/doc/numpy-1.13.0/user/basics.subclassing.html#slightly-more-realistic-example-attribute-added-to-existing-array.

    #: Enum type of the array items.
    possible_values: None | type[t.Enum] = None

    def __new__(
        cls,
        input_array: t.Array[t.ArrayEnum],
        possible_values: None | type[t.Enum] = None,
    ) -> EnumArray:
        obj = numpy.asarray(input_array).view(cls)
        obj.possible_values = possible_values
        return obj

    # See previous comment
    def __array_finalize__(self, obj: None | t.EnumArray | t.Array[t.ArrayAny]) -> None:
        if obj is None:
            return None
        if isinstance(obj, EnumArray):
            self.possible_values = obj.possible_values
        return None

    @overload  # type: ignore[override]
    def __eq__(self, other: None | t.Enum | type[t.Enum]) -> t.Array[t.ArrayBool]:
        ...

    @overload
    def __eq__(self, other: object) -> t.Array[t.ArrayBool] | bool:
        ...

    def __eq__(self, other: object) -> t.Array[t.ArrayBool] | bool:
        boolean_array: t.Array[t.ArrayBool]
        boolean: bool

        if self.possible_values is None:
            return NotImplemented

        view: t.Array[t.ArrayEnum] = self.view(numpy.ndarray)

        if other is None or self._is_an_enum_type(other):
            boolean_array = view == other
            return boolean_array

        # When comparing to an item of self.possible_values, use the item index
        # to speed up the comparison.
        if self._is_an_enum(other):
            # Use view(ndarray) so that the result is a classic ndarray, not an
            # EnumArray.
            boolean_array = view == other.index
            return boolean_array

        boolean = view == other
        return boolean

    @overload  # type: ignore[override]
    def __ne__(self, other: None | t.Enum | type[t.Enum]) -> t.Array[t.ArrayBool]:
        ...

    @overload
    def __ne__(self, other: object) -> t.Array[t.ArrayBool] | bool:
        ...

    def __ne__(self, other: object) -> t.Array[t.ArrayBool] | bool:
        return numpy.logical_not(self == other)

    def _forbidden_operation(self, other: object) -> NoReturn:
        raise TypeError(
            "Forbidden operation. The only operations allowed on EnumArrays "
            "are '==' and '!='.",
        )

    __add__ = _forbidden_operation  # type: ignore[assignment]
    __mul__ = _forbidden_operation  # type: ignore[assignment]
    __lt__ = _forbidden_operation  # type: ignore[assignment]
    __le__ = _forbidden_operation  # type: ignore[assignment]
    __gt__ = _forbidden_operation  # type: ignore[assignment]
    __ge__ = _forbidden_operation  # type: ignore[assignment]
    __and__ = _forbidden_operation  # type: ignore[assignment]
    __or__ = _forbidden_operation  # type: ignore[assignment]

    def decode(self) -> t.Array[t.ArrayEnum]:
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

    def decode_to_str(self) -> t.Array[t.ArrayStr]:
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

    def _is_an_enum(self, other: object) -> TypeGuard[t.Enum]:
        return (
            not hasattr(other, "__name__")
            and other.__class__.__name__ is self.possible_values.__name__
        )

    def _is_an_enum_type(self, other: object) -> TypeGuard[type[t.Enum]]:
        return (
            hasattr(other, "__name__")
            and other.__name__ is self.possible_values.__name__
        )
