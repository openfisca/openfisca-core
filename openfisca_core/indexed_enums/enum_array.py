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
        'EnumArray(Housing.TENANT)'

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
        TypeError: int() argument must be a string, a bytes-like object or a...

        >>> class OccupancyStatus(variables.Variable):
        ...     value_type = enum.Enum
        ...     possible_values = Housing

        >>> enum.EnumArray(array, OccupancyStatus.possible_values)
        EnumArray(Housing.TENANT)

    .. _Subclassing ndarray:
        https://numpy.org/doc/stable/user/basics.subclassing.html

    """

    #: Enum type of the array items.
    possible_values: None | type[t.Enum] = None

    def __new__(
        cls,
        input_array: object,
        possible_values: None | type[t.Enum] = None,
    ) -> Self:
        """See comment above."""
        if not isinstance(input_array, numpy.ndarray):
            return cls.__new__(cls, numpy.asarray(input_array), possible_values)
        if input_array.ndim == 0:
            return cls.__new__(cls, input_array.reshape(1), possible_values)
        obj = input_array.astype(t.EnumDType).view(cls)
        obj.possible_values = possible_values
        return obj

    def __array_finalize__(self, obj: None | t.EnumArray | t.ObjArray) -> None:
        """See comment above."""
        if obj is None:
            return
        if isinstance(obj, EnumArray):
            self.possible_values = obj.possible_values
        return

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
        if (
            isinstance(other, type(t.Enum))
            and other.__name__ is self.possible_values.__name__
        ):
            result = (
                self.view(numpy.ndarray) == other.indices[other.indices <= max(self)]
            )
            return result
        if (
            isinstance(other, t.Enum)
            and other.__class__.__name__ is self.possible_values.__name__
        ):
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
        arr = self.astype(t.EnumDType)
        arr = arr.reshape(1) if arr.ndim == 0 else arr
        result = self.possible_values.items[arr.astype(t.EnumDType)].enum
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
        arr = self.astype(t.EnumDType)
        arr = arr.reshape(1) if arr.ndim == 0 else arr
        result = self.possible_values.items[arr.astype(t.EnumDType)].name
        return result

    def __repr__(self) -> str:
        items = ", ".join(str(item) for item in self.decode())
        return f"{self.__class__.__name__}({items})"

    def __str__(self) -> str:
        return str(self.decode_to_str())


__all__ = ["EnumArray"]
