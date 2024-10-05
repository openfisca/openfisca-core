from __future__ import annotations

from typing import Any, NoReturn
from typing_extensions import Self

import numpy

from . import types as t


class EnumArray(t.EnumArray):
    """A subclass of :class:`~numpy.ndarray` of :class:`.Enum`.

    :class:`.Enum` arrays are encoded as :class:`int` to improve performance.

    Note:
        Subclassing :class:`~numpy.ndarray` is a little tricky™. To read more
        about the :meth:`.__new__` and :meth:`.__array_finalize__` methods
        below, see `Subclassing ndarray`_.

    .. _Subclassing ndarray:
        https://numpy.org/doc/stable/user/basics.subclassing.html

    """

    #: Enum type of the array items.
    possible_values: None | type[t.Enum] = None

    def __new__(
        cls,
        input_array: t.Array[t.DTypeEnum],
        possible_values: None | type[t.Enum] = None,
    ) -> Self:
        """See comment above."""
        obj = numpy.asarray(input_array).view(cls)
        obj.possible_values = possible_values
        return obj

    def __array_finalize__(self, obj: numpy.int32 | None) -> None:
        """See comment above."""
        if obj is None:
            return

        self.possible_values = getattr(obj, "possible_values", None)

    def __eq__(self, other: object) -> bool:
        """Compare equality with the item's :attr:`~.Enum.index`.

        When comparing to an item of :attr:`.possible_values`, use the
        item's :attr:`~.Enum.index`. to speed up the comparison.

        Whenever possible, use :any:`numpy.ndarray.view` so that the result is
        a classic :class:`~numpy.ndarray`, not an :obj:`.EnumArray`.

        Args:
            other: Another :class:`object` to compare to.

        Returns:
            bool: When ???
            numpy.ndarray[numpy.bool_]: When ???

        Note:
            This breaks the `Liskov substitution principle`_.

        .. _Liskov substitution principle:
            https://en.wikipedia.org/wiki/Liskov_substitution_principle

        """

        if other.__class__.__name__ is self.possible_values.__name__:
            return self.view(numpy.ndarray) == other.index

        return self.view(numpy.ndarray) == other

    def __ne__(self, other: object) -> bool:
        """Inequality…

        Args:
            other: Another :class:`object` to compare to.

        Returns:
            bool: When ???
            numpy.ndarray[numpy.bool_]: When ???

        Note:
            This breaks the `Liskov substitution principle`_.

        .. _Liskov substitution principle:
            https://en.wikipedia.org/wiki/Liskov_substitution_principle

        """

        return numpy.logical_not(self == other)

    def _forbidden_operation(self, other: Any) -> NoReturn:
        msg = (
            "Forbidden operation. The only operations allowed on EnumArrays "
            "are '==' and '!='."
        )
        raise TypeError(
            msg,
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
        """Decode itself to a normal array.

        Returns:
            numpy.ndarray[t.Enum]: The items of the :obj:`.EnumArray`.

        For instance:

        >>> enum_array = household("housing_occupancy_status", period)
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
        """Decode itself to an array of strings.

        Returns:
            numpy.ndarray[numpy.str_]: The string values of the :obj:`.EnumArray`.

        For instance:

        >>> enum_array = household("housing_occupancy_status", period)
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
        return f"{self.__class__.__name__}({self.decode()!s})"

    def __str__(self) -> str:
        return str(self.decode_to_str())
