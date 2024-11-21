from __future__ import annotations

from typing import NoReturn
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

    Examples:
        >>> import numpy

        >>> from openfisca_core import indexed_enums as enum, variables

        >>> class Housing(enum.Enum):
        ...     OWNER = "Owner"
        ...     TENANT = "Tenant"
        ...     FREE_LODGER = "Free lodger"
        ...     HOMELESS = "Homeless"

        >>> array = numpy.array([1], dtype=numpy.int16)
        >>> enum_array = enum.EnumArray(array, Housing)

        >>> repr(enum.EnumArray)
        "<class 'openfisca_core.indexed_enums.enum_array.EnumArray'>"

        >>> repr(enum_array)
        'EnumArray([Housing.TENANT])'

        >>> str(enum_array)
        "['TENANT']"

        >>> list(map(int, enum_array))
        [1]

        >>> int(enum_array[0])
        1

        >>> enum_array[0] in enum_array
        True

        >>> len(enum_array)
        1

        >>> enum_array = enum.EnumArray(list(Housing), Housing)
        Traceback (most recent call last):
        AttributeError: 'list' object has no attribute 'view'

        >>> class OccupancyStatus(variables.Variable):
        ...     value_type = enum.Enum
        ...     possible_values = Housing

        >>> enum.EnumArray(array, OccupancyStatus.possible_values)
        EnumArray([Housing.TENANT])

    .. _Subclassing ndarray:
        https://numpy.org/doc/stable/user/basics.subclassing.html

    """

    #: Enum type of the array items.
    possible_values: None | type[t.Enum]

    def __new__(
        cls,
        input_array: t.IndexArray,
        possible_values: type[t.Enum],
    ) -> Self:
        """See comment above."""
        obj = input_array.view(cls)
        obj.possible_values = possible_values
        return obj

    def __array_finalize__(self, obj: None | t.EnumArray | t.VarArray) -> None:
        """See comment above."""
        if obj is None:
            return
        self.possible_values = getattr(obj, "possible_values", None)

    def __eq__(self, other: object) -> t.BoolArray:  # type: ignore[override]
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
            >>> import numpy

            >>> from openfisca_core import indexed_enums as enum

            >>> class Housing(enum.Enum):
            ...     OWNER = "Owner"
            ...     TENANT = "Tenant"

            >>> array = numpy.array([1])
            >>> enum_array = enum.EnumArray(array, Housing)

            >>> enum_array == Housing
            array([False,  True])

            >>> enum_array == Housing.TENANT
            array([ True])

            >>> enum_array == 1
            array([ True])

            >>> enum_array == [1]
            array([ True])

            >>> enum_array == [2]
            array([False])

            >>> enum_array == "1"
            array([False])

            >>> enum_array is None
            False

            >>> enum_array == enum.EnumArray(numpy.array([1]), Housing)
            array([ True])

        Note:
            This breaks the `Liskov substitution principle`_.

        .. _Liskov substitution principle:
            https://en.wikipedia.org/wiki/Liskov_substitution_principle

        """
        result: t.BoolArray

        if self.possible_values is None:
            return NotImplemented
        if other is None:
            return NotImplemented
        if isinstance(other, type(t.Enum)) and other == self.possible_values:
            result = (
                self.view(numpy.ndarray)
                == self.possible_values.indices[
                    self.possible_values.indices <= max(self)
                ]
            )
            return result
        if isinstance(other, t.Enum) and other.__class__ == self.possible_values:
            result = self.view(numpy.ndarray) == other.index
            return result
        # For NumPy >=1.26.x.
        if isinstance(is_equal := self.view(numpy.ndarray) == other, numpy.ndarray):
            return is_equal
        # For NumPy <1.26.x.
        return numpy.array([is_equal], dtype=t.BoolDType)

    def __ne__(self, other: object) -> t.BoolArray:  # type: ignore[override]
        """Inequality.

        Args:
            other: Another :class:`object` to compare to.

        Returns:
            bool: When ???
            ndarray[bool_]: When ???

        Examples:
            >>> import numpy

            >>> from openfisca_core import indexed_enums as enum

            >>> class Housing(enum.Enum):
            ...     OWNER = "Owner"
            ...     TENANT = "Tenant"

            >>> array = numpy.array([1])
            >>> enum_array = enum.EnumArray(array, Housing)

            >>> enum_array != Housing
            array([ True, False])

            >>> enum_array != Housing.TENANT
            array([False])

            >>> enum_array != 1
            array([False])

            >>> enum_array != [1]
            array([False])

            >>> enum_array != [2]
            array([ True])

            >>> enum_array != "1"
            array([ True])

            >>> enum_array is not None
            True

        Note:
            This breaks the `Liskov substitution principle`_.

        .. _Liskov substitution principle:
            https://en.wikipedia.org/wiki/Liskov_substitution_principle

        """
        return numpy.logical_not(self == other)

    @staticmethod
    def _forbidden_operation(*__args: object, **__kwds: object) -> NoReturn:
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

    def decode(self) -> t.ObjArray:
        """Decode itself to a normal array.

        Returns:
            ndarray[Enum]: The items of the :obj:`.EnumArray`.

        Raises:
            TypeError: When the :attr:`.possible_values` is not defined.

        Examples:
            >>> import numpy

            >>> from openfisca_core import indexed_enums as enum

            >>> class Housing(enum.Enum):
            ...     OWNER = "Owner"
            ...     TENANT = "Tenant"

            >>> array = numpy.array([1])
            >>> enum_array = enum.EnumArray(array, Housing)
            >>> enum_array.decode()
            array([Housing.TENANT], dtype=object)

        """
        result: t.ObjArray
        if self.possible_values is None:
            msg = (
                f"The possible values of the {self.__class__.__name__} are "
                f"not defined."
            )
            raise TypeError(msg)
        array = self.reshape(1).astype(t.EnumDType) if self.ndim == 0 else self
        result = self.possible_values.enums[array]
        return result

    def decode_to_str(self) -> t.StrArray:
        """Decode itself to an array of strings.

        Returns:
            ndarray[str_]: The string values of the :obj:`.EnumArray`.

        Raises:
            TypeError: When the :attr:`.possible_values` is not defined.

        Examples:
            >>> import numpy

            >>> from openfisca_core import indexed_enums as enum

            >>> class Housing(enum.Enum):
            ...     OWNER = "Owner"
            ...     TENANT = "Tenant"

            >>> array = numpy.array([1])
            >>> enum_array = enum.EnumArray(array, Housing)
            >>> enum_array.decode_to_str()
            array(['TENANT'], dtype='<U6')

        """
        result: t.StrArray
        if self.possible_values is None:
            msg = (
                f"The possible values of the {self.__class__.__name__} are "
                f"not defined."
            )
            raise TypeError(msg)
        array = self.reshape(1).astype(t.EnumDType) if self.ndim == 0 else self
        result = self.possible_values.names[array]
        return result

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.decode()!s})"

    def __str__(self) -> str:
        return str(self.decode_to_str())


__all__ = ["EnumArray"]
