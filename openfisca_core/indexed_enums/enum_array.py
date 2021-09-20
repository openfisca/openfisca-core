from __future__ import annotations

from typing import Any, NoReturn, Optional, Type, Union

import numpy

from openfisca_core.types import ArrayLike, ArrayType, Encodable


class EnumArray(numpy.ndarray):
    """:class:`numpy.ndarray` subclass representing an array of :class:`.Enum`.

    :class:`EnumArrays <.EnumArray>` are encoded as :class:`int` arrays to
    improve performance.

    Note:
        Subclassing `numpy.ndarray` is a little tricky™. To read more about the
        :meth:`.__new__` and :meth:`.__array_finalize__` methods below, see
        `Subclassing ndarray`_.

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


    .. _Subclassing ndarray:
        https://numpy.org/doc/stable/user/basics.subclassing.html

    """

    def __new__(
            cls,
            input_array: ArrayType[int],
            possible_values: Optional[Type[Encodable]] = None,
            ) -> EnumArray:
        """See comment above."""

        obj: EnumArray
        obj = numpy.asarray(input_array).view(cls)
        obj.possible_values = possible_values
        return obj

    def __array_finalize__(self, obj: Optional[ArrayType[int]]) -> None:
        """See comment above."""

        if obj is None:
            return

        self.possible_values = getattr(obj, "possible_values", None)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({str(self.decode())})>"

    def __str__(self) -> str:
        return str(self.decode_to_str())

    def __eq__(self, other: Any) -> Union[ArrayType[bool], bool]:
        """Compare equality with the item index.

        When comparing to an item of :attr:`.possible_values`, use the item
        index to speed up the comparison.

        Whenever possible, use :meth:`numpy.ndarray.view` so that the result is
        a classic :obj:`numpy.ndarray`, not an :obj:`.EnumArray`.

        Args:
            other: Another object to compare to.

        Returns:
            True, False, or a boolean :class:`numpy.ndarray`.

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

            >>> enum_array == None
            array([False])

        """

        if other.__class__.__name__ is self.possible_values.__name__:
            return self.view(numpy.ndarray) == other.index

        return self.view(numpy.ndarray) == other

    def __ne__(self, other: Any) -> Union[ArrayType[bool], bool]:
        """Inequality…

        Args:
            other: Another object to compare to.

        Returns:
            True, False, or a boolean :class:`numpy.ndarray`.

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

            >>> enum_array != None
            array([ True])

        """

        return numpy.logical_not(self == other)

    def _forbidden_operation(self, other: Any) -> NoReturn:
        raise TypeError(
            "Forbidden operation. The only operations allowed on "
            f"{self.__class__.__name__}s are '==' and '!='.",
            )

    __add__ = _forbidden_operation
    __mul__ = _forbidden_operation
    __lt__ = _forbidden_operation
    __le__ = _forbidden_operation
    __gt__ = _forbidden_operation
    __ge__ = _forbidden_operation
    __and__ = _forbidden_operation
    __or__ = _forbidden_operation

    def decode(self) -> ArrayLike[Encodable]:
        """Decodes itself to a normal array.

        Returns:
            The enum items of the :obj:`.EnumArray`.

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

    def decode_to_str(self) -> ArrayType[str]:
        """Decodes itself to an array of strings.

        Returns:
            The string identifiers of the :obj:`.EnumArray`.

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
