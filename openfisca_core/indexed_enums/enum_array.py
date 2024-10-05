from __future__ import annotations

from typing import NoReturn
from typing_extensions import Self

import numpy
from . import types as t


class EnumArray(t.EnumArray):
    """A subclass of :class:`~numpy.ndarray` of :class:`.Enum`.

    :class:`.Enum` arrays are encoded as :class:`int` to improve performance.

    Examples:
        >>> from openfisca_core.indexed_enums import Enum
        >>> from openfisca_core.variables import Variable

        >>> class Housing(Enum):
        ...     OWNER = "Owner"
        ...     TENANT = "Tenant"
        ...     FREE_LODGER = "Free lodger"
        ...     HOMELESS = "Homeless"

        >>> array = numpy.array([1])
        >>> enum_array = EnumArray(array, Housing)

        >>> repr(EnumArray)
        "<class 'openfisca_core.indexed_enums.enum_array.EnumArray'>"

        >>> repr(enum_array)
        '<EnumArray([<Housing.TENANT(Tenant)>])>'

        >>> str(enum_array)
        "['TENANT']"

        >>> list(enum_array)
        [1]

        >>> enum_array[0]
        1

        >>> enum_array[0] in enum_array
        True

        >>> len(enum_array)
        1

        >>> enum_array = EnumArray(list(Housing), Housing)
        >>> enum_array[Housing.TENANT.index]
        <Housing.TENANT(Tenant)>

        >>> class OccupancyStatus(Variable):
        ...     value_type = Enum
        ...     possible_values = Housing

        >>> EnumArray(array, OccupancyStatus.possible_values)
        <EnumArray([<Housing.TENANT(Tenant)>])>

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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.decode()!s})"

    def __str__(self) -> str:
        return str(self.decode_to_str())

    def __eq__(self, other: object) -> bool | t.Array[t.DTypeBool]:
        """Compare equality with the item's :attr:`~.Enum.index`.

        When comparing to an item of :attr:`.possible_values`, use the
        item's :attr:`~.Enum.index`. to speed up the comparison.

        Whenever possible, use :any:`numpy.ndarray.view` so that the result is
        a classic :class:`~numpy.ndarray`, not an :obj:`.EnumArray`.

        Args:
            other: Another :class:`object` to compare to.

        Returns:
            bool: When ???
            ndarray[bool_]: When ???

        Examples:
            >>> from openfisca_core.indexed_enums import Enum

            >>> class MyEnum(Enum):
            ...     FOO = b"foo"
            ...     BAR = b"bar"

            >>> array = numpy.array([1])
            >>> enum_array = EnumArray(array, MyEnum)

            >>> enum_array == 1
            array([ True])

            >>> enum_array == [1]
            array([ True])

            >>> enum_array == [2]
            array([False])

            >>> enum_array == "1"
            False

            >>> enum_array is None
            array([False])

        Note:
            This breaks the `Liskov substitution principle`_.

        .. _Liskov substitution principle:
            https://en.wikipedia.org/wiki/Liskov_substitution_principle

        """
        if other.__class__.__name__ is self.possible_values.__name__:
            return self.view(numpy.ndarray) == other.index
        return self.view(numpy.ndarray) == other

    def __ne__(self, other: object) -> bool | t.Array[t.DTypeBool]:
        """Inequality.

        Args:
            other: Another :class:`object` to compare to.

        Returns:
            bool: When ???
            ndarray[bool_]: When ???

        Examples:
            >>> from openfisca_core.indexed_enums import Enum

            >>> class MyEnum(Enum):
            ...     FOO = b"foo"
            ...     BAR = b"bar"

            >>> array = numpy.array([1])
            >>> enum_array = EnumArray(array, MyEnum)

            >>> enum_array != 1
            array([False])

            >>> enum_array != [1]
            array([False])

            >>> enum_array != [2]
            array([ True])

            >>> enum_array != "1"
            True

            >>> enum_array is not None
            array([ True])

        Note:
            This breaks the `Liskov substitution principle`_.

        .. _Liskov substitution principle:
            https://en.wikipedia.org/wiki/Liskov_substitution_principle

        """
        return numpy.logical_not(self == other)

    @staticmethod
    def _forbidden_operation(other: object) -> NoReturn:
        msg = (
            "Forbidden operation. The only operations allowed on EnumArrays "
            "are '==' and '!='."
        )
        raise TypeError(msg)

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
            ndarray[Enum]: The items of the :obj:`.EnumArray`.

        Examples:
            >>> from openfisca_core.indexed_enums import Enum

            >>> class MyEnum(Enum):
            ...     FOO = b"foo"
            ...     BAR = b"bar"

            >>> array = numpy.array([1])
            >>> enum_array = EnumArray(array, MyEnum)
            >>> enum_array.decode()
            array([<MyEnum.BAR(b'bar')>], dtype=object)

        """
        return numpy.select(
            [self == item.index for item in self.possible_values],
            list(self.possible_values),
        )

    def decode_to_str(self) -> numpy.str_:
        """Decode itself to an array of strings.

        Returns:
            ndarray[str_]: The string values of the :obj:`.EnumArray`.

        Examples:
            >>> from openfisca_core.indexed_enums import Enum

            >>> class MyEnum(Enum):
            ...     FOO = b"foo"
            ...     BAR = b"bar"

            >>> array = numpy.array([1])
            >>> enum_array = EnumArray(array, MyEnum)
            >>> enum_array.decode_to_str()
            array(['BAR']...)

        """
        return numpy.select(
            [self == item.index for item in self.possible_values],
            [item.name for item in self.possible_values],
        )


__all__ = ["EnumArray"]
